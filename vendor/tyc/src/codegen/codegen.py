"""
Code generator for TyC.
"""

from typing import Any

from ..utils.nodes import *
from ..utils.nodes import StructType as ASTStructType
from ..utils.visitor import BaseVisitor
from .emitter import *
from .frame import *
from .io import IO_SYMBOL_LIST
from .utils import *


class StringArrayType:
    """Marker type for JVM main(String[] args)."""
    pass


class CodeGenerator(BaseVisitor):
    """AST -> Jasmin code generator."""

    def __init__(self):
        self.emit = None
        self.functions = {}
        self.structs = {}
        self.current_return_type = VoidType()
        self.class_name = "TyC"
        self.break_labels = []
        self.continue_labels = []
        self.expected_struct_stack = []

    def _lookup_symbol(self, name: str, sym_list: list[Symbol]) -> Symbol:
        for sym in reversed(sym_list):
            if sym.name == name:
                return sym
        raise RuntimeError(f"Undeclared symbol: {name}")

    def _same_type(self, left, right):
        if type(left) is not type(right):
            return False
        if isinstance(left, ASTStructType):
            return left.struct_name == right.struct_name
        return True

    def _field_type(self, struct_name, member):
        for name, typ in self.structs[struct_name]:
            if name == member:
                return typ
        raise RuntimeError(f"Unknown field: {struct_name}.{member}")

    def _push_null(self, frame):
        frame.push()
        return self.emit.jvm.emitPUSHNULL()

    def _default_value_code(self, typ, frame):
        if is_int_type(typ):
            return self.emit.emit_push_iconst(0, frame)
        if is_float_type(typ):
            return self.emit.emit_push_fconst("0.0", frame)
        if is_string_type(typ):
            return self.emit.emit_push_const("", StringType(), frame)
        if is_struct_type(typ):
            return self._push_null(frame)
        raise RuntimeError(f"Unsupported type: {typ}")

    def _with_expected_struct(self, typ, callback):
        if is_struct_type(typ):
            self.expected_struct_stack.append(typ)
            try:
                return callback()
            finally:
                self.expected_struct_stack.pop()
        return callback()

    def _infer_type_from_env(self, node, env):
        if isinstance(node, IntLiteral):
            return IntType()
        if isinstance(node, FloatLiteral):
            return FloatType()
        if isinstance(node, StringLiteral):
            return StringType()
        if isinstance(node, Identifier):
            return env[node.name]
        if isinstance(node, FuncCall):
            return self.functions[node.name].type.return_type
        if isinstance(node, AssignExpr):
            return self._infer_type_from_env(node.lhs, env)
        if isinstance(node, BinaryOp):
            if node.operator in ["<", "<=", ">", ">=", "==", "!=", "&&", "||"]:
                return IntType()
            left_type = self._infer_type_from_env(node.left, env)
            right_type = self._infer_type_from_env(node.right, env)
            if is_float_type(left_type) or is_float_type(right_type):
                return FloatType()
            return IntType()
        if isinstance(node, PrefixOp) or isinstance(node, PostfixOp):
            if node.operator == "!":
                return IntType()
            return self._infer_type_from_env(node.operand, env)
        if isinstance(node, MemberAccess):
            obj_type = self._infer_type_from_env(node.obj, env)
            return self._field_type(obj_type.struct_name, node.member)
        if isinstance(node, StructLiteral) and self.expected_struct_stack:
            return self.expected_struct_stack[-1]
        return IntType()

    def _infer_type(self, node: Expr, o: Access):
        if isinstance(node, IntLiteral):
            return IntType()
        if isinstance(node, FloatLiteral):
            return FloatType()
        if isinstance(node, StringLiteral):
            return StringType()
        if isinstance(node, Identifier):
            return self._lookup_symbol(node.name, o.sym).type
        if isinstance(node, AssignExpr):
            return self._infer_type(node.lhs, o)
        if isinstance(node, FuncCall):
            return self.functions[node.name].type.return_type
        if isinstance(node, MemberAccess):
            obj_type = self._infer_type(node.obj, o)
            return self._field_type(obj_type.struct_name, node.member)
        if isinstance(node, StructLiteral) and self.expected_struct_stack:
            return self.expected_struct_stack[-1]
        if isinstance(node, PrefixOp) or isinstance(node, PostfixOp):
            if node.operator == "!":
                return IntType()
            return self._infer_type(node.operand, o)
        if isinstance(node, BinaryOp):
            if node.operator in ["<", "<=", ">", ">=", "==", "!=", "&&", "||"]:
                return IntType()
            left_type = self._infer_type(node.left, o)
            right_type = self._infer_type(node.right, o)
            if is_float_type(left_type) or is_float_type(right_type):
                return FloatType()
            return IntType()
        return IntType()

    def _infer_func_return(self, func):
        env = {param.name: param.param_type for param in func.params}

        def add_var(stmt):
            if isinstance(stmt, VarDecl):
                if stmt.var_type:
                    env[stmt.name] = stmt.var_type
                elif stmt.init_value:
                    env[stmt.name] = self._infer_type_from_env(stmt.init_value, env)

        def stmt_return(stmt):
            if isinstance(stmt, ReturnStmt):
                if stmt.expr is None:
                    return VoidType()
                return self._infer_type_from_env(stmt.expr, env)
            if isinstance(stmt, VarDecl):
                add_var(stmt)
                return None
            if isinstance(stmt, BlockStmt):
                old_env = dict(env)
                try:
                    for item in stmt.statements:
                        found = stmt_return(item)
                        if found is not None:
                            return found
                    return None
                finally:
                    env.clear()
                    env.update(old_env)
            if isinstance(stmt, IfStmt):
                found = stmt_return(stmt.then_stmt)
                if found is not None:
                    return found
                if stmt.else_stmt:
                    return stmt_return(stmt.else_stmt)
            if isinstance(stmt, WhileStmt) or isinstance(stmt, ForStmt):
                return stmt_return(stmt.body)
            if isinstance(stmt, SwitchStmt):
                for case in stmt.cases:
                    found = stmt_return(BlockStmt(case.statements))
                    if found is not None:
                        return found
                if stmt.default_case:
                    return stmt_return(BlockStmt(stmt.default_case.statements))
            return None

        return stmt_return(func.body) or VoidType()

    def _emit_struct_class(self, node: StructDecl):
        old_emit = self.emit
        self.emit = Emitter(f"{node.name}.j")
        self.emit.print_out(f".source {node.name}.java\n")
        self.emit.print_out(f".class public {node.name}\n")
        self.emit.print_out(".super java/lang/Object\n")

        for mem in node.members:
            desc = self.emit.get_jvm_type(mem.member_type)
            self.emit.print_out(f".field public {mem.name} {desc}\n")

        self.emit.print_out("\n.method public <init>()V\n")
        self.emit.print_out("\taload_0\n")
        self.emit.print_out("\tinvokespecial java/lang/Object/<init>()V\n")
        self.emit.print_out("\treturn\n")
        self.emit.print_out(".limit stack 1\n")
        self.emit.print_out(".limit locals 1\n")
        self.emit.print_out(".end method\n")
        self.emit.emit_epilog()
        self.emit = old_emit

    def _emit_not(self, expr_code, frame):
        true_label = frame.get_new_label()
        end_label = frame.get_new_label()
        base = frame.get_stack_size() - 1
        code = expr_code
        code += self.emit.emit_if_false(true_label, frame)
        code += self.emit.emit_push_iconst(0, frame)
        code += self.emit.emit_goto(end_label, frame)
        code += self.emit.emit_label(true_label, frame)
        code += self.emit.emit_push_iconst(1, frame)
        code += self.emit.emit_label(end_label, frame)
        frame.curr_op_stack_size = base + 1
        return code

    def _emit_relop(self, left_code, right_code, op, typ, frame, base):
        code = left_code + right_code + self.emit.emit_re_op(op, typ, frame)
        frame.curr_op_stack_size = base + 1
        return code

    def _always_returns(self, stmt):
        if isinstance(stmt, ReturnStmt):
            return True
        if isinstance(stmt, BlockStmt):
            return bool(stmt.statements) and self._always_returns(stmt.statements[-1])
        if isinstance(stmt, IfStmt):
            return stmt.else_stmt is not None and self._always_returns(stmt.then_stmt) and self._always_returns(stmt.else_stmt)
        return False

    def visit_program(self, node: Program, o: Any = None):
        self.emit = Emitter(f"{self.class_name}.j")
        self.emit.print_out(self.emit.emit_prolog(self.class_name))

        for io_sym in IO_SYMBOL_LIST:
            self.functions[io_sym.name] = io_sym

        for decl in node.decls:
            if isinstance(decl, StructDecl):
                self.structs[decl.name] = [
                    (member.name, member.member_type) for member in decl.members
                ]

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                return_type = decl.return_type or self._infer_func_return(decl)
                param_types = [param.param_type for param in decl.params]
                self.functions[decl.name] = Symbol(
                    decl.name,
                    FunctionType(param_types, return_type),
                    CName(self.class_name),
                )

        for decl in node.decls:
            if isinstance(decl, StructDecl):
                self._emit_struct_class(decl)

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                self.visit(decl, None)

        self.emit.emit_epilog()

    def visit_func_decl(self, node: FuncDecl, o: Any = None):
        self.current_return_type = self.functions[node.name].type.return_type
        frame = Frame(node.name, self.current_return_type)
        frame.enter_scope(True)

        if node.name == "main":
            mtype = FunctionType([StringArrayType()], VoidType())
        else:
            mtype = FunctionType([p.param_type for p in node.params], self.current_return_type)

        self.emit.print_out(self.emit.emit_method(node.name, mtype, True))

        start_label = frame.get_start_label()
        end_label = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_label, frame))

        local_syms: list[Symbol] = []
        if node.name == "main":
            args_idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(
                    args_idx, "args", StringArrayType(), start_label, end_label
                )
            )

        for param in node.params:
            idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(idx, param.name, param.param_type, start_label, end_label)
            )
            local_syms.append(Symbol(param.name, param.param_type, Index(idx)))

        self.visit(node.body, SubBody(frame, local_syms))

        if is_void_type(self.current_return_type):
            self.emit.print_out(self.emit.emit_return(VoidType(), frame))

        self.emit.print_out(self.emit.emit_label(end_label, frame))
        frame.exit_scope()
        self.emit.print_out(self.emit.emit_end_method(frame))

    def visit_block_stmt(self, node: BlockStmt, o: SubBody = None):
        frame = o.frame
        frame.enter_scope(False)
        start_label = frame.get_start_label()
        end_label = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_label, frame))
        local_body = SubBody(frame, list(o.sym))
        for stmt in node.statements:
            local_body = self.visit(stmt, local_body)
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        frame.exit_scope()
        return o

    def visit_var_decl(self, node: VarDecl, o: SubBody = None):
        frame = o.frame
        idx = frame.get_new_index()
        access = Access(frame, o.sym)
        var_type = node.var_type or self._infer_type(node.init_value, access)
        self.emit.print_out(
            self.emit.emit_var(
                idx, node.name, var_type, frame.get_start_label(), frame.get_end_label()
            )
        )

        if node.init_value is None:
            self.emit.print_out(self._default_value_code(var_type, frame))
        else:
            def generate_init():
                return self.visit(node.init_value, access)
            rhs_code, _ = self._with_expected_struct(var_type, generate_init)
            self.emit.print_out(rhs_code)

        self.emit.print_out(self.emit.emit_write_var(node.name, var_type, idx, frame))
        o.sym.append(Symbol(node.name, var_type, Index(idx)))
        return o

    def visit_expr_stmt(self, node: ExprStmt, o: SubBody = None):
        code, expr_type = self.visit(node.expr, Access(o.frame, o.sym))
        self.emit.print_out(code)
        if not is_void_type(expr_type):
            self.emit.print_out(self.emit.emit_pop(o.frame))
        return o

    def visit_if_stmt(self, node: IfStmt, o: SubBody = None):
        frame = o.frame
        cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
        else_label = frame.get_new_label()
        end_label = frame.get_new_label()
        self.emit.print_out(cond_code)
        self.emit.print_out(self.emit.emit_if_false(else_label, frame))
        self.visit(node.then_stmt, o)
        if not self._always_returns(node.then_stmt):
            self.emit.print_out(self.emit.emit_goto(end_label, frame))
        self.emit.print_out(self.emit.emit_label(else_label, frame))
        if node.else_stmt:
            self.visit(node.else_stmt, o)
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        return o

    def visit_while_stmt(self, node: WhileStmt, o: SubBody = None):
        frame = o.frame
        continue_label = frame.get_new_label()
        break_label = frame.get_new_label()
        self.continue_labels.append(continue_label)
        self.break_labels.append(break_label)

        self.emit.print_out(self.emit.emit_label(continue_label, frame))
        cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
        self.emit.print_out(cond_code)
        self.emit.print_out(self.emit.emit_if_false(break_label, frame))
        self.visit(node.body, o)
        self.emit.print_out(self.emit.emit_goto(continue_label, frame))
        self.emit.print_out(self.emit.emit_label(break_label, frame))

        self.break_labels.pop()
        self.continue_labels.pop()
        return o

    def visit_for_stmt(self, node: ForStmt, o: SubBody = None):
        frame = o.frame
        if node.init:
            o = self.visit(node.init, o)

        cond_label = frame.get_new_label()
        continue_label = frame.get_new_label()
        break_label = frame.get_new_label()
        self.continue_labels.append(continue_label)
        self.break_labels.append(break_label)

        self.emit.print_out(self.emit.emit_label(cond_label, frame))
        if node.condition:
            cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
            self.emit.print_out(cond_code)
            self.emit.print_out(self.emit.emit_if_false(break_label, frame))

        self.visit(node.body, o)
        self.emit.print_out(self.emit.emit_label(continue_label, frame))
        if node.update:
            update_code, update_type = self.visit(node.update, Access(frame, o.sym))
            self.emit.print_out(update_code)
            if not is_void_type(update_type):
                self.emit.print_out(self.emit.emit_pop(frame))
        self.emit.print_out(self.emit.emit_goto(cond_label, frame))
        self.emit.print_out(self.emit.emit_label(break_label, frame))

        self.break_labels.pop()
        self.continue_labels.pop()
        return o

    def visit_switch_stmt(self, node: SwitchStmt, o: SubBody = None):
        frame = o.frame
        end_label = frame.get_new_label()
        default_label = frame.get_new_label() if node.default_case else end_label
        case_labels = [frame.get_new_label() for _ in node.cases]

        expr_code, expr_type = self.visit(node.expr, Access(frame, o.sym))
        temp_idx = frame.get_new_index()
        self.emit.print_out(expr_code)
        self.emit.print_out(self.emit.emit_write_var("$switch", expr_type, temp_idx, frame))

        for case, label in zip(node.cases, case_labels):
            self.emit.print_out(self.emit.emit_read_var("$switch", expr_type, temp_idx, frame))
            case_code, _ = self.visit(case.expr, Access(frame, o.sym))
            self.emit.print_out(case_code)
            base = frame.get_stack_size() - 2
            self.emit.print_out(self.emit.emit_re_op("==", expr_type, frame))
            frame.curr_op_stack_size = base + 1
            self.emit.print_out(self.emit.emit_if_true(label, frame))

        self.emit.print_out(self.emit.emit_goto(default_label, frame))
        self.break_labels.append(end_label)

        for case, label in zip(node.cases, case_labels):
            self.emit.print_out(self.emit.emit_label(label, frame))
            self.visit(case, o)
        if node.default_case:
            self.emit.print_out(self.emit.emit_label(default_label, frame))
            self.visit(node.default_case, o)

        self.break_labels.pop()
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        return o

    def visit_case_stmt(self, node: CaseStmt, o: SubBody = None):
        for stmt in node.statements:
            o = self.visit(stmt, o)
        return o

    def visit_default_stmt(self, node: DefaultStmt, o: SubBody = None):
        for stmt in node.statements:
            o = self.visit(stmt, o)
        return o

    def visit_break_stmt(self, node: BreakStmt, o: SubBody = None):
        self.emit.print_out(self.emit.emit_goto(self.break_labels[-1], o.frame))
        return o

    def visit_continue_stmt(self, node: ContinueStmt, o: SubBody = None):
        self.emit.print_out(self.emit.emit_goto(self.continue_labels[-1], o.frame))
        return o

    def visit_return_stmt(self, node: ReturnStmt, o: SubBody = None):
        if node.expr is None:
            self.emit.print_out(self.emit.emit_return(VoidType(), o.frame))
            return o

        def generate_expr():
            return self.visit(node.expr, Access(o.frame, o.sym))

        code, ret_type = self._with_expected_struct(self.current_return_type, generate_expr)
        self.emit.print_out(code)
        self.emit.print_out(self.emit.emit_return(ret_type, o.frame))
        return o

    def visit_binary_op(self, node: BinaryOp, o: Access = None):
        frame = o.frame
        base = frame.get_stack_size()
        left_code, left_type = self.visit(node.left, o)
        right_code, right_type = self.visit(node.right, o)

        if node.operator in ["+", "-"]:
            result_type = FloatType() if is_float_type(left_type) or is_float_type(right_type) else IntType()
            return left_code + right_code + self.emit.emit_add_op(node.operator, result_type, frame), result_type
        if node.operator in ["*", "/"]:
            result_type = FloatType() if is_float_type(left_type) or is_float_type(right_type) else IntType()
            return left_code + right_code + self.emit.emit_mul_op(node.operator, result_type, frame), result_type
        if node.operator == "%":
            return left_code + right_code + self.emit.emit_mod(frame), IntType()
        if node.operator == "&&":
            return left_code + right_code + self.emit.emit_and_op(frame), IntType()
        if node.operator == "||":
            return left_code + right_code + self.emit.emit_or_op(frame), IntType()
        if node.operator in ["<", "<=", ">", ">=", "==", "!="]:
            op_type = FloatType() if is_float_type(left_type) or is_float_type(right_type) else IntType()
            return self._emit_relop(left_code, right_code, node.operator, op_type, frame, base), IntType()
        raise RuntimeError(f"Unsupported operator: {node.operator}")

    def _assign_member(self, node, o):
        lhs = node.lhs
        obj_code, obj_type = self.visit(lhs.obj, o)
        field_type = self._field_type(obj_type.struct_name, lhs.member)

        def generate_rhs():
            return self.visit(node.rhs, o)

        rhs_code, _ = self._with_expected_struct(field_type, generate_rhs)
        field_name = f"{obj_type.struct_name}/{lhs.member}"
        code = obj_code + rhs_code
        code += self.emit.emit_dup_x1(o.frame)
        code += self.emit.emit_put_field(field_name, field_type, o.frame)
        return code, field_type

    def visit_assign_expr(self, node: AssignExpr, o: Access = None):
        if isinstance(node.lhs, Identifier):
            lhs_sym = self._lookup_symbol(node.lhs.name, o.sym)

            def generate_rhs():
                return self.visit(node.rhs, o)

            rhs_code, _ = self._with_expected_struct(lhs_sym.type, generate_rhs)
            code = rhs_code + self.emit.emit_dup(o.frame)
            code += self.emit.emit_write_var(node.lhs.name, lhs_sym.type, lhs_sym.value.value, o.frame)
            return code, lhs_sym.type
        if isinstance(node.lhs, MemberAccess):
            return self._assign_member(node, o)
        raise RuntimeError("Unsupported assignment lhs")

    def visit_func_call(self, node: FuncCall, o: Access = None):
        fn_sym = self.functions[node.name]
        fn_type = fn_sym.type
        code = ""
        for arg, param_type in zip(node.args, fn_type.param_types):
            def generate_arg(arg=arg):
                return self.visit(arg, o)
            arg_code, _ = self._with_expected_struct(param_type, generate_arg)
            code += arg_code
        code += self.emit.emit_invoke_static(f"{fn_sym.value.value}/{node.name}", fn_type, o.frame)
        return code, fn_type.return_type

    def visit_identifier(self, node: Identifier, o: Access = None):
        sym = self._lookup_symbol(node.name, o.sym)
        return self.emit.emit_read_var(node.name, sym.type, sym.value.value, o.frame), sym.type

    def visit_int_literal(self, node: IntLiteral, o: Access = None):
        return self.emit.emit_push_iconst(node.value, o.frame), IntType()

    def visit_float_literal(self, node: FloatLiteral, o: Access = None):
        return self.emit.emit_push_fconst(str(node.value), o.frame), FloatType()

    def visit_string_literal(self, node: StringLiteral, o: Access = None):
        return self.emit.emit_push_const(node.value, StringType(), o.frame), StringType()

    def visit_struct_decl(self, node: StructDecl, o: Any = None):
        return None

    def visit_member_decl(self, node: MemberDecl, o: Any = None):
        return None

    def visit_param(self, node: Param, o: Any = None):
        return None

    def visit_int_type(self, node: IntType, o: Any = None):
        return node

    def visit_float_type(self, node: FloatType, o: Any = None):
        return node

    def visit_string_type(self, node: StringType, o: Any = None):
        return node

    def visit_void_type(self, node: VoidType, o: Any = None):
        return node

    def visit_struct_type(self, node: ASTStructType, o: Any = None):
        return node

    def visit_prefix_op(self, node: PrefixOp, o: Access = None):
        frame = o.frame
        if node.operator == "+":
            return self.visit(node.operand, o)
        if node.operator == "-":
            operand_code, operand_type = self.visit(node.operand, o)
            return operand_code + self.emit.emit_neg_op(operand_type, frame), operand_type
        if node.operator == "!":
            operand_code, _ = self.visit(node.operand, o)
            return self._emit_not(operand_code, frame), IntType()
        if node.operator in ["++", "--"]:
            if not isinstance(node.operand, Identifier):
                raise RuntimeError("prefix inc/dec only supports identifier")
            sym = self._lookup_symbol(node.operand.name, o.sym)
            code = self.emit.emit_read_var(node.operand.name, sym.type, sym.value.value, frame)
            if is_float_type(sym.type):
                code += self.emit.emit_push_fconst("1.0", frame)
            else:
                code += self.emit.emit_push_iconst(1, frame)
            op = "+" if node.operator == "++" else "-"
            code += self.emit.emit_add_op(op, sym.type, frame)
            code += self.emit.emit_dup(frame)
            code += self.emit.emit_write_var(node.operand.name, sym.type, sym.value.value, frame)
            return code, sym.type
        raise RuntimeError(f"Unsupported prefix operator: {node.operator}")

    def visit_postfix_op(self, node: PostfixOp, o: Access = None):
        frame = o.frame
        if node.operator in ["++", "--"]:
            if not isinstance(node.operand, Identifier):
                raise RuntimeError("postfix inc/dec only supports identifier")
            sym = self._lookup_symbol(node.operand.name, o.sym)
            code = self.emit.emit_read_var(node.operand.name, sym.type, sym.value.value, frame)
            code += self.emit.emit_dup(frame)
            if is_float_type(sym.type):
                code += self.emit.emit_push_fconst("1.0", frame)
            else:
                code += self.emit.emit_push_iconst(1, frame)
            op = "+" if node.operator == "++" else "-"
            code += self.emit.emit_add_op(op, sym.type, frame)
            code += self.emit.emit_write_var(node.operand.name, sym.type, sym.value.value, frame)
            return code, sym.type
        raise RuntimeError(f"Unsupported postfix operator: {node.operator}")

    def visit_member_access(self, node: MemberAccess, o: Access = None):
        obj_code, obj_type = self.visit(node.obj, o)
        field_type = self._field_type(obj_type.struct_name, node.member)
        code = obj_code + self.emit.emit_get_field(
            f"{obj_type.struct_name}/{node.member}",
            field_type,
            o.frame,
        )
        return code, field_type

    def visit_struct_literal(self, node: StructLiteral, o: Access = None):
        if not self.expected_struct_stack:
            raise RuntimeError("Struct literal needs expected struct type")
        struct_type = self.expected_struct_stack[-1]
        struct_name = struct_type.struct_name
        members = self.structs[struct_name]
        code = self.emit.emit_new_instance(struct_name, o.frame)
        for value, (member_name, member_type) in zip(node.values, members):
            code += self.emit.emit_dup(o.frame)

            def generate_value(value=value):
                return self.visit(value, o)

            value_code, _ = self._with_expected_struct(member_type, generate_value)
            code += value_code
            code += self.emit.emit_put_field(f"{struct_name}/{member_name}", member_type, o.frame)
        return code, struct_type
