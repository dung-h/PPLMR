# PPL HM Mini-Project

## Structure
- `scripts/`: Python runners for the 3 ASP applications.
- `asp/`: generated baseline ASP programs grouped by domain.
- `cases/`: generated edge-case ASP programs grouped by domain.
- `report/`: report source and compiled PDF.
- `main_en.txt`, `main_en.pdf`: assignment statement.
- `AGENTS.md`: internal progress log, ignored by git.

## Environment
- Python 3.12+
- `clingo` installed in the active environment
- Optional: XeLaTeX to rebuild `report/report.pdf`

## Run
```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\scope_binding.py"
& ".\.venv\Scripts\python.exe" ".\scripts\db_serializability.py"
& ".\.venv\Scripts\python.exe" ".\scripts\os_banker.py"
```

## Outputs
- PPL baseline: `asp/ppl/scope_binding.lp`
- PPL edge cases: `cases/ppl/*.lp`
- Database baseline: `asp/database/database_serializability.lp`
- Database edge cases: `cases/db/*.lp`
- OS baseline: `asp/os/os_banker.lp`
- OS edge cases: `cases/os/*.lp`

## Submission checklist
- Include `scripts/`, `asp/`, `cases/`, `report/report.tex`, `report/report.pdf`, and assignment-related data.
- Exclude `.venv/`, LaTeX temporary files, and `AGENTS.md`.
