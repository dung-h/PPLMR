# PPL Honors Module Mini-Project — Submission README

This repository contains a mini-project implementing three Answer Set Programming (ASP) applications for
Principles of Programming Languages (PPL), Database Systems, and Operating Systems. The project includes
ASP encodings, Python runners, and an academic report.

Summary
- 28 test cases total: 12 (PPL), 9 (Database), 7 (OS)
- `report/report.tex` and `report.pdf` (compiled with XeLaTeX) are included for submission preview.

Prerequisites
- Python 3.8+ (recommended) and `pip`
- Clingo (Potassco) installed and on PATH
- XeLaTeX (for compiling the report)

Quick build & tests
1. Create and activate a virtual environment (optional):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt    # if provided
```
2. Run domain tests:
```powershell
python scripts/scope_binding.py
python scripts/db_serializability.py
python scripts/os_banker.py
```
3. Build the report (XeLaTeX):
```powershell
cd report
xelatex report.tex
xelatex report.tex
cd ..
```

What to include in the submission ZIP
- `scripts/` — Python runners and helpers
- `asp/` — ASP encodings (baseline and variants)
- `cases/` — all test case files (PPL, db, os)
- `report/report.tex` and `report/report.pdf`
- `README.md`, `APPLICATIONS.md`, `AGENTS.md` (if relevant)
- `vendor/tyc/src/` (source only) — include `vendor/tyc/build/` only if generated artifacts are required to run offline

Files to avoid committing (generated / reproducible)
- `.venv/`, `venv/`
- LaTeX auxiliary files: `*.aux`, `*.log`, `*.out`, `*.synctex.gz`
- Rendered images and temporary outputs: `report/_pdf_pages/`, `*.png`

If you want me to add a `.gitignore` and remove generated files from git index, I can do that next.

Contact / Author
- Nhóm 8:
	- 2310543 — HỒ ANH DŨNG — dung.hokhmt2k23@hcmut.edu.vn
	- 2312264 — LÊ THÀNH NGHĨA — nghia.lethanh58566@hcmut.edu.vn
	- 2312291 — VŨ TRỌNG NGHĨA — nghia.vutrong@hcmut.edu.vn

Deadline (course): May 15, 2026 23:59 (GMT+7)

---
See `report/report.tex` for the full academic writeup and cross-domain analysis.
# PPLMR
