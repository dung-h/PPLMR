import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASP_DIR = REPO_ROOT / "asp" / "ppl"
CASES_DIR = REPO_ROOT / "cases" / "ppl"
ASP_FILENAME = "scope_binding.lp"

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
    % If callers only provide declared_in/2 + function_scope/2 (old cases), we treat the
    % function scope as the declaration scope.
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

    % Diagnostics: shadowing and ill-formed uses.
    shadowing(X, InnerS, OuterS) :- declared_in_scope(X, InnerS), declared_in_scope(X, OuterS), ancestor_or_self(InnerS, OuterS), InnerS != OuterS.
    orphan_use(X, UseS) :- use_in(X, UseS), not variable(X).

    #show global_variable/1.
    #show local_variable/2.
    #show in_scope/2.
    #show bound_variable/2.
    #show orphan_declaration/2.
    #show missing_scope/1.
    #show untyped_variable/1.
    #show non_int_type/2.

    #show binding/3.
    #show resolved_use/3.
    #show free_var/2.
    #show shadowing/3.
    #show orphan_use/2.
    """
).lstrip()

CASES: list[dict[str, object]] = [
    {
        "name": "baseline",
        "description": "All variables are local with int types.",
        "facts": """
        variable(x).
        variable(y).
        variable(z).

        declared_in(x, foo).
        declared_in(y, bar).
        declared_in(z, foo).

        function_scope(foo, f1).
        function_scope(bar, f2).

        type_of(x, int).
        type_of(y, int).
        type_of(z, int).
        """,
        "expect_in": [
            "local_variable(x,foo)",
            "local_variable(y,bar)",
            "local_variable(z,foo)",
            "in_scope(x,f1)",
            "in_scope(y,f2)",
            "in_scope(z,f1)",
            "bound_variable(x,f1)",
            "bound_variable(y,f2)",
            "bound_variable(z,f1)",
        ],
        "expect_out": ["global_variable(x)", "global_variable(y)", "global_variable(z)"],
    },
    {
        "name": "global_only",
        "description": "A variable without declaration becomes global.",
        "facts": """
        variable(w).
        type_of(w, int).
        """,
        "expect_in": ["global_variable(w)", "in_scope(w,global)", "bound_variable(w,global)"],
        "expect_out": ["local_variable(w,_)"] ,
    },
    {
        "name": "untyped",
        "description": "Declared variable without a type is not bound.",
        "facts": """
        variable(u).
        declared_in(u, foo).
        function_scope(foo, f1).
        """,
        "expect_in": ["local_variable(u,foo)", "in_scope(u,f1)", "untyped_variable(u)"],
        "expect_out": ["bound_variable(u,f1)"],
    },
    {
        "name": "non_int_type",
        "description": "Non-int types should not be bound.",
        "facts": """
        variable(v).
        declared_in(v, foo).
        function_scope(foo, f1).
        type_of(v, string).
        """,
        "expect_in": ["local_variable(v,foo)", "in_scope(v,f1)", "non_int_type(v,string)"],
        "expect_out": ["bound_variable(v,f1)"],
    },
    {
        "name": "missing_function_scope",
        "description": "Declared in a function without scope mapping.",
        "facts": """
        variable(k).
        declared_in(k, missing).
        type_of(k, int).
        """,
        "expect_in": ["local_variable(k,missing)", "missing_scope(missing)"],
        "expect_out": ["in_scope(k,_)"] ,
    },
    {
        "name": "orphan_declaration",
        "description": "Declaration without a variable fact.",
        "facts": """
        declared_in(q, foo).
        function_scope(foo, f1).
        type_of(q, int).
        """,
        "expect_in": ["local_variable(q,foo)", "in_scope(q,f1)", "orphan_declaration(q,foo)"],
        "expect_out": ["global_variable(q)"],
    },
    {
        "name": "multi_decl",
        "description": "Same variable declared in multiple functions.",
        "facts": """
        variable(x).
        declared_in(x, foo).
        declared_in(x, bar).
        function_scope(foo, f1).
        function_scope(bar, f2).
        type_of(x, int).
        """,
        "expect_in": [
            "local_variable(x,foo)",
            "local_variable(x,bar)",
            "in_scope(x,f1)",
            "in_scope(x,f2)",
            "bound_variable(x,f1)",
            "bound_variable(x,f2)",
        ],
        "expect_out": ["global_variable(x)"],
    },
    {
        "name": "mixed_global_local",
        "description": "Mix of local and global variables.",
        "facts": """
        variable(a).
        variable(b).
        declared_in(a, foo).
        function_scope(foo, f1).
        type_of(a, int).
        type_of(b, int).
        """,
        "expect_in": ["local_variable(a,foo)", "in_scope(a,f1)", "global_variable(b)"],
        "expect_out": ["global_variable(a)", "local_variable(b,_)"] ,
    },
    {
        "name": "global_non_int",
        "description": "A global variable with non-int type stays unbound but is still diagnosed.",
        "facts": """
        variable(g).
        type_of(g, bool).
        """,
        "expect_in": ["global_variable(g)", "in_scope(g,global)", "non_int_type(g,bool)"],
        "expect_out": ["bound_variable(g,global)"] ,
    },
    {
        "name": "mixed_diagnostics",
        "description": "One case combines local binding, global non-int data, and orphan declarations.",
        "facts": """
        variable(a).
        variable(b).
        declared_in(a, foo).
        declared_in(c, foo).
        function_scope(foo, f1).
        type_of(a, int).
        type_of(b, string).
        """,
        "expect_in": [
            "local_variable(a,foo)",
            "in_scope(a,f1)",
            "bound_variable(a,f1)",
            "global_variable(b)",
            "in_scope(b,global)",
            "non_int_type(b,string)",
            "orphan_declaration(c,foo)",
            "in_scope(c,f1)",
        ],
        "expect_out": ["bound_variable(b,global)", "global_variable(c)"],
    },

    {
        "name": "shadowing_nested_scope",
        "description": "Nested lexical scopes: inner declaration shadows outer, and uses resolve to the closest declaration.",
        "facts": """
        variable(x).
        type_of(x, int).

        % A function scope with one nested block scope.
        function_scope(foo, s_foo).
        scope_parent(s_block, s_foo).

        % Two declarations of x in different scopes (shadowing).
        declared_in_scope(x, s_foo).
        declared_in_scope(x, s_block).

        % Uses from each scope should bind differently.
        use_in(x, s_block).
        use_in(x, s_foo).
        """,
        "expect_in": [
            "shadowing(x,s_block,s_foo)",
            "binding(s_block,x,s_block)",
            "binding(s_foo,x,s_foo)",
            "resolved_use(x,s_block,s_block)",
            "resolved_use(x,s_foo,s_foo)",
        ],
        "expect_out": ["free_var(x,s_block)", "free_var(x,s_foo)"],
    },

    {
        "name": "free_variable_use",
        "description": "A variable used in a scope with no reachable declaration is a free variable.",
        "facts": """
        function_scope(foo, s_foo).
        scope_parent(s_block, s_foo).

        % y is used but never declared (and not even introduced as variable/1).
        use_in(y, s_block).
        """,
        "expect_in": ["free_var(y,s_block)", "orphan_use(y,s_block)"],
        "expect_out": ["resolved_use(y,s_block,_)"],
    },
]


def generate_asp_file(path: Path, facts: str) -> None:
    asp_code = BASE_RULES.format(facts=facts.strip())
    path.write_text(asp_code, encoding="utf-8")
    print(f"ASP file created: {path}")


def run_clingo(asp_path: Path) -> tuple[str, str, int, list[str]]:
    cmd = ["clingo", str(asp_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        cmd = [sys.executable, "-m", "clingo", str(asp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    return result.stdout, result.stderr, result.returncode, cmd


def parse_models(output: str) -> list[str]:
    lines = output.splitlines()
    models: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Answer:"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                models.append(lines[j].strip())
                i = j
        i += 1
    return models


def expand_expected(expected: str, atoms: set[str]) -> bool:
    if expected.endswith("_)"):
        prefix = expected[:-2]
        if prefix.endswith(","):
            return any(atom.startswith(prefix) for atom in atoms)
    if expected.endswith("(_)"):
        prefix = expected[:-3]
        return any(atom.startswith(prefix) for atom in atoms)
    return expected in atoms


def check_expectations(
    atoms: set[str],
    expect_in: list[str],
    expect_out: list[str],
) -> list[str]:
    issues: list[str] = []
    for exp in expect_in:
        if not expand_expected(exp, atoms):
            issues.append(f"Missing expected atom: {exp}")
    for exp in expect_out:
        if expand_expected(exp, atoms):
            issues.append(f"Unexpected atom present: {exp}")
    return issues


def analyze_results(case: dict[str, object], output: str) -> bool:
    models = parse_models(output)
    if not models:
        print("No stable models found.")
        return False

    expect_in = case.get("expect_in", [])
    expect_out = case.get("expect_out", [])

    success = True
    for idx, model_line in enumerate(models, start=1):
        atoms = set(model_line.split())
        print(f"\nStable Model {idx}:")
        print(model_line)

        issues = check_expectations(
            atoms,
            list(expect_in),
            list(expect_out),
        )
        if issues:
            success = False
            print("Expectation check: FAIL")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("Expectation check: PASS")

    return success


def main() -> None:
    ASP_DIR.mkdir(parents=True, exist_ok=True)
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    passed = 0
    total = len(CASES)

    for case in CASES:
        name = str(case["name"])
        description = str(case["description"])
        facts = str(case["facts"])

        if name == "baseline":
            asp_path = ASP_DIR / ASP_FILENAME
        else:
            asp_path = CASES_DIR / f"{name}.lp"

        generate_asp_file(asp_path, textwrap.dedent(facts))

        print(f"\n=== Case: {name} ===")
        print(description)

        stdout, stderr, code, cmd = run_clingo(asp_path)
        print(f"\nClingo command: {' '.join(cmd)}")
        if stderr:
            print("\nClingo stderr:")
            print(stderr)

        print("\nClingo Output:")
        print(stdout)

        ok = analyze_results(case, stdout)
        if ok:
            passed += 1

        if code != 0:
            print(f"\nClingo exited with code {code}.")

    print(f"\nSummary: {passed}/{total} cases passed.")


if __name__ == "__main__":
    main()
