# PDF Visual Read Skill

## Goal
Read PDF content visually (like a human) instead of relying on text extraction.

## Workflow
1. Render PDF pages to PNG images:

```bash
c:/Users/HAD/Desktop/PPLMR/.venv/Scripts/python.exe scripts/pdf_visual_reader.py report.pdf --pages 1,8
```

2. Open rendered images and inspect them directly:
- `report/_pdf_pages/page_01.png`
- `report/_pdf_pages/page_08.png`

## Notes
- This is visual reading, not plain-text extraction.
- Increase quality with `--zoom 2.5` or `--zoom 3.0` if needed.
- Render all pages by omitting `--pages`.
