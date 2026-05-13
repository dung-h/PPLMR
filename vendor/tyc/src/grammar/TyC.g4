grammar TyC;

@lexer::header {
from lexererr import *
}

@lexer::members {
def emit(self):
    tk = self.type
    if tk == self.UNCLOSE_STRING:       
        result = super().emit();
        raise UncloseString(result.text);
    elif tk == self.ILLEGAL_ESCAPE:
        result = super().emit();
        raise IllegalEscape(result.text);
    elif tk == self.ERROR_CHAR:
        result = super().emit();
        raise ErrorToken(result.text); 
    else:
        return super().emit();
}

options{
	language=Python3;
}

// TODO: Define grammar rules here
// Parser here
// Should I put void main as a normal function? or a seperate terminal token
// a sequence of structs and functions ? Nullable or not?
program: declList EOF;
declList: decl declList | ;
decl: structDecl | funcDecl;

// Struct Declaration. Struct can have no members. Nullable
structDecl: K_STRUCT ID LB memberList RB SEMI;
memberList: member memberList | ;
member: typ ID SEMI;
typ: K_INT | K_FLOAT | K_STRING | ID;

// Function Declaration. Return type is optional. If not specified, it is void.
// Function type is optional. paramList is optional.
// Param cannot be auto. paramList is comma separated.
// Test: int add(auto b){} is not valid. auto main() is valid or not ????
funcDecl: (typ | K_VOID)? ID LP paramList RP stmtBlock;
paramList: param paramPrime | ;
paramPrime: COMMA param paramPrime | ;
param: typ ID;

// Block Statement Defintion. Can be nullable
stmtBlock: LB stmtList RB;
stmtList: stmt stmtList | ;
// a semicolon (;) by itself does not constitute a valid statement
stmt: varDeclStmt | stmtBlock | exprStmt | ifStmt | whileStmt | forStmt | switchStmt | returnStmt | breakStmt | continueStmt;

// Variable Declaration Statement
// TODO Does it accept auto x, y, z; ? listID
// !!! Important found, var type declaration can be None. None means auto. Reference nodes.py
varDeclStmt: (typ| K_AUTO) ID (ASSIGN expr)? SEMI;

// If Statement
ifStmt: K_IF LP expr RP stmt (K_ELSE stmt)?;

// While Statement
whileStmt: K_WHILE LP expr RP stmt;

// For Statement
forStmt: K_FOR LP forFirst SEMI forCond SEMI forUpdate RP stmt;
forCond: expr?;
forUpdate: expr?;

forFirst: forVarInit | forAssign | ;
forVarInit: (typ | K_AUTO) ID (ASSIGN expr)?;
forAssign: assignLHS ASSIGN expr;

// Switch Statement. Atmost one default case. 
switchStmt: K_SWITCH LP expr RP stmtSwitchBlock;
stmtSwitchBlock: LB caseList RB;
caseList: casePrime defaultCase?;
casePrime: K_CASE expr COLON stmtList casePrime | ;
defaultCase: K_DEFAULT COLON stmtList;

// Break Statement
breakStmt: K_BREAK SEMI;

// Continue Statement
continueStmt: K_CONTINUE SEMI;

// Return Statement. Can be void
returnStmt: K_RETURN expr? SEMI;

// Expression Statement
exprStmt: expr SEMI;

// Expression
// Expression statements are used for their side effects 
// (such as function calls, assignments, or increment/decrement operations).
// Test: x = a = 5 + 6;
// Assignment Right Associative
expr: assignLHS ASSIGN expr | logicOrExpr;
assignLHS: ID | memberAccessExpr;

// Logical OR expression. Left Associative
logicOrExpr: logicOrExpr OR logicAndExpr | logicAndExpr;

// Logical AND expression. Left Associative
logicAndExpr: logicAndExpr AND logicEqExpr | logicEqExpr;
 
// Equality Expression. Left Associative
logicEqExpr: logicEqExpr (EQ | NEQ) relExpr | relExpr;

// Relational Expression. Left Associative
relExpr: relExpr (LT | LE | GT | GE) addExpr | addExpr;

// Additive Expression. Left Associative
addExpr: addExpr (ADD | SUB) mulExpr | mulExpr;

// Multiplicative Expression. Left Associative
mulExpr: mulExpr (MUL | DIV | MOD) unaryExpr | unaryExpr;

// Unary Expression. Right Associative
unaryExpr: NOT unaryExpr | SUB unaryExpr | ADD unaryExpr | INC unaryExpr | DEC unaryExpr | postfixExpr;

// Postfix Expression. Function Call
postfixExpr: accessExpr (INC | DEC)?;
accessExpr: memberAccessExpr | callExpr | primaryExpr;
memberAccessExpr: memberBase (DOT ID)+;
memberBase: callExpr | primaryExpr;
callExpr: ID LP argList RP;

primaryExpr: ID | INT_LIT | FLOAT_LIT | STRING_LIT | LP expr RP | structInit;
structInit: LB argList RB;



argList: expr argListPrime | ;
argListPrime: COMMA expr argListPrime | ;


// Lexer part
// 1. Keywords
// auto, break, case, continue, default, else, float, for, if, int, return, string, struct, switch, void, while.
K_AUTO: 'auto';
K_BREAK: 'break';
K_CASE: 'case';
K_CONTINUE: 'continue';
K_DEFAULT: 'default';
K_ELSE: 'else';
K_FLOAT: 'float';
K_FOR: 'for';
K_IF: 'if';
K_INT: 'int';
K_RETURN: 'return';
K_STRING: 'string';
K_STRUCT: 'struct';
K_SWITCH: 'switch';
K_VOID: 'void';
K_WHILE: 'while';

// 2. Operators
// 2.1 Math Operators +, -, *, /, %
ADD: '+';
SUB: '-';
MUL: '*';
DIV: '/';
MOD: '%';

// 2.2 Relational Operators ==, !=, <, <=, >, >=
EQ: '==';
NEQ: '!=';
LT: '<';
LE: '<=';
GT: '>'; 
GE: '>=';

// 2.3 Logical Operators &&, ||, !
AND: '&&';
OR: '||';
NOT: '!';

// 2.4 Increment & Decrement
INC: '++';
DEC: '--';

// 2.5 Assignment Operators =
ASSIGN: '=';

// 2.7: Dot operator .
DOT: '.';

// 3. Separators (, ), {, }, ;, , , :
LP: '(';
RP: ')';
LB: '{';
RB: '}';
SEMI: ';';
COMMA: ',';
COLON: ':';

// 4. Literals
fragment Letter: [a-zA-Z_];
fragment Digit: [0-9];
ID: Letter (Letter | Digit)*;
INT_LIT: '0' | [1-9] Digit*;

// 2 cases of float literal. Float does not accept negative sign. Exponent part must be Digit only, not Float
// Test: 1e0, 1.0e0, 1.0e+0, 1.0e-0, -.4, -.4e3, 0e0 valid.
FLOAT_LIT: ((Digit+ '.' Digit* | Digit* '.' Digit+) ([Ee] [+-]? Digit+)? ) | Digit+ [Ee] [+-]? Digit+ ;

// STRING Literals
fragment ESC: '\\' [bfrnt"\\]; 
STRING_LIT: '"' (ESC | ~["\\\r\n])* '"' {self.text = self.text[1:-1];};

// 5. Comments
LINE_COMMENT: '//' ~[\r\n]* -> skip;
BLOCK_COMMENT: '/*' .*? '*/' -> skip;
WS : [ \t\r\n\f]+ -> skip ; // skip spaces, tabs

// 6. Error Handling
ILLEGAL_ESCAPE: '"' (ESC | ~["\\\r\n])* '\\' ~[bfrnt"\\] {self.text = self.text[1:]};
UNCLOSE_STRING: '"' (ESC | ~["\\\r\n])* ([\r\n] | EOF) {
    if self.text[-1] == '\r' or self.text[-1] == '\n':
        self.text = self.text[1:-1]
    else:
        self.text = self.text[1:]

};
ERROR_CHAR: .;
