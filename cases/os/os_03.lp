% Case 03: unsafe_after_partial_progress
% Purpose: One process can finish first, but the state still remains globally unsafe.
% Expected: Safe execution sequence found (SAT) or no sequence exists (UNSAT).
% Run: clingo os_03.lp 1
%
% Facts
proc(p1). proc(p2). proc(p3).
res(a). res(b).

alloc(p1,a,1). alloc(p1,b,0).
alloc(p2,a,0). alloc(p2,b,1).
alloc(p3,a,1). alloc(p3,b,0).

max(p1,a,1). max(p1,b,0).
max(p2,a,2). max(p2,b,1).
max(p3,a,1). max(p3,b,2).

avail0(a,0). avail0(b,1).

#defined proc/1.
#defined res/1.
#defined alloc/3.
#defined max/3.
#defined avail0/2.

need(P,R,N) :- max(P,R,M), alloc(P,R,A), N = M - A.

pcount(N) :- N = #count { P : proc(P) }.
step(1..N) :- pcount(N).

% Guess one process per step and force each process to appear exactly once.
1 { run(S,P) : proc(P) } 1 :- step(S).
1 { run(S,P) : step(S) } 1 :- proc(P).

finished_before(S,P) :- step(S), run(S0,P), S0 < S.
returned(S,R,Ret) :- step(S), res(R), Ret = #sum { A,P : alloc(P,R,A), finished_before(S,P) }.
available(S,R,V) :- step(S), res(R), avail0(R,B), returned(S,R,Ret), V = B + Ret.

% A process can run at step S only if all remaining needs are available.
:- run(S,P), need(P,R,N), available(S,R,V), N > V.

% Diagnostics: if the state is UNSAT, these atoms help explain the immediate blockers.
% can_run_now(P) means P could run as the *first* process given avail0.
can_run_now(P) :- proc(P), not lacks_resource_now(P,_).
lacks_resource_now(P,R) :- proc(P), res(R), need(P,R,N), avail0(R,V0), N > V0.
blocked_initial(P) :- proc(P), not can_run_now(P).

#show need/3.
#show available/3.
#show run/2.
#show can_run_now/1.
#show blocked_initial/1.
#show lacks_resource_now/2.
