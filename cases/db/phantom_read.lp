% Phantom Read (Conflict-based perspective)
% T1: R(X), Compute aggregate
% T2: Insert Y (or delete Z) with same key range
% T1: R(X) again, sees different result
% From conflict-serialization view: both read same item X but not conflicting directly
% However, the logical anomaly comes from "range predicate" level

% Facts - simplified: treating predicate anomaly as conflict on a special item
tx(t1). tx(t2). tx(t3).
op(1,t1,r,data).
op(2,t2,r,data).
op(3,t2,w,phantom).  % T2 inserts/deletes in same range
op(4,t3,r,data).
op(5,t3,w,result).

#defined tx/1.
#defined op/4.

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

#show serializable/0.
#show edge/2.
