% OS Banker: Resource Hoarding (two processes compete tightly)
% 2 processes, 1 resource
% Both need the full resource but already allocated some
% Very tight margin - only one valid execution order

proc(p1). proc(p2).
res(mem).

alloc(p1,mem,3).
alloc(p2,mem,3).

max(p1,mem,5).
max(p2,mem,5).

avail0(mem,4).

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

% Diagnostic: show which process(es) must run first
must_run_first(P) :- can_run_now(P), not can_run_now(P2), P != P2.

#show need/3.
#show run/2.
#show can_run_now/1.
#show must_run_first/1.
