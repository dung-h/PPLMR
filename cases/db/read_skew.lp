% Read Skew Anomaly
% T1: R(X)=0, R(Y)=0 (expects X+Y=0)
% T2: W(X)=100, W(Y)=100, Commit
% T1: Reads inconsistent state: X'=100 but still sees Y=0 (or vice versa)
% 
% From conflict-serializability: T1 reads both X and Y before T2 writes,
% so conflict edges should force T1 before T2, or T2 before T1 completely.
% If both reads happen before any write, but then partial reads of updated data,
% schedule can be acyclic but still NOT serializable in VIEW sense.

% Facts
tx(t1). tx(t2).
op(1,t1,r,x).
op(2,t1,r,y).
op(3,t2,w,x).
op(4,t2,w,y).
op(5,t2,c,none).
op(6,t1,c,none).

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
#show order/2.
