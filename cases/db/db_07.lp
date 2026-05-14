% Lost Update Anomaly
% T1: R(X)=10, Compute X+5, W(X)=15, Commit
% T2: R(X)=10, Compute X*2, W(X)=20, Commit
% Result: T1's update is lost; final X=20 instead of either 15 or 20 serially
% This schedule is NOT conflict-serializable due to the write-write conflict.

% Facts
tx(t1). tx(t2).
op(1,t1,r,x).
op(2,t2,r,x).
op(3,t1,w,x).
op(4,t2,w,x).
op(5,t1,c,none).
op(6,t2,c,none).

#defined tx/1.
#defined op/4.

% op(Index, Transaction, Action, Item)
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

% Commit-based isolation analysis
has_commit :- op(_,_,c,_).
commit_pos(T,I) :- has_commit, op(I,T,c,_).
write_pos(T,X,I) :- has_commit, op(I,T,w,X).
read_pos(T,X,I) :- has_commit, op(I,T,r,X).

later_write_between(Iw,Ir,X) :- has_commit, idx(Iw), idx(Ir), write_pos(_,X,I2), Iw < I2, I2 < Ir.
rf(Tr,Tw,X,Iw,Ir) :- has_commit, write_pos(Tw,X,Iw), read_pos(Tr,X,Ir), Tw != Tr, Iw < Ir, not later_write_between(Iw,Ir,X).

#show not_serializable/0.
#show edge/2.
#show cycle/1.
