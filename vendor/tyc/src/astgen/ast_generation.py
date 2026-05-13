"""
AST Generation module for TyC programming language.
This module contains the ASTGeneration class that converts parse trees
into Abstract Syntax Trees using the visitor pattern.
"""

from functools import reduce
from build.TyCVisitor import TyCVisitor
from build.TyCParser import TyCParser
from src.utils.nodes import *


class ASTGeneration(TyCVisitor):
    """AST Generation visitor for TyC language."""

    # 1. Implement Top-Level Constructs: Program/ Declaration/ Function/ Struct/ Typ
    # program: declList EOF
    def visitProgram(self, ctx):
        declList = self.visit(ctx.declList())
        return Program(declList)
    
    # declList: decl declList | ;
    def visitDeclList(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        else:
            decl = self.visit(ctx.decl())
            declList = self.visit(ctx.declList())
            return [decl] + declList

    # decl: structDecl | funcDecl;
    def visitDecl(self, ctx):
        if ctx.structDecl():
            return self.visit(ctx.structDecl())
        elif ctx.funcDecl():
            return self.visit(ctx.funcDecl())
    
    # structDecl: K_STRUCT ID LB memberList RB SEMI;
    def visitStructDecl(self, ctx):
        structName = ctx.ID().getText()
        memberList = self.visit(ctx.memberList())
        return StructDecl(structName, memberList)
    #  memberList: member memberList | ;
    def visitMemberList(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        else:
            member = self.visit(ctx.member())
            memberList = self.visit(ctx.memberList())
            return [member] + memberList
    # member: typ ID SEMI;
    def visitMember(self, ctx):
        typ = self.visit(ctx.typ())
        memberName = ctx.ID().getText()
        return MemberDecl(typ, memberName)
    
    # typ: K_INT | K_FLOAT | K_STRING | ID;
    def visitTyp(self, ctx):
        if ctx.K_INT():
            return IntType()
        elif ctx.K_FLOAT():
            return FloatType()
        elif ctx.K_STRING():
            return StringType()
        return StructType(ctx.ID().getText())

    # funcDecl: (typ | K_VOID)? ID LP paramList RP stmtBlock;
    def visitFuncDecl(self, ctx):
        returnType = None
        if ctx.typ():
            returnType = self.visit(ctx.typ())
        elif ctx.K_VOID():
            returnType = VoidType()

        funcName = ctx.ID().getText()
        funcParams = self.visit(ctx.paramList())
        funcBody = self.visit(ctx.stmtBlock())
        return FuncDecl(returnType, funcName, funcParams, funcBody)
    
    # paramList: param paramPrime | ;
    def visitParamList(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        param = self.visit(ctx.param())
        paramPrime = self.visit(ctx.paramPrime())
        return [param] + paramPrime
    
    # paramPrime: COMMA param paramPrime | ;
    def visitParamPrime(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        param = self.visit(ctx.param())
        paramPrime = self.visit(ctx.paramPrime())
        return [param] + paramPrime

    # param: typ ID;
    def visitParam(self, ctx):
        paramType = self.visit(ctx.typ())
        paramName = ctx.ID().getText()
        return Param(paramType, paramName)
    
    # 2. Implement Statements: stmtBlock, varDecl, if/while/for/switch, return/break/continue/exprStmt
    # stmtBlock: LB stmtList RB;
    def visitStmtBlock(self, ctx):
        stmtList = self.visit(ctx.stmtList())
        return BlockStmt(stmtList)
    
    # stmtList: stmt stmtList | ;
    def visitStmtList(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        stmt = self.visit(ctx.stmt())
        stmtList = self.visit(ctx.stmtList())
        return [stmt] + stmtList
    # stmt: varDeclStmt | stmtBlock | exprStmt | ifStmt | whileStmt | forStmt | switchStmt | returnStmt | breakStmt | continueStmt;
    def visitStmt(self, ctx):
        if ctx.varDeclStmt():
            return self.visit(ctx.varDeclStmt())
        elif ctx.stmtBlock():
            return self.visit(ctx.stmtBlock())
        elif ctx.exprStmt():
            return self.visit(ctx.exprStmt())
        elif ctx.ifStmt():
            return self.visit(ctx.ifStmt())
        elif ctx.whileStmt():
            return self.visit(ctx.whileStmt())
        elif ctx.forStmt():
            return self.visit(ctx.forStmt())
        elif ctx.switchStmt():
            return self.visit(ctx.switchStmt())
        elif ctx.returnStmt():
            return self.visit(ctx.returnStmt())
        elif ctx.breakStmt():
            return self.visit(ctx.breakStmt())
        elif ctx.continueStmt():
            return self.visit(ctx.continueStmt())

    # varDeclStmt: (typ| K_AUTO) ID (ASSIGN expr)? SEMI;
    def visitVarDeclStmt(self, ctx):
        varType = self.visit(ctx.typ()) if ctx.typ() else None
        varName = ctx.ID().getText()
        initValue = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(varType, varName, initValue)
    
    # ifStmt: K_IF LP expr RP stmt (K_ELSE stmt)?;
    def visitIfStmt(self, ctx):
        valExpr = self.visit(ctx.expr())
        thenStmt = self.visit(ctx.stmt(0))
        elseStmt = None
        if ctx.K_ELSE():
            elseStmt = self.visit(ctx.stmt(1))
        return IfStmt(valExpr, thenStmt, elseStmt)
    
    # whileStmt: K_WHILE LP expr RP stmt;
    def visitWhileStmt(self, ctx):
        valExpr = self.visit(ctx.expr())
        bodyStmt = self.visit(ctx.stmt())
        return WhileStmt(valExpr, bodyStmt)
    
    # forStmt: K_FOR LP forFirst SEMI forCond SEMI forUpdate RP stmt;
    def visitForStmt(self, ctx):
        forFirst = self.visit(ctx.forFirst())
        condExpr = self.visit(ctx.forCond()) 
        updateExpr =  self.visit(ctx.forUpdate())
        bodyStmt = self.visit(ctx.stmt())
        return ForStmt(forFirst, condExpr, updateExpr, bodyStmt)
    
    # forCond: expr?;
    def visitForCond(self, ctx):
        if ctx.expr():
            return self.visit(ctx.expr())
        return None
        
    # forUpdate: expr?;
    def visitForUpdate(self, ctx):
        if ctx.expr():
            return self.visit(ctx.expr())
        return None

    # forFirst: forVarInit | forAssign | ;
    def visitForFirst(self, ctx):
        if ctx.getChildCount() == 0:
            return None
        elif ctx.forVarInit():
            return self.visit(ctx.forVarInit())
        elif ctx.forAssign():
            return ExprStmt(self.visit(ctx.forAssign()))
    
    # forVarInit: (typ| K_AUTO) ID (ASSIGN expr)?;
    def visitForVarInit(self, ctx):
        varType = self.visit(ctx.typ()) if ctx.typ() else None
        varName = ctx.ID().getText()
        initValue = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(varType, varName, initValue)
    
    # forAssign: logicOrExpr ASSIGN expr;
    def visitForAssign(self, ctx):
        lhs = self.visit(ctx.assignLHS())
        rhs = self.visit(ctx.expr())
        return AssignExpr(lhs, rhs)

    # switchStmt: K_SWITCH LP expr RP stmtSwitchBlock;
    def visitSwitchStmt(self, ctx):
        valExpr = self.visit(ctx.expr())
        cases, defaul_case = self.visit(ctx.stmtSwitchBlock())
        return SwitchStmt(valExpr, cases, defaul_case)
    # stmtSwitchBlock: LB caseList RB;
    def visitStmtSwitchBlock(self, ctx):
        return self.visit(ctx.caseList())
    
    # caseList: casePrime defaultCase?;
    def visitCaseList(self, ctx):
        cases = self.visit(ctx.casePrime())
        if ctx.defaultCase():
            return cases, self.visit(ctx.defaultCase())
        return cases, None
    
    # casePrime:  K_CASE expr COLON stmtList casePrime | ;
    def visitCasePrime(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        caseVal = self.visit(ctx.expr())
        caseStmts = self.visit(ctx.stmtList())
        followingCases = self.visit(ctx.casePrime())
        return [CaseStmt(caseVal, caseStmts)] + followingCases

    # defaultCase: K_DEFAULT COLON stmtList casePrime;
    def visitDefaultCase(self, ctx):
        return DefaultStmt(self.visit(ctx.stmtList()))
    
    # breakStmt: K_BREAK SEMI;
    def visitBreakStmt(self, ctx):
        return BreakStmt()
    
    # continueStmt: K_CONTINUE SEMI;
    def visitContinueStmt(self, ctx):
        return ContinueStmt()
    
    # returnStmt: K_RETURN expr? SEMI;
    def visitReturnStmt(self, ctx):
        returnValue = self.visit(ctx.expr()) if ctx.expr() else None
        return ReturnStmt(returnValue)
    
    # exprStmt: expr SEMI;
    def visitExprStmt(self, ctx):
        expr = self.visit(ctx.expr())
        return ExprStmt(expr)
    
    # 3. Expressions: expr -> logicOr -> ... -> unary/postfix/access/primary
    # expr: logicOrExpr ASSIGN expr | logicOrExpr;
    def visitExpr(self, ctx):
        if ctx.ASSIGN():
            lhs = self.visit(ctx.assignLHS())
            rhs = self.visit(ctx.expr())
            return AssignExpr(lhs, rhs)
        else:
            return self.visit(ctx.logicOrExpr())

    def visitAssignLHS(self, ctx):
        if ctx.ID():
            return Identifier(ctx.ID().getText())
        return self.visit(ctx.memberAccessExpr())
    
    # logicOrExpr: logicOrExpr OR logicAndExpr | logicAndExpr;
    def visitLogicOrExpr(self, ctx):
        if ctx.OR():
            left = self.visit(ctx.logicOrExpr())
            right = self.visit(ctx.logicAndExpr())
            return BinaryOp(left, '||', right)
        else:
            return self.visit(ctx.logicAndExpr())
    
    # logicAndExpr: logicAndExpr AND logicEqExpr | logicEqExpr;
    def visitLogicAndExpr(self, ctx):
        if ctx.AND():
            left = self.visit(ctx.logicAndExpr())
            right = self.visit(ctx.logicEqExpr())
            return BinaryOp(left, '&&', right)
        else:
            return self.visit(ctx.logicEqExpr())
    
    # logicEqExpr: logicEqExpr (EQ | NEQ) relExpr | relExpr;
    def visitLogicEqExpr(self, ctx):
        if ctx.EQ() or ctx.NEQ():
            left = self.visit(ctx.logicEqExpr())
            right = self.visit(ctx.relExpr())
            op = '==' if ctx.EQ() else '!='
            return BinaryOp(left, op, right)
        else:
            return self.visit(ctx.relExpr())
    
    # relExpr: relExpr (LT | LE | GT | GE) addExpr | addExpr;
    def visitRelExpr(self, ctx):
        if ctx.getChildCount() == 3:
            left = self.visit(ctx.relExpr())
            right = self.visit(ctx.addExpr())
            if ctx.LT():
                op = '<'
            elif ctx.LE():
                op = '<='
            elif ctx.GT():
                op = '>'
            else:
                op = '>='
            return BinaryOp(left, op, right)
        else:
            return self.visit(ctx.addExpr())
    # addExpr: addExpr (ADD | SUB) mulExpr | mulExpr;
    def visitAddExpr(self, ctx):
        if ctx.getChildCount() == 3:
            left = self.visit(ctx.addExpr())
            right = self.visit(ctx.mulExpr())
            op = '+' if ctx.ADD() else '-'
            return BinaryOp(left, op, right)
        else:
            return self.visit(ctx.mulExpr())
    
    # mulExpr: mulExpr (MUL | DIV | MOD) unaryExpr | unaryExpr;
    def visitMulExpr(self, ctx):
        if ctx.getChildCount() == 3:
            left = self.visit(ctx.mulExpr())
            right = self.visit(ctx.unaryExpr())
            if ctx.MUL():
                op = '*'
            elif ctx.DIV():
                op = '/'
            else:
                op = '%'
            return BinaryOp(left, op, right)
        else:
            return self.visit(ctx.unaryExpr())

    # unaryExpr: NOT unaryExpr | SUB unaryExpr | ADD unaryExpr | INC unaryExpr | DEC unaryExpr | postfixExpr;
    def visitUnaryExpr(self, ctx):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            operand = self.visit(ctx.unaryExpr())
            return PrefixOp(op, operand)
        else:
            return self.visit(ctx.postfixExpr())
    
    # postfixExpr: accessExpr (INC | DEC)?;
    def visitPostfixExpr(self, ctx):
        if ctx.getChildCount() == 2:
            operand = self.visit(ctx.accessExpr())
            op = ctx.getChild(1).getText()
            return PostfixOp(op, operand)
        else:
            return self.visit(ctx.accessExpr())

    def visitAccessExpr(self, ctx):
        if ctx.memberAccessExpr():
            return self.visit(ctx.memberAccessExpr())
        if ctx.callExpr():
            return self.visit(ctx.callExpr())
        return self.visit(ctx.primaryExpr())

    def visitMemberAccessExpr(self, ctx):
        obj = self.visit(ctx.memberBase())
        for token in ctx.ID():
            obj = MemberAccess(obj, token.getText())
        return obj

    def visitMemberBase(self, ctx):
        if ctx.callExpr():
            return self.visit(ctx.callExpr())
        return self.visit(ctx.primaryExpr())

    def visitCallExpr(self, ctx):
        args = self.visit(ctx.argList())
        return FuncCall(ctx.ID().getText(), args)
    
    # primaryExpr: ID | INT_LIT | FLOAT_LIT | STRING_LIT | LP expr RP | structInit;
    def visitPrimaryExpr(self, ctx):
        if ctx.ID():
            return Identifier(ctx.ID().getText())
        elif ctx.INT_LIT():
            return IntLiteral(int(ctx.INT_LIT().getText()))
        elif ctx.FLOAT_LIT():
            return FloatLiteral(float(ctx.FLOAT_LIT().getText()))
        elif ctx.STRING_LIT():
            return StringLiteral(ctx.STRING_LIT().getText()) 
        elif ctx.expr():
            return self.visit(ctx.expr())
        else:
            return self.visit(ctx.structInit())

    # structInit: LB argList RB;
    def visitStructInit(self, ctx):
        arguments = self.visit(ctx.argList())
        return StructLiteral(arguments)
    # argList: expr argListPrime | ;
    def visitArgList(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        expr = self.visit(ctx.expr())
        argListPrime = self.visit(ctx.argListPrime())
        return [expr] + argListPrime

    # argListPrime: COMMA expr argListPrime | ;
    def visitArgListPrime(self, ctx):
        if ctx.getChildCount() == 0:
            return []
        expr = self.visit(ctx.expr())
        argListPrime = self.visit(ctx.argListPrime())
        return [expr] + argListPrime
