# Generated from C:/Users/HAD/Desktop/Assignment1_PPL/tyc-compiler/src/grammar/TyC.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .TyCParser import TyCParser
else:
    from TyCParser import TyCParser

# This class defines a complete generic visitor for a parse tree produced by TyCParser.

class TyCVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by TyCParser#program.
    def visitProgram(self, ctx:TyCParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#declList.
    def visitDeclList(self, ctx:TyCParser.DeclListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#decl.
    def visitDecl(self, ctx:TyCParser.DeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#structDecl.
    def visitStructDecl(self, ctx:TyCParser.StructDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#memberList.
    def visitMemberList(self, ctx:TyCParser.MemberListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#member.
    def visitMember(self, ctx:TyCParser.MemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#typ.
    def visitTyp(self, ctx:TyCParser.TypContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#funcDecl.
    def visitFuncDecl(self, ctx:TyCParser.FuncDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#paramList.
    def visitParamList(self, ctx:TyCParser.ParamListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#paramPrime.
    def visitParamPrime(self, ctx:TyCParser.ParamPrimeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#param.
    def visitParam(self, ctx:TyCParser.ParamContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#stmtBlock.
    def visitStmtBlock(self, ctx:TyCParser.StmtBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#stmtList.
    def visitStmtList(self, ctx:TyCParser.StmtListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#stmt.
    def visitStmt(self, ctx:TyCParser.StmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#varDeclStmt.
    def visitVarDeclStmt(self, ctx:TyCParser.VarDeclStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#ifStmt.
    def visitIfStmt(self, ctx:TyCParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#whileStmt.
    def visitWhileStmt(self, ctx:TyCParser.WhileStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forStmt.
    def visitForStmt(self, ctx:TyCParser.ForStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forCond.
    def visitForCond(self, ctx:TyCParser.ForCondContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forUpdate.
    def visitForUpdate(self, ctx:TyCParser.ForUpdateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forFirst.
    def visitForFirst(self, ctx:TyCParser.ForFirstContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forVarInit.
    def visitForVarInit(self, ctx:TyCParser.ForVarInitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#forAssign.
    def visitForAssign(self, ctx:TyCParser.ForAssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#switchStmt.
    def visitSwitchStmt(self, ctx:TyCParser.SwitchStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#stmtSwitchBlock.
    def visitStmtSwitchBlock(self, ctx:TyCParser.StmtSwitchBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#caseList.
    def visitCaseList(self, ctx:TyCParser.CaseListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#casePrime.
    def visitCasePrime(self, ctx:TyCParser.CasePrimeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#defaultCase.
    def visitDefaultCase(self, ctx:TyCParser.DefaultCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#breakStmt.
    def visitBreakStmt(self, ctx:TyCParser.BreakStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#continueStmt.
    def visitContinueStmt(self, ctx:TyCParser.ContinueStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#returnStmt.
    def visitReturnStmt(self, ctx:TyCParser.ReturnStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#exprStmt.
    def visitExprStmt(self, ctx:TyCParser.ExprStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#expr.
    def visitExpr(self, ctx:TyCParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#assignLHS.
    def visitAssignLHS(self, ctx:TyCParser.AssignLHSContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#logicOrExpr.
    def visitLogicOrExpr(self, ctx:TyCParser.LogicOrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#logicAndExpr.
    def visitLogicAndExpr(self, ctx:TyCParser.LogicAndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#logicEqExpr.
    def visitLogicEqExpr(self, ctx:TyCParser.LogicEqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#relExpr.
    def visitRelExpr(self, ctx:TyCParser.RelExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#addExpr.
    def visitAddExpr(self, ctx:TyCParser.AddExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#mulExpr.
    def visitMulExpr(self, ctx:TyCParser.MulExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#unaryExpr.
    def visitUnaryExpr(self, ctx:TyCParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#postfixExpr.
    def visitPostfixExpr(self, ctx:TyCParser.PostfixExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#accessExpr.
    def visitAccessExpr(self, ctx:TyCParser.AccessExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#memberAccessExpr.
    def visitMemberAccessExpr(self, ctx:TyCParser.MemberAccessExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#memberBase.
    def visitMemberBase(self, ctx:TyCParser.MemberBaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#callExpr.
    def visitCallExpr(self, ctx:TyCParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#primaryExpr.
    def visitPrimaryExpr(self, ctx:TyCParser.PrimaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#structInit.
    def visitStructInit(self, ctx:TyCParser.StructInitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#argList.
    def visitArgList(self, ctx:TyCParser.ArgListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by TyCParser#argListPrime.
    def visitArgListPrime(self, ctx:TyCParser.ArgListPrimeContext):
        return self.visitChildren(ctx)



del TyCParser