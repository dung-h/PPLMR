import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASP_DIR = REPO_ROOT / "asp" / "database"
CASES_DIR = REPO_ROOT / "cases" / "db"
BASE_FILENAME = "database_serializability.lp"

BASE_RULES = textwrap.dedent(
    """
    % Facts
    {facts}

    #defined tx/1.
    #defined op/4.

    % op(Index, Transaction, Action, Item)
    % Action is typically r/w; we also support c (commit) for enhanced isolation analysis.
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

    % ---- Enhanced analysis (optional): recoverable / cascadeless / strict schedules ----
    % Only enabled when the input contains commit actions.
    has_commit :- op(_,_,c,_).

    commit_pos(T,I) :- has_commit, op(I,T,c,_).
    write_pos(T,X,I) :- has_commit, op(I,T,w,X).
    read_pos(T,X,I) :- has_commit, op(I,T,r,X).

    later_write_between(Iw,Ir,X) :- has_commit, idx(Iw), idx(Ir), write_pos(_,X,I2), Iw < I2, I2 < Ir.
    rf(Tr,Tw,X,Iw,Ir) :- has_commit, write_pos(Tw,X,Iw), read_pos(Tr,X,Ir), Tw != Tr, Iw < Ir, not later_write_between(Iw,Ir,X).

    % Recoverable: if Tr reads-from Tw and Tr commits, then Tw must commit before Tr.
    recoverable_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,_), commit_pos(Tr,_), not commit_pos(Tw,_).
    recoverable_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,_), commit_pos(Tr,Icr), commit_pos(Tw,Icw), Icr < Icw.
    recoverable :- has_commit, not recoverable_violation(_,_,_).
    not_recoverable :- has_commit, recoverable_violation(_,_,_).

    % Cascadeless: a read-from is allowed only after the writer commits.
    cascadeless_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,Ir), not commit_pos(Tw,_).
    cascadeless_violation(Tr,Tw,X) :- rf(Tr,Tw,X,_,Ir), commit_pos(Tw,Ic), Ic > Ir.
    cascadeless :- has_commit, not cascadeless_violation(_,_,_).
    not_cascadeless :- has_commit, cascadeless_violation(_,_,_).

    % Strict: after a write by Tw, no other tx may read/write the item until Tw commits.
    committed_between(Tw,Iw,I) :- has_commit, idx(Iw), idx(I), commit_pos(Tw,Ic), Iw < Ic, Ic < I.
    strict_violation(T,Tw,X) :- has_commit, write_pos(Tw,X,Iw), op(I,T,A,X), T != Tw, A != c, Iw < I, not committed_between(Tw,Iw,I).
    strict :- has_commit, not strict_violation(_,_,_).
    not_strict :- has_commit, strict_violation(_,_,_).

    #show edge/2.
    #show cycle/1.
    #show serializable/0.
    #show not_serializable/0.
    #show order/2.

    #show rf/5.
    #show recoverable/0.
    #show not_recoverable/0.
    #show recoverable_violation/3.
    #show cascadeless/0.
    #show not_cascadeless/0.
    #show cascadeless_violation/3.
    #show strict/0.
    #show not_strict/0.
    #show strict_violation/3.
    """
).lstrip()

CASES: list[dict[str, object]] = [
    {
        "name": "serializable_chain",
        "description": "Acyclic precedence graph with a straightforward serial order.",
        "facts": """
        tx(t1). tx(t2). tx(t3).
        op(1,t1,r,a).
        op(2,t2,w,a).
        op(3,t2,r,b).
        op(4,t3,w,b).
        """,
        "expect_in": ["serializable", "edge(t1,t2)", "edge(t2,t3)", "order("],
        "expect_out": ["not_serializable", "cycle("],
    },
    {
        "name": "serializable_branching",
        "description": "A four-transaction schedule with branching dependencies but no cycle.",
        "facts": """
        tx(t1). tx(t2). tx(t3). tx(t4).
        op(1,t1,w,a).
        op(2,t2,r,a).
        op(3,t1,w,b).
        op(4,t3,r,b).
        op(5,t2,w,c).
        op(6,t4,r,c).
        op(7,t3,w,d).
        op(8,t4,r,d).
        """,
        "expect_in": ["serializable", "edge(t1,t2)", "edge(t1,t3)", "edge(t2,t4)", "edge(t3,t4)", "order("],
        "expect_out": ["not_serializable", "cycle("],
    },
    {
        "name": "non_serializable_cycle",
        "description": "Two transactions create a direct cycle in the precedence graph.",
        "facts": """
        tx(t1). tx(t2).
        op(1,t1,w,a).
        op(2,t2,r,a).
        op(3,t2,w,b).
        op(4,t1,r,b).
        """,
        "expect_in": ["not_serializable", "edge(t1,t2)", "edge(t2,t1)", "cycle(t1)"],
        "expect_out": ["serializable", "order("],
    },
    {
        "name": "non_serializable_three_way",
        "description": "A three-transaction schedule produces a longer dependency cycle.",
        "facts": """
        tx(t1). tx(t2). tx(t3).
        op(1,t1,w,a).
        op(2,t2,r,a).
        op(3,t2,w,b).
        op(4,t3,r,b).
        op(5,t3,w,c).
        op(6,t1,r,c).
        """,
        "expect_in": ["not_serializable", "edge(t1,t2)", "edge(t2,t3)", "edge(t3,t1)", "cycle(t1)"],
        "expect_out": ["serializable", "order("],
    },

    {
        "name": "recoverable_violation",
        "description": "Serializable schedule but not recoverable/cascadeless due to early commit after dirty read.",
        "facts": """
        tx(t1). tx(t2).
        op(1,t1,w,a).
        op(2,t2,r,a).
        op(3,t2,c,none).
        op(4,t1,c,none).
        """,
        "expect_in": [
            "serializable",
            "edge(t1,t2)",
            "rf(t2,t1,a,1,2)",
            "not_recoverable",
            "not_cascadeless",
        ],
        "expect_out": ["recoverable", "cascadeless"],
    },

    {
        "name": "strict_violation",
        "description": "Two writers overlap on the same item before the first commit => not strict.",
        "facts": """
        tx(t1). tx(t2).
        op(1,t1,w,a).
        op(2,t2,w,a).
        op(3,t2,c,none).
        op(4,t1,c,none).
        """,
        "expect_in": [
            "serializable",
            "edge(t1,t2)",
            "not_strict",
            "strict_violation(t2,t1,a)",
        ],
        "expect_out": ["strict", "not_recoverable", "not_cascadeless"],
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


def has_token(atoms: set[str], token: str) -> bool:
    if token.endswith("("):
        return any(atom.startswith(token) for atom in atoms)
    return token in atoms


def check_expectations(atoms: set[str], expect_in: list[str], expect_out: list[str]) -> list[str]:
    issues: list[str] = []
    for token in expect_in:
        if not has_token(atoms, token):
            issues.append(f"Missing expected atom: {token}")
    for token in expect_out:
        if has_token(atoms, token):
            issues.append(f"Unexpected atom present: {token}")
    return issues


def analyze_case(case: dict[str, object], output: str) -> bool:
    models = parse_models(output)
    if not models:
        print("No stable model produced.")
        return False

    atoms = set(models[0].split())
    print("Stable Model:")
    print(models[0])

    issues = check_expectations(
        atoms,
        list(case.get("expect_in", [])),
        list(case.get("expect_out", [])),
    )
    if issues:
        print("Expectation check: FAIL")
        for issue in issues:
            print(f"- {issue}")
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

        asp_path = ASP_DIR / BASE_FILENAME if name == "serializable_chain" else CASES_DIR / f"{name}.lp"
        write_case(asp_path, facts)

        print(f"\n=== DB Case: {name} ===")
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
