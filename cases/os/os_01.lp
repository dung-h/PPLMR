% Case 01: safe_state_classic
% Purpose: A larger textbook-style instance with five processes and three resources.
% Expected: Safe execution sequence found (SAT) or no sequence exists (UNSAT).
% Run: clingo os_01.lp 1
%
% Facts
proc(p0). proc(p1). proc(p2). proc(p3). proc(p4).
res(a). res(b). res(c).

alloc(p0,a,0). alloc(p0,b,1). alloc(p0,c,0).
alloc(p1,a,2). alloc(p1,b,0). alloc(p1,c,0).
alloc(p2,a,3). alloc(p2,b,0). alloc(p2,c,2).
alloc(p3,a,2). alloc(p3,b,1). alloc(p3,c,1).
alloc(p4,a,0). alloc(p4,b,0). alloc(p4,c,2).

max(p0,a,7). max(p0,b,5). max(p0,c,3).
max(p1,a,3). max(p1,b,2). max(p1,c,2).
max(p2,a,9). max(p2,b,0). max(p2,c,2).
max(p3,a,2). max(p3,b,2). max(p3,c,2).
max(p4,a,4). max(p4,b,3). max(p4,c,3).

avail0(a,3). avail0(b,3). avail0(c,2).

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
