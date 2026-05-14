import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASP_DIR = REPO_ROOT / "asp" / "os"
CASES_DIR = REPO_ROOT / "cases" / "os"
BASE_FILENAME = "os_banker.lp"

BASE_RULES = textwrap.dedent(
    """
    % Facts
    {facts}

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
    """
).lstrip()

CASES: list[dict[str, object]] = [
    {
        "name": "safe_state",
        "description": "At least one safe execution sequence exists.",
        "facts": """
        proc(p1). proc(p2). proc(p3).
        res(cpu). res(io).

        alloc(p1,cpu,1). alloc(p1,io,0).
        alloc(p2,cpu,0). alloc(p2,io,1).
        alloc(p3,cpu,1). alloc(p3,io,1).

        max(p1,cpu,2). max(p1,io,1).
        max(p2,cpu,1). max(p2,io,2).
        max(p3,cpu,1). max(p3,io,1).

        avail0(cpu,1). avail0(io,1).
        """,
        "expect_model": True,
        "expect_in": ["run(", "need(p3,cpu,0)", "need(p3,io,0)"],
    },
    {
        "name": "safe_state_classic",
        "description": "A larger textbook-style instance with five processes and three resources.",
        "facts": """
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
        """,
        "expect_model": True,
        "expect_in": ["run(", "need(p1,a,1)", "need(p1,b,2)", "need(p3,a,0)", "need(p3,b,1)", "need(p3,c,1)"],
    },
    {
        "name": "unsafe_state",
        "description": "No safe sequence exists, so the program is UNSAT.",
        "facts": """
        proc(p1). proc(p2).
        res(cpu). res(io).

        alloc(p1,cpu,1). alloc(p1,io,0).
        alloc(p2,cpu,0). alloc(p2,io,1).

        max(p1,cpu,2). max(p1,io,1).
        max(p2,cpu,1). max(p2,io,2).

        avail0(cpu,0). avail0(io,0).
        """,
        "expect_model": False,
    },
    {
        "name": "unsafe_after_partial_progress",
        "description": "One process can finish first, but the state still remains globally unsafe.",
        "facts": """
        proc(p1). proc(p2). proc(p3).
        res(a). res(b).

        alloc(p1,a,1). alloc(p1,b,0).
        alloc(p2,a,0). alloc(p2,b,1).
        alloc(p3,a,1). alloc(p3,b,0).

        max(p1,a,1). max(p1,b,0).
        max(p2,a,2). max(p2,b,1).
        max(p3,a,1). max(p3,b,2).

        avail0(a,0). avail0(b,1).
        """,
        "expect_model": False,
    },
]


def write_case(path: Path, facts: str) -> None:
    code = BASE_RULES.replace("{facts}", facts.strip())
    path.write_text(code, encoding="utf-8")


def run_clingo(path: Path) -> tuple[str, str, int, list[str]]:
    cmd = ["clingo", str(path), "1"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        cmd = [sys.executable, "-m", "clingo", str(path), "1"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout, result.stderr, result.returncode, cmd


def parse_models(output: str) -> list[str]:
    lines = output.splitlines()
    models: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("Answer:"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                models.append(lines[j].strip())
                i = j
        i += 1
    return models


def analyze_case(case: dict[str, object], output: str) -> bool:
    expect_model = bool(case.get("expect_model", True))
    models = parse_models(output)
    has_model = len(models) > 0

    if expect_model and not has_model:
        print("Expectation check: FAIL")
        print("- Expected a stable model but none was produced.")
        return False

    if (not expect_model) and has_model:
        print("Expectation check: FAIL")
        print("- Expected UNSAT but a model was produced.")
        print(f"- Model: {models[0]}")
        return False

    if not expect_model:
        if "UNSATISFIABLE" in output:
            print("Expectation check: PASS")
            return True
        print("Expectation check: FAIL")
        print("- Expected UNSATISFIABLE marker not found.")
        return False

    atoms = set(models[0].split())
    print("Stable Model:")
    print(models[0])
    for token in list(case.get("expect_in", [])):
        if token.endswith("("):
            if not any(atom.startswith(token) for atom in atoms):
                print("Expectation check: FAIL")
                print(f"- Missing expected atom prefix: {token}")
                return False
        elif token not in atoms:
            print("Expectation check: FAIL")
            print(f"- Missing expected atom: {token}")
            return False

    print("Expectation check: PASS")
    return True


def main() -> None:
    ASP_DIR.mkdir(parents=True, exist_ok=True)
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    passed = 0
    for case in CASES:
        name = str(case["name"])
        description = str(case["description"])
        facts = textwrap.dedent(str(case["facts"]))

        asp_path = ASP_DIR / BASE_FILENAME if name == "safe_state" else CASES_DIR / f"{name}.lp"
        write_case(asp_path, facts)

        print(f"\n=== OS Case: {name} ===")
        print(description)
        print(f"ASP file: {asp_path}")

        stdout, stderr, code, cmd = run_clingo(asp_path)
        print(f"Clingo command: {' '.join(cmd)}")
        if stderr:
            print("Clingo stderr:")
            print(stderr)
        print("Clingo output:")
        print(stdout)

        ok = analyze_case(case, stdout)
        if ok:
            passed += 1
        if code != 0:
            print(f"Clingo exited with code {code}")

    total = len(CASES)
    print(f"\nSummary: {passed}/{total} cases passed.")


if __name__ == "__main__":
    main()
