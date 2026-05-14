% Case 02: untyped
% Purpose: Declared variable without a type is not bound.
% Expected: Binding and resolution predicates computed correctly.
% Run: clingo ppl_02.lp 1
%
% Facts
variable(u).
declared_in(u, foo).
function_scope(foo, f1).

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
