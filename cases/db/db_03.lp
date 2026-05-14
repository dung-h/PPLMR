% Case 03: non_serializable_three_way
% Purpose: A three-transaction schedule produces a longer dependency cycle.
% Expected: Produces stable model(s) with serialization/isolation properties.
% Run: clingo db_03.lp 1
%
% Facts
tx(t1). tx(t2). tx(t3).
op(1,t1,w,a).
op(2,t2,r,a).
op(3,t2,w,b).
op(4,t3,r,b).
op(5,t3,w,c).
op(6,t1,r,c).

#defined tx/1.
#defined op/4.

% op(Index, Transaction, Action, Item)
% Action is typically r/w; we also support c (commit) for enhanced isolation analysis.
idx(I) :- op(I,_,_,_).
conflict(I,J,T1,T2,X) :- op(I,T1,w,X), op(J,T2,_,X), T1 != T2, I < J.
conflict(I,J,T1,T2,X) :- op(I,T1,_,X), op(J,T2,w,X), T1 != T2, I < J.
edge(T1,T2) :- conflict(_,_,T1,T2,_).

path(T1,T2) :- edge(T1,T2).
path(T1,T3) :- path(T1,T2), edge(T2,T3).
cycle(T) :- path(T,T).

serializable :- not cycle(_).
not_serializable :- cycle(_).

tcount(N) :- N = #count { T : tx(T) }.
pos(1..N) :- tcount(N).

1 { order(T,P) : pos(P) } 1 :- tx(T), serializable.
1 { order(T,P) : tx(T) } 1 :- pos(P), serializable.
:- serializable, edge(T1,T2), order(T1,P1), order(T2,P2), P1 >= P2.

% ---- Enhanced analysis (optional): recoverable / cascadeless / strict schedules ----
% Only enabled when the input contains commit actions.
has_commit :- op(_,_,c,_).

commit_pos(T,I) :- has_commit, op(I,T,c,_).
write_pos(T,X,I) :- has_commit, op(I,T,w,X).
read_pos(T,X,I) :- has_commit, op(I,T,r,X).

later_write_between(Iw,Ir,X) :- has_commit, idx(Iw), idx(Ir), write_pos(_,X,I2), Iw < I2, I2 < Ir.
rf(Tr,Tw,X,Iw,Ir) :- has_commit, write_pos(Tw,X,Iw), read_pos(Tr,X,Ir), Tw != Tr, Iw < Ir, not later_write_between(Iw,Ir,X).

% Recoverable: if Tr reads-from Tw and Tr commits, then Tw must commit before Tr.
recoverable_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,_), commit_pos(Tr,_), not commit_pos(Tw,_).
recoverable_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,_), commit_pos(Tr,Icr), commit_pos(Tw,Icw), Icr < Icw.
recoverable :- has_commit, not recoverable_violation(_,_,_).
not_recoverable :- has_commit, recoverable_violation(_,_,_).

% Cascadeless: a read-from is allowed only after the writer commits.
cascadeless_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,Ir), not commit_pos(Tw,_).
cascadeless_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,Ir), commit_pos(Tw,Ic), Ic > Ir.
cascadeless :- has_commit, not cascadeless_violation(_,_,_).
not_cascadeless :- has_commit, cascadeless_violation(_,_,_).

% Strict: after a write by Tw, no other tx may read/write the item until Tw commits.
committed_between(Tw,Iw,I) :- has_commit, idx(Iw), idx(I), commit_pos(Tw,Ic), Iw < Ic, Ic < I.
strict_violation(T,Tw,X) :- has_commit, write_pos(Tw,X,Iw), op(I,T,A,X), T != Tw, A != c, Iw < I, not committed_between(Tw,Iw,I).
strict :- has_commit, not strict_violation(_,_,_).
not_strict :- has_commit, strict_violation(_,_,_).

#show edge/2.
#show cycle/1.
#show serializable/0.
#show not_serializable/0.
#show order/2.

#show rf/5.
#show recoverable/0.
#show not_recoverable/0.
#show recoverable_violation/3.
#show cascadeless/0.
#show not_cascadeless/0.
#show cascadeless_violation/3.
#show strict/0.
#show not_strict/0.
#show strict_violation/3.
