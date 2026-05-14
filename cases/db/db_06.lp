% Dirty Write / Intermediate Write Conflict
% T1: W(X)=100
% T2: W(X)=200 (overwrites T1's uncommitted write)
% T1: Commit
% T2: Abort
% Result: If T2 was supposed to be second but aborted, T1's write is final.
% But this schedule has write-write conflict in immediate succession.

% Facts
tx(t1). tx(t2).
op(1,t1,w,x).
op(2,t2,w,x).
op(3,t1,c,none).
op(4,t2,a,none).

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
#show not_serializable/0.
#show edge/2.
#show cycle/1.
