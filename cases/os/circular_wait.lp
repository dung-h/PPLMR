% OS Banker: Circular Wait / Resource Starvation
% 4 processes, 2 resources
% P1 wants (R1, R2), P2 wants (R2, R1) - circular pattern
% Careful allocation may avoid this, but tests resource interlock scenario

proc(p1). proc(p2). proc(p3). proc(p4).
res(r1). res(r2).

alloc(p1,r1,1). alloc(p1,r2,0).
alloc(p2,r1,0). alloc(p2,r2,1).
alloc(p3,r1,0). alloc(p3,r2,0).
alloc(p4,r1,0). alloc(p4,r2,0).

max(p1,r1,2). max(p1,r2,2).
max(p2,r1,2). max(p2,r2,2).
max(p3,r1,1). max(p3,r2,1).
max(p4,r1,1). max(p4,r2,1).

avail0(r1,1). avail0(r2,1).

#defined proc/1.
#defined res/1.
#defined alloc/3.
#defined max/3.
#defined avail0/2.

need(P,R,N) :- max(P,R,M), alloc(P,R,A), N = M - A.

pcount(N) :- N = #count { P : proc(P) }.
step(1..N) :- pcount(N).

1 { run(S,P) : proc(P) } 1 :- step(S).
1 { run(S,P) : step(S) } 1 :- proc(P).

finished_before(S,P) :- step(S), run(S0,P), S0 < S.
returned(S,R,Ret) :- step(S), res(R), Ret = #sum { A,P : alloc(P,R,A), finished_before(S,P) }.
available(S,R,V) :- step(S), res(R), avail0(R,B), returned(S,R,Ret), V = B + Ret.

:- run(S,P), need(P,R,N), available(S,R,V), N > V.

can_run_now(P) :- proc(P), not lacks_resource_now(P,_).
lacks_resource_now(P,R) :- proc(P), res(R), need(P,R,N), avail0(R,V0), N > V0.
blocked_initial(P) :- proc(P), not can_run_now(P).

#show need/3.
#show available/3.
#show run/2.
#show can_run_now/1.
