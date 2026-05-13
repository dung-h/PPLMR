% Facts
scope_parent(s0,global).
function_scope("foo",s0).
variable("x").
declared_in_scope("x",s0).
scope_parent(s1,s0).
variable("y").
declared_in_scope("y",s1).
variable("x").
use_in("x",s1).
variable("y").
use_in("y",s1).
variable("z").
declared_in_scope("z",s1).
scope_parent(s2,s1).
variable("x").
use_in("x",s2).
variable("y").
declared_in_scope("y",s2).
variable("x").
variable("x").
variable("y").
use_in("y",s2).
type_of("y",int).
variable("x").
type_of("z",int).
type_of("x",int).

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
