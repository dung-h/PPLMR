# ASP Applications for 3 Subjects

## 1) PPL: Scope and Binding Analysis
- File: `scripts/scope_binding.py`
- Output predicates: `local_variable/2`, `global_variable/1`, `in_scope/2`, `bound_variable/2`
- Covers edge cases: untyped variable, missing function scope, orphan declaration, multi-declaration.

Run:
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\scope_binding.py"
```

## 2) Database Systems: Conflict-Serializability
- File: `scripts/db_serializability.py`
- Core logic:
  - Build precedence graph edges from conflicting operations.
  - Detect cycle via transitive closure.
  - If acyclic, generate one valid serial order.
- Output predicates: `edge/2`, `cycle/1`, `serializable`, `not_serializable`, `order/2`.

Run:
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\db_serializability.py"
```

## 3) Operating Systems: Banker's Safe Sequence
- File: `scripts/os_banker.py`
- Core logic:
  - Compute `need = max - alloc`.
  - Guess a full process order.
  - Enforce that each chosen process can run with currently available resources.
- Output predicates: `need/3`, `available/3`, `run/2`.
- Safe state -> stable model exists; unsafe state -> `UNSATISFIABLE`.

Run:
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\os_banker.py"
```

## Cross-Domain Contrast (for report section)
- PPL: Symbolic static analysis (scope/type-related constraints).
- Database: Graph reasoning (conflict edges, cycle detection).
- Operating Systems: Resource-feasibility planning over ordered execution.
