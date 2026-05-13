import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VENDOR_TYC = REPO_ROOT / "vendor" / "tyc"


BASE_RULES = textwrap.dedent(
    """
    % Facts
    {facts}

    #defined variable/1.
    #defined declared_in/2.
    #defined function_scope/2.
    #defined type_of/2.

    % Optional (enhanced PPL depth): lexical scopes, shadowing, and free variables.
    #defined scope/1.
    #defined scope_parent/2.
    #defined declared_in_scope/2.
    #defined use_in/2.

    % Rules
    global_variable(X) :- variable(X), not local_variable(X, _).
    local_variable(X, F) :- declared_in(X, F).

    in_scope(X, S) :- local_variable(X, F), function_scope(F, S).
    in_scope(X, global) :- global_variable(X).

    bound_variable(X, S) :- in_scope(X, S), type_of(X, int).

    % Diagnostics for edge cases
    orphan_declaration(X, F) :- declared_in(X, F), not variable(X).
    missing_scope(F) :- declared_in(_, F), not function_scope(F, _).
    untyped_variable(X) :- variable(X), not type_of(X, _).
    non_int_type(X, T) :- type_of(X, T), T != int.

    % ---- Enhanced rules: nested scopes + shadowing + free-variable detection ----
    % Bridge: keep the original function-level facts useful in a lexical-scope setting.
    declared_in_scope(X, S) :- declared_in(X, F), function_scope(F, S).

    scope(global).
    scope(S) :- function_scope(_, S).
    scope(S) :- scope_parent(S, _).
    scope(S) :- scope_parent(_, S).
    scope(S) :- declared_in_scope(_, S).
    scope(S) :- use_in(_, S).

    ancestor_or_self(S, S) :- scope(S).
    ancestor_or_self(S, A) :- scope_parent(S, P), ancestor_or_self(P, A).

    reachable_decl(UseS, X, DeclS) :- ancestor_or_self(UseS, DeclS), declared_in_scope(X, DeclS).
    shadowed_by(UseS, X, DeclS) :- reachable_decl(UseS, X, DeclS), reachable_decl(UseS, X, DeclS2), ancestor_or_self(DeclS2, DeclS), DeclS2 != DeclS.
    binding(UseS, X, DeclS) :- reachable_decl(UseS, X, DeclS), not shadowed_by(UseS, X, DeclS).

    resolved_use(X, UseS, DeclS) :- use_in(X, UseS), binding(UseS, X, DeclS).
    free_var(X, UseS) :- use_in(X, UseS), not binding(UseS, X, _).

    shadowing(X, InnerS, OuterS) :- declared_in_scope(X, InnerS), declared_in_scope(X, OuterS), ancestor_or_self(InnerS, OuterS), InnerS != OuterS.
    orphan_use(X, UseS) :- use_in(X, UseS), not variable(X).

    #show binding/3.
    #show resolved_use/3.
    #show free_var/2.
    #show shadowing/3.
    #show orphan_use/2.

    #show type_of/2.
    #show function_scope/2.
    #show scope_parent/2.
    #show declared_in_scope/2.
    #show use_in/2.
    """
).lstrip()


def asp_str(s: str) -> str:
    # Use clingo string constants for identifiers to avoid uppercase issues.
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def generate_asp_file(path: Path, facts: str) -> None:
    asp_code = BASE_RULES.format(facts=facts.strip())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(asp_code, encoding="utf-8")


def run_clingo(asp_path: Path) -> tuple[str, str, int, list[str]]:
    cmd = ["clingo", str(asp_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        cmd = [sys.executable, "-m", "clingo", str(asp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout, result.stderr, result.returncode, cmd


def tyc_type_to_asp(typ) -> str:
    # Import inside to keep this script runnable even if vendoring is missing.
    from src.utils.nodes import IntType, FloatType, StringType, VoidType, StructType

    if isinstance(typ, IntType):
        return "int"
    if isinstance(typ, FloatType):
        return "float"
    if isinstance(typ, StringType):
        return "string"
    if isinstance(typ, VoidType):
        return "void"
    if isinstance(typ, StructType):
        # Keep this an atom so existing ASP comparisons stay simple.
        return f"struct_{typ.struct_name.lower()}"
    return "unknown"


@dataclass(frozen=True)
class Facts:
    asp: str


def generate_facts_from_tyc(program_text: str) -> Facts:
    if not VENDOR_TYC.exists():
        raise RuntimeError(f"Missing vendored TyC at {VENDOR_TYC}")

    # Make vendored packages importable.
    # Note: the generated lexer/parser import `lexererr` as a top-level module.
    vendor_root = str(VENDOR_TYC)
    vendor_build = str(VENDOR_TYC / "build")
    if vendor_build not in sys.path:
        sys.path.insert(0, vendor_build)
    if vendor_root not in sys.path:
        sys.path.insert(0, vendor_root)

    from antlr4 import CommonTokenStream, InputStream
    from build.TyCLexer import TyCLexer
    from build.TyCParser import TyCParser
    from src.utils.error_listener import NewErrorListener
    from src.astgen.ast_generation import ASTGeneration
    from src.semantics.static_checker import StaticChecker

    class TracingStaticChecker(StaticChecker):
        def __init__(self):
            super().__init__()
            self._next_scope_id = 0
            self._scope_ids: dict[int, str] = {}
            self._scope_id_stack: list[str] = []
            self._facts: list[str] = []
            self._seen_decl: set[tuple[str, str]] = set()
            self._seen_use: set[tuple[str, str]] = set()
            self._seen_type: set[tuple[str, str]] = set()

        def _cur_scope_id(self) -> str:
            return self._scope_id_stack[-1] if self._scope_id_stack else "global"

        def _new_scope_id(self) -> str:
            sid = f"s{self._next_scope_id}"
            self._next_scope_id += 1
            return sid

        def _enter_scope(self):
            parent = self._cur_scope_id()
            scope_dict = {}
            self.scopes.append(scope_dict)

            sid = self._new_scope_id()
            self._scope_ids[id(scope_dict)] = sid
            self._scope_id_stack.append(sid)

            self._facts.append(f"scope_parent({sid},{parent}).")

        def _leave_scope(self):
            # Before popping, snapshot final types in this scope.
            active = self._active_scope()
            if active is not None:
                for name, info in active.items():
                    typ = info.get("type")
                    if typ is None or self._is_pending_type(typ):
                        continue
                    t = tyc_type_to_asp(typ)
                    key = (name, t)
                    if key not in self._seen_type:
                        self._seen_type.add(key)
                        self._facts.append(f"type_of({asp_str(name)},{t}).")

            super()._leave_scope()
            if self._scope_id_stack:
                self._scope_id_stack.pop()

        def _bind_local(self, name, typ, node):
            super()._bind_local(name, typ, node)
            sid = self._cur_scope_id()

            self._facts.append(f"variable({asp_str(name)}).")

            key = (name, sid)
            if key not in self._seen_decl:
                self._seen_decl.add(key)
                self._facts.append(f"declared_in_scope({asp_str(name)},{sid}).")

        def visit_identifier(self, node, o=None):
            sid = self._cur_scope_id()
            self._facts.append(f"variable({asp_str(node.name)}).")

            key = (node.name, sid)
            if key not in self._seen_use:
                self._seen_use.add(key)
                self._facts.append(f"use_in({asp_str(node.name)},{sid}).")

            return super().visit_identifier(node, o)

        def visit_assign_expr(self, node, o=None):
            # Ensure LHS counts as a use per project requirement.
            from src.utils.nodes import Identifier

            sid = self._cur_scope_id()
            if isinstance(node.lhs, Identifier):
                self._facts.append(f"variable({asp_str(node.lhs.name)}).")
                key = (node.lhs.name, sid)
                if key not in self._seen_use:
                    self._seen_use.add(key)
                    self._facts.append(f"use_in({asp_str(node.lhs.name)},{sid}).")

            return super().visit_assign_expr(node, o)

        def visit_func_decl(self, node, o=None):
            # Copy of base logic with instrumentation for function_scope + params.
            from src.utils.nodes import VoidType
            from src.semantics.static_error import Redeclared

            if node.name in self.funcs:
                raise Redeclared("Function", node.name)
            ret_type = node.return_type
            if ret_type is not None:
                self.visit(ret_type)

            params_track = set()
            param_types = []
            for param in node.params:
                if param.name in params_track:
                    raise Redeclared("Parameter", param.name)
                params_track.add(param.name)
                self.visit(param)
                param_types.append(param.param_type)

            self.funcs[node.name] = {
                "return_type": ret_type if ret_type is not None else self.UNKNOWN,
                "param_types": param_types,
                "node": node,
            }
            self._guess_function_return(node)

            old_func = self.cur_func
            old_params = self.cur_params
            self.cur_func = node.name
            self.cur_params = set(params_track)

            self._enter_scope()  # function param scope
            func_sid = self._cur_scope_id()
            self._facts.append(f"function_scope({asp_str(node.name)},{func_sid}).")

            # Bind params into active scope and record declarations.
            for param in node.params:
                self._active_scope()[param.name] = {"type": param.param_type, "node": param}
                self._facts.append(f"variable({asp_str(param.name)}).")
                self._facts.append(f"declared_in_scope({asp_str(param.name)},{func_sid}).")

            self.visit(node.body)
            self._leave_scope()

            self.cur_func = old_func
            self.cur_params = old_params

    # Parse -> AST
    input_stream = InputStream(program_text)
    lexer = TyCLexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(NewErrorListener.INSTANCE)

    token_stream = CommonTokenStream(lexer)
    parser = TyCParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(NewErrorListener.INSTANCE)

    tree = parser.program()
    ast = ASTGeneration().visit(tree)

    # Check + trace facts
    checker = TracingStaticChecker()
    checker.check_program(ast)

    facts = "\n".join(checker._facts)
    return Facts(asp=facts)


def main() -> None:
    # Hardcoded TyC program string for demo.
    program_text = textwrap.dedent(
        """
        int foo(int x) {
            int y = 1;
            auto z = x + y;
            {
                int y = x;
                x = y;
            }
            return x;
        }
        """
    ).strip()

    facts = generate_facts_from_tyc(program_text)
    asp_path = REPO_ROOT / "cases" / "ppl" / "tyc_demo.lp"
    generate_asp_file(asp_path, facts.asp)

    stdout, stderr, code, cmd = run_clingo(asp_path)
    print(f"Clingo command: {' '.join(cmd)}")
    if stderr:
        print("\nClingo stderr:")
        print(stderr)
    print("\nClingo output:")
    print(stdout)
    if code != 0:
        raise SystemExit(code)

    print(f"\nWrote ASP program to: {asp_path}")


if __name__ == "__main__":
    main()
