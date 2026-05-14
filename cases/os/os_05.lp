% OS Banker: Immediate Deadlock
% All processes need more than available at step 0
% No process can run even as the first one
% Expected: UNSATISFIABLE

proc(p1). proc(p2).
res(cpu).

alloc(p1,cpu,0).
alloc(p2,cpu,0).

max(p1,cpu,2).
max(p2,cpu,2).

avail0(cpu,1).

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

#show blocked_initial/1.
#show lacks_resource_now/2.
