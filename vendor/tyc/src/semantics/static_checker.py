"""
Static Semantic Checker for TyC Programming Language

This module implements a comprehensive static semantic checker using visitor pattern
for the TyC procedural programming language. It performs type checking,
scope management, type inference, and detects all semantic errors as
specified in the TyC language specification.
"""

from functools import reduce
from typing import (
    Dict,
    List,
    Set,
    Optional,
    Any,
    Tuple,
    NamedTuple,
    Union,
    TYPE_CHECKING,
)
from ..utils.visitor import ASTVisitor
from ..utils.nodes import (
    ASTNode,
    Program,
    StructDecl,
    MemberDecl,
    FuncDecl,
    Param,
    VarDecl,
    IfStmt,
    WhileStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    ReturnStmt,
    BlockStmt,
    SwitchStmt,
    CaseStmt,
    DefaultStmt,
    Type,
    IntType,
    FloatType,
    StringType,
    VoidType,
    StructType,
    BinaryOp,
    PrefixOp,
    PostfixOp,
    AssignExpr,
    MemberAccess,
    FuncCall,
    Identifier,
    StructLiteral,
    IntLiteral,
    FloatLiteral,
    StringLiteral,
    ExprStmt,
    Expr,
    Stmt,
    Decl,
)

TyCType = Union[IntType, FloatType, StringType, VoidType, StructType]
from .static_error import (
    StaticError,
    Redeclared,
    UndeclaredIdentifier,
    UndeclaredFunction,
    UndeclaredStruct,
    TypeCannotBeInferred,
    TypeMismatchInStatement,
    TypeMismatchInExpression,
    MustInLoop,
)

class StaticChecker(ASTVisitor):
    class UnknownType:
        pass

    UNKNOWN = UnknownType()

    def __init__(self):
        self.structs = {}
        self.funcs = {
        "readInt": {"return_type": IntType(), "param_types": []},
        "readFloat": {"return_type": FloatType(), "param_types": []},
        "readString": {"return_type": StringType(), "param_types": []},
        "printInt": {"return_type": VoidType(), "param_types": [IntType()]},
        "printFloat": {"return_type": VoidType(), "param_types": [FloatType()]},
        "printString": {"return_type": VoidType(), "param_types": [StringType()]},
    }
        self.scopes = []
        self.cur_func = None
        self.cur_params = set()
        self.depth = 0
        self.switch_depth = 0

    def check_program(self, ast):
        return self.visit(ast)

    def _is_writable_target(self, expr):
        return isinstance(expr, (Identifier, MemberAccess))

    def _enter_scope(self):
        self.scopes.append({})

    def _leave_scope(self):
        self.scopes.pop() if self.scopes else None

    def _active_scope(self):
        return self.scopes[-1] if self.scopes else None

    def _local_entry(self, name):
        if self._active_scope() and name in self._active_scope():
            return self._active_scope().get(name)
        return None

    def _resolve_local(self, name):
        return next((scope[name] for scope in reversed(self.scopes) if name in scope), None)

    def _bind_local(self, name, typ, node):
        if self._local_entry(name) is not None:
            raise Redeclared("Variable", name)

        if name in self.cur_params:
            raise Redeclared("Variable", name)
        self._active_scope()[name] = {"type": typ, "node": node}

    def _reject_local_duplicate(self, name):
        if self._local_entry(name) is not None:
            raise Redeclared("Variable", name)
        if name in self.cur_params:
            raise Redeclared("Variable", name)

    def _type_matches(self, left, right):
        if type(left) != type(right):
            return False
        if isinstance(left, StructType):
            return left.struct_name == right.struct_name
        return True

    def _is_pending_type(self, typ):
        return typ is self.UNKNOWN

    def _check_struct_name(self, typ):
        if isinstance(typ, StructType):
            if typ.struct_name not in self.structs:
                raise UndeclaredStruct(typ.struct_name)

    def _is_real_type(self, typ):
        return isinstance(typ, (IntType, FloatType, StringType, VoidType, StructType))

    def _is_int_case_constant(self, expr):
        if isinstance(expr, IntLiteral):
            return True
        if isinstance(expr, PrefixOp):
            return expr.operator in ["+", "-", "!"] and self._is_int_case_constant(expr.operand)
        if isinstance(expr, BinaryOp):
            return (
                expr.operator in ["+", "-", "*", "/", "%", ">", "<", ">=", "<=", "==", "!=", "&&", "||"]
                and self._is_int_case_constant(expr.left)
                and self._is_int_case_constant(expr.right)
            )
        return False

    def _preview_expr_type(self, expr, env, expected=None):
        if isinstance(expr, IntLiteral):
            return IntType()
        if isinstance(expr, FloatLiteral):
            return FloatType()
        if isinstance(expr, StringLiteral):
            return StringType()
        if isinstance(expr, Identifier):
            typ = env.get(expr.name, self.UNKNOWN)
            if self._is_pending_type(typ) and self._is_real_type(expected) and not isinstance(expected, VoidType):
                env[expr.name] = expected
                return expected
            return typ
        if isinstance(expr, FuncCall):
            func = self.funcs.get(expr.name)
            return self.UNKNOWN if func is None else func["return_type"]
        if isinstance(expr, MemberAccess):
            obj_type = self._preview_expr_type(expr.obj, env)
            if isinstance(obj_type, StructType) and obj_type.struct_name in self.structs:
                for member in self.structs[obj_type.struct_name].members:
                    if member.name == expr.member:
                        return member.member_type
            return self.UNKNOWN
        if isinstance(expr, StructLiteral):
            if not isinstance(expected, StructType) or expected.struct_name not in self.structs:
                return self.UNKNOWN
            members = self.structs[expected.struct_name].members
            if len(expr.values) != len(members):
                return self.UNKNOWN
            for value, member in zip(expr.values, members):
                value_type = self._preview_expr_type(value, env, member.member_type)
                if not self._type_matches(value_type, member.member_type):
                    return self.UNKNOWN
            return expected
        if isinstance(expr, AssignExpr):
            lhs_type = self._preview_expr_type(expr.lhs, env)
            rhs_type = self._preview_expr_type(expr.rhs, env, None if self._is_pending_type(lhs_type) else lhs_type)
            if self._is_pending_type(lhs_type) and self._is_real_type(rhs_type) and isinstance(expr.lhs, Identifier):
                env[expr.lhs.name] = rhs_type
                return rhs_type
            return lhs_type
        if isinstance(expr, PrefixOp):
            operand_type = self._preview_expr_type(expr.operand, env)
            if expr.operator in ["+", "-"]:
                return operand_type if isinstance(operand_type, (IntType, FloatType)) else self.UNKNOWN
            if expr.operator in ["!", "++", "--"]:
                return IntType() if isinstance(operand_type, IntType) else self.UNKNOWN
        if isinstance(expr, PostfixOp):
            operand_type = self._preview_expr_type(expr.operand, env)
            return IntType() if isinstance(operand_type, IntType) else self.UNKNOWN
        if isinstance(expr, BinaryOp):
            left_type = self._preview_expr_type(expr.left, env)
            right_type = self._preview_expr_type(expr.right, env)
            if expr.operator in ["+", "-", "*", "/"]:
                if self._is_pending_type(left_type) and isinstance(expr.right, IntLiteral):
                    left_type = IntType()
                    if isinstance(expr.left, Identifier):
                        env[expr.left.name] = left_type
                if self._is_pending_type(right_type) and isinstance(expr.left, IntLiteral):
                    right_type = IntType()
                    if isinstance(expr.right, Identifier):
                        env[expr.right.name] = right_type
                if isinstance(left_type, (IntType, FloatType)) and isinstance(right_type, (IntType, FloatType)):
                    return FloatType() if isinstance(left_type, FloatType) or isinstance(right_type, FloatType) else IntType()
                return self.UNKNOWN
            if expr.operator in ["%", "&&", "||"]:
                return IntType() if isinstance(left_type, IntType) and isinstance(right_type, IntType) else self.UNKNOWN
            if expr.operator in [">", "<", ">=", "<=", "==", "!="]:
                return IntType() if isinstance(left_type, (IntType, FloatType)) and isinstance(right_type, (IntType, FloatType)) else self.UNKNOWN
        return self.UNKNOWN

    def _first_value_return_type(self, stmt, env):
        if isinstance(stmt, ReturnStmt):
            return None if stmt.expr is None else self._preview_expr_type(stmt.expr, env)
        if isinstance(stmt, BlockStmt):
            local_env = env.copy()
            for child in stmt.statements:
                result = self._first_value_return_type(child, local_env)
                if result is not None:
                    return result
            return None
        if isinstance(stmt, VarDecl):
            var_type = stmt.var_type if stmt.var_type is not None else self.UNKNOWN
            if stmt.init_value is not None:
                init_type = self._preview_expr_type(stmt.init_value, env, None if self._is_pending_type(var_type) else var_type)
                if self._is_pending_type(var_type) and self._is_real_type(init_type):
                    var_type = init_type
            env[stmt.name] = var_type
            return None
        if isinstance(stmt, ExprStmt):
            self._preview_expr_type(stmt.expr, env)
            return None
        if isinstance(stmt, IfStmt):
            result = self._first_value_return_type(stmt.then_stmt, env.copy())
            if result is not None:
                return result
            if stmt.else_stmt is not None:
                result = self._first_value_return_type(stmt.else_stmt, env.copy())
                if result is not None:
                    return result
            return None
        if isinstance(stmt, WhileStmt):
            return self._first_value_return_type(stmt.body, env.copy())
        if isinstance(stmt, ForStmt):
            local_env = env.copy()
            if stmt.init is not None:
                self._first_value_return_type(stmt.init, local_env)
            return self._first_value_return_type(stmt.body, local_env.copy())
        if isinstance(stmt, SwitchStmt):
            for case in stmt.cases:
                for child in case.statements:
                    result = self._first_value_return_type(child, env.copy())
                    if result is not None:
                        return result
            if stmt.default_case is not None:
                for child in stmt.default_case.statements:
                    result = self._first_value_return_type(child, env.copy())
                    if result is not None:
                        return result
            return None
        return None

    def _guess_function_return(self, node):
        if node.return_type is not None:
            return
        env = {param.name: param.param_type for param in node.params}
        result = self._first_value_return_type(node.body, env)
        if result is None:
            self.funcs[node.name]["return_type"] = VoidType()
        elif not self._is_pending_type(result):
            self.funcs[node.name]["return_type"] = result

    def visit_program(self, node: "Program", o: Any = None):
        [self.visit(decl) for decl in node.decls]

    def visit_struct_decl(self, node: "StructDecl", o: Any = None):
        if node.name in self.structs:
            raise Redeclared("Struct", node.name)

        mem_tracker = set()
        for mem in node.members:
            if mem.name in mem_tracker:
                raise Redeclared("Member", mem.name)
            mem_tracker.add(mem.name)
            self.visit(mem)
        self.structs[node.name] = node

    def visit_member_decl(self, node: "MemberDecl", o: Any = None):
        self.visit(node.member_type)

    def visit_func_decl(self, node: "FuncDecl", o: Any = None):
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
                                 "node": node
                                }
        self._guess_function_return(node)
        old_func = self.cur_func
        old_params = self.cur_params
        self.cur_func = node.name
        self.cur_params = set(params_track)

        self._enter_scope()
        for param in node.params:
            self._active_scope()[param.name] = {"type": param.param_type, "node": param}
        self.visit(node.body)
        self._leave_scope()
        self.cur_func = old_func
        self.cur_params = old_params

    def visit_param(self, node: "Param", o: Any = None):
        self.visit(node.param_type)
        return node.param_type

    def visit_int_type(self, node: "IntType", o: Any = None):
        return node

    def visit_float_type(self, node: "FloatType", o: Any = None):
        return node

    def visit_string_type(self, node: "StringType", o: Any = None):
        return node

    def visit_void_type(self, node: "VoidType", o: Any = None):
        return node

    def visit_struct_type(self, node: "StructType", o: Any = None):
        self._check_struct_name(node)
        return node

    def visit_block_stmt(self, node: "BlockStmt", o: Any = None):
        self._enter_scope()
        [self.visit(stmt) for stmt in node.statements]
        for symbol in self._active_scope().values():
            if self._is_pending_type(symbol["type"]):
                raise TypeCannotBeInferred(node)
        self._leave_scope()

    def visit_var_decl(self, node, o=None):
        var_type = node.var_type if node.var_type is not None else self.UNKNOWN
        self._reject_local_duplicate(node.name)

        if node.var_type is not None:
            self.visit(node.var_type)

        if node.init_value is not None:
            try:
                init_type = self.visit(node.init_value, None if self._is_pending_type(var_type) else var_type)
            except TypeCannotBeInferred as err:
                if self._is_pending_type(var_type) and err.ctx is node.init_value and isinstance(node.init_value, StructLiteral):
                    raise TypeCannotBeInferred(node)
                raise

            if self._is_pending_type(var_type):
                if self._is_pending_type(init_type):
                    raise TypeCannotBeInferred(node)
                if isinstance(init_type, VoidType):
                    raise TypeCannotBeInferred(node)
                self._bind_local(node.name, init_type, node)
                return

            if self._is_pending_type(init_type):
                raise TypeCannotBeInferred(node.init_value)

            if not self._type_matches(var_type, init_type):
                raise TypeMismatchInStatement(node)

        self._bind_local(node.name, var_type, node)

    def _fix_auto_identifier(self, expr, typ):
        if isinstance(typ, VoidType):
            return False
        if isinstance(expr, Identifier):
            sym = self._resolve_local(expr.name)
            if sym is None:
                raise UndeclaredIdentifier(expr.name)
            if not self._is_pending_type(sym["type"]):
                return self._type_matches(sym["type"], typ)
            sym["type"] = typ
            return True
        return False

    def _read_lhs_type(self, expr):
        if isinstance(expr, Identifier):
            sym = self._resolve_local(expr.name)
            if sym is None:
                raise UndeclaredIdentifier(expr.name)
            return sym["type"]
        if isinstance(expr, MemberAccess):
            return self.visit(expr)
        return self.UNKNOWN

    def visit_if_stmt(self, node: "IfStmt", o: Any = None):
        try:
            cond_type = self.visit(node.condition)
        except TypeCannotBeInferred as err:
            if err.ctx is node.condition and isinstance(node.condition, StructLiteral):
                raise TypeMismatchInStatement(node)
            raise
        if self._is_pending_type(cond_type):
            if not self._fix_auto_identifier(node.condition, IntType()):
                raise TypeCannotBeInferred(node.condition)
            cond_type = IntType()
        if not isinstance(cond_type, IntType):
            raise TypeMismatchInStatement(node)
        self.visit(node.then_stmt)
        if node.else_stmt is not None:
            self.visit(node.else_stmt)

    def visit_while_stmt(self, node: "WhileStmt", o: Any = None):
        cond_type = self.visit(node.condition)
        if self._is_pending_type(cond_type):
            if not self._fix_auto_identifier(node.condition, IntType()):
                raise TypeCannotBeInferred(node.condition)
            cond_type = IntType()
        if not isinstance(cond_type, IntType):
            raise TypeMismatchInStatement(node)

        self.depth += 1
        self.visit(node.body)
        self.depth -= 1

    def visit_for_stmt(self, node: "ForStmt", o: Any = None):
        if node.init is not None:
            self.visit(node.init)
        if node.condition is not None:
            cond_type = self.visit(node.condition)
            if self._is_pending_type(cond_type):
                if not self._fix_auto_identifier(node.condition, IntType()):
                    raise TypeCannotBeInferred(node.condition)
                cond_type = IntType()
            if not isinstance(cond_type, IntType):
                raise TypeMismatchInStatement(node)
        if node.update is not None:
            self.visit(node.update)
        self.depth += 1
        self._enter_scope()
        self.visit(node.body)
        for symbol in self._active_scope().values():
            if self._is_pending_type(symbol["type"]):
                raise TypeCannotBeInferred(node)
        self._leave_scope()
        self.depth -= 1

    def visit_switch_stmt(self, node: "SwitchStmt", o: Any = None):
        switch_type = self.visit(node.expr)
        if self._is_pending_type(switch_type):
            if not self._fix_auto_identifier(node.expr, IntType()):
                raise TypeCannotBeInferred(node.expr)
            switch_type = IntType()
        if not isinstance(switch_type, IntType):
            raise TypeMismatchInStatement(node)

        self.switch_depth += 1

        for case in node.cases:
            self.visit(case)
        if node.default_case is not None:
            self.visit(node.default_case)
        self.switch_depth -= 1

    def visit_case_stmt(self, node: "CaseStmt", o: Any = None):
        if not self._is_int_case_constant(node.expr):
            try:
                self.visit(node.expr)
            except TypeCannotBeInferred as err:
                if err.ctx is node.expr and isinstance(node.expr, StructLiteral):
                    raise TypeMismatchInStatement(node)
                raise
            raise TypeMismatchInStatement(node)
        case_type = self.visit(node.expr)
        if self._is_pending_type(case_type):
            if not self._fix_auto_identifier(node.expr, IntType()):
                raise TypeCannotBeInferred(node.expr)
            case_type = IntType()
        if not isinstance(case_type, IntType):
            raise TypeMismatchInStatement(node)

        for stmt in node.statements:
            self.visit(stmt)


    def visit_default_stmt(self, node: "DefaultStmt", o: Any = None):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_break_stmt(self, node: "BreakStmt", o: Any = None):
        if self.depth == 0 and self.switch_depth == 0:
            raise MustInLoop(node)

    def visit_continue_stmt(self, node: "ContinueStmt", o: Any = None):
        if self.depth == 0:
            raise MustInLoop(node)

    def visit_return_stmt(self, node: "ReturnStmt", o: Any = None):
        expected = self.funcs[self.cur_func]['return_type']
        if node.expr is None:
            re = VoidType()
            if self._is_pending_type(expected):
                return
        else:
            re = self.visit(node.expr, None if self._is_pending_type(expected) else expected)
            if self._is_pending_type(re):
                if self._is_pending_type(expected) or not self._fix_auto_identifier(node.expr, expected):
                    raise TypeCannotBeInferred(node)
                re = expected
            if isinstance(expected, VoidType):
                raise TypeMismatchInStatement(node)
        if self._is_pending_type(expected):
            self.funcs[self.cur_func]['return_type'] = re
            return

        if not self._type_matches(re, expected):
            raise TypeMismatchInStatement(node)

    def visit_expr_stmt(self, node: "ExprStmt", o: Any = None):
        expr_type = self.visit(node.expr, node)
        if self._is_pending_type(expr_type):
            raise TypeCannotBeInferred(node)

    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if self._is_pending_type(left_type) and self._is_pending_type(right_type) and node.operator not in ["%", "&&", "||"]:
            raise TypeCannotBeInferred(node)

        if node.operator in ["+", "-", "*", "/"]:


            if self._is_pending_type(left_type):
                if not isinstance(node.right, IntLiteral):
                    raise TypeCannotBeInferred(node)
                if not self._fix_auto_identifier(node.left, IntType()):
                    raise TypeCannotBeInferred(node)
                left_type = IntType()

            if self._is_pending_type(right_type):
                if not isinstance(node.left, IntLiteral):
                    raise TypeCannotBeInferred(node)
                if not self._fix_auto_identifier(node.right, IntType()):
                    raise TypeCannotBeInferred(node)
                right_type = IntType()

            if isinstance(left_type, (IntType, FloatType)) and isinstance(right_type, (IntType, FloatType)):
                return FloatType() if isinstance(left_type, FloatType) or isinstance(right_type, FloatType) else IntType()
            raise TypeMismatchInExpression(node)
        if node.operator == '%':
            if self._is_pending_type(left_type):
                if not self._fix_auto_identifier(node.left, IntType()):
                    raise TypeCannotBeInferred(node)
                left_type = IntType()
            if self._is_pending_type(right_type):
                if not self._fix_auto_identifier(node.right, IntType()):
                    raise TypeCannotBeInferred(node)
                right_type = IntType()
            if isinstance(left_type, IntType) and isinstance(right_type, IntType):
                return IntType()
            raise TypeMismatchInExpression(node)
        if node.operator in [">", "<", ">=", "<=", '==', '!=']:
            if self._is_pending_type(left_type) or self._is_pending_type(right_type):
                raise TypeCannotBeInferred(node)
            if isinstance(left_type, (IntType, FloatType)) and isinstance(right_type, (IntType, FloatType)):
                return IntType()
            raise TypeMismatchInExpression(node)

        if node.operator in ["&&", "||"]:
            if self._is_pending_type(left_type):
                if not self._fix_auto_identifier(node.left, IntType()):
                    raise TypeCannotBeInferred(node)
                left_type = IntType()
            if self._is_pending_type(right_type):
                if not self._fix_auto_identifier(node.right, IntType()):
                    raise TypeCannotBeInferred(node)
                right_type = IntType()
            if isinstance(left_type, IntType) and isinstance(right_type, IntType):
                return IntType()
            raise TypeMismatchInExpression(node)

    def visit_prefix_op(self, node: "PrefixOp", o: Any = None):
        operand_type = self.visit(node.operand)
        if node.operator in ["+", "-"]:
            if self._is_pending_type(operand_type):
                if not isinstance(o, (IntType, FloatType)):
                    raise TypeCannotBeInferred(node)
                if not self._fix_auto_identifier(node.operand, o):
                    raise TypeCannotBeInferred(node)
                return o
            if isinstance(operand_type, (IntType, FloatType)):
                return operand_type
            raise TypeMismatchInExpression(node)
        if node.operator == '!':
            if self._is_pending_type(operand_type):
                if not self._fix_auto_identifier(node.operand, IntType()):
                    raise TypeCannotBeInferred(node)
                return IntType()
            if isinstance(operand_type, IntType):
                return IntType()
            raise TypeMismatchInExpression(node)

        if node.operator in ["++", "--"]:
            if not self._is_writable_target(node.operand):
                raise TypeMismatchInExpression(node)
            if self._is_pending_type(operand_type):
                if not self._fix_auto_identifier(node.operand, IntType()):
                    raise TypeCannotBeInferred(node)
                return IntType()
            if isinstance(operand_type, IntType):
                return IntType()
            raise TypeMismatchInExpression(node)

    def visit_postfix_op(self, node: "PostfixOp", o: Any = None):
        operand_type = self.visit(node.operand)
        if node.operator in ["++", "--"]:
            if not self._is_writable_target(node.operand):
                raise TypeMismatchInExpression(node)
            if self._is_pending_type(operand_type):
                if not self._fix_auto_identifier(node.operand, IntType()):
                    raise TypeCannotBeInferred(node)
                return IntType()
            if isinstance(operand_type, IntType):
                return IntType()
            raise TypeMismatchInExpression(node)
        raise TypeMismatchInExpression(node)

    def visit_assign_expr(self, node: "AssignExpr", o: Any = None):

        if not self._is_writable_target(node.lhs):
            raise TypeMismatchInExpression(node)
        lhs_type = self.visit(node.lhs)
        rhs_type = self.visit(node.rhs, None if self._is_pending_type(lhs_type) else lhs_type)
        if self._is_pending_type(lhs_type):
            lhs_type = self._read_lhs_type(node.lhs)

        if self._is_pending_type(lhs_type) and self._is_pending_type(rhs_type):
            raise TypeCannotBeInferred(node)
        if self._is_pending_type(lhs_type) and isinstance(rhs_type, VoidType):
            raise TypeCannotBeInferred(node)
        if self._is_pending_type(lhs_type):
            if not self._fix_auto_identifier(node.lhs, rhs_type):
                if isinstance(o, ExprStmt):
                    raise TypeMismatchInStatement(o)
                raise TypeMismatchInExpression(node)
            return rhs_type
        if self._is_pending_type(rhs_type):
            if not self._fix_auto_identifier(node.rhs, lhs_type):
                if isinstance(o, ExprStmt):
                    raise TypeMismatchInStatement(o)
                raise TypeMismatchInExpression(node)
            return lhs_type
        if not self._type_matches(lhs_type, rhs_type):
            if isinstance(o, ExprStmt):
                raise TypeMismatchInStatement(o)
            raise TypeMismatchInExpression(node)
        return lhs_type

    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        obj_type = self.visit(node.obj)
        if self._is_pending_type(obj_type):
            raise TypeCannotBeInferred(node)
        if not isinstance(obj_type, StructType):
            raise TypeMismatchInExpression(node)
        self._check_struct_name(obj_type)
        struct_decl = self.structs[obj_type.struct_name]
        for member in struct_decl.members:
            if member.name == node.member:
                return member.member_type
        raise TypeMismatchInExpression(node)

    def visit_func_call(self, node: "FuncCall", o: Any = None):
        func = self.funcs.get(node.name)
        if func is None:
            raise UndeclaredFunction(node.name)
        for index, arg in enumerate(node.args):
            param_type = func["param_types"][index] if index < len(func["param_types"]) else None
            if param_type is None:
                self.visit(arg)
                continue
            arg_type = self.visit(arg, param_type)
            if self._is_pending_type(arg_type):
                if not self._fix_auto_identifier(arg, param_type):
                    raise TypeCannotBeInferred(node)
            elif not self._type_matches(arg_type, param_type):
                    raise TypeMismatchInExpression(node)
        if len(node.args) != len(func["param_types"]):
            raise TypeMismatchInExpression(node)
        return func["return_type"]

    def visit_identifier(self, node: "Identifier", o: Any = None):
        sym = self._resolve_local(node.name)
        if sym is None:
            raise UndeclaredIdentifier(node.name)
        if self._is_pending_type(sym["type"]) and self._is_real_type(o) and not isinstance(o, VoidType):
            sym["type"] = o
        return sym["type"]

    def visit_struct_literal(self, node: "StructLiteral", o: Any = None):
        expected = o
        if not isinstance(expected, StructType):
            for value in node.values:
                self.visit(value)
            raise TypeCannotBeInferred(node)
        self._check_struct_name(expected)
        struct_decl = self.structs[expected.struct_name]
        unfixed_extra = False
        for value, member in zip(node.values, struct_decl.members):
            value_type = self.visit(value, member.member_type)
            member_type = member.member_type
            if self._is_pending_type(value_type):
                if not self._fix_auto_identifier(value, member.member_type):
                    raise TypeCannotBeInferred(node)
                value_type = member_type
            if not self._type_matches(value_type, member.member_type):
                raise TypeMismatchInExpression(node)
        for value in node.values[len(struct_decl.members):]:
            value_type = self.visit(value)
            if self._is_pending_type(value_type):
                unfixed_extra = True
        if len(node.values) != len(struct_decl.members):
            if unfixed_extra:
                raise TypeCannotBeInferred(node)
            raise TypeMismatchInExpression(node)
        return expected
    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        return IntType()
    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        return FloatType()

    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        return StringType()
