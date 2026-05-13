#!/usr/bin/env python3
"""Render PDF pages to PNG images for visual inspection.

Usage examples:
  python scripts/pdf_visual_reader.py report.pdf
  python scripts/pdf_visual_reader.py report.pdf --pages 1,8,11 --zoom 2.0
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz  # PyMuPDF


def parse_pages(pages_arg: str | None, page_count: int) -> list[int]:
    if not pages_arg:
        return list(range(page_count))

    pages: list[int] = []
    for token in pages_arg.split(','):
        token = token.strip()
        if not token:
            continue
        if '-' in token:
            start_s, end_s = token.split('-', 1)
            start = int(start_s)
            end = int(end_s)
            if start > end:
                start, end = end, start
            pages.extend(range(start - 1, end))
        else:
            pages.append(int(token) - 1)

    # Deduplicate while keeping order and clamp bounds.
    seen = set()
    cleaned: list[int] = []
    for p in pages:
        if 0 <= p < page_count and p not in seen:
            seen.add(p)
            cleaned.append(p)
    return cleaned


def render_pdf(pdf_path: Path, output_dir: Path, pages_arg: str | None, zoom: float) -> list[Path]:
    doc = fitz.open(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = parse_pages(pages_arg, doc.page_count)
    matrix = fitz.Matrix(zoom, zoom)
    written: list[Path] = []

    for idx in pages:
        pix = doc[idx].get_pixmap(matrix=matrix)
        out_file = output_dir / f"page_{idx + 1:02d}.png"
        pix.save(str(out_file))
        written.append(out_file)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PDF pages to PNG for visual reading")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument(
        "--output-dir",
        default="report/_pdf_pages",
        help="Output directory for PNG pages (default: report/_pdf_pages)",
    )
    parser.add_argument(
        "--pages",
        default=None,
        help="Pages to render, 1-based. Example: 1,3,5-8 (default: all pages)",
    )
    parser.add_argument(
        "--zoom",
        type=float,
        default=2.0,
        help="Render zoom factor (default: 2.0)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    written = render_pdf(pdf_path, Path(args.output_dir), args.pages, args.zoom)
    print(f"Rendered {len(written)} page(s)")
    for p in written:
        print(p)


if __name__ == "__main__":
    main()
