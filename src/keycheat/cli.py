"""Command-line interface: `keycheat <config.toml> [options]`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .model import SheetConfigError, load_sheet
from .render_html import render_html
from .render_pdf import render_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keycheat",
        description="Render a TOML keyboard-shortcut config into an HTML and/or PDF cheat sheet.",
    )
    parser.add_argument("config", type=Path, help="Path to the shortcuts .toml file")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output base path without extension (default: same name as config)",
    )
    parser.add_argument(
        "--format",
        choices=["html", "pdf", "both"],
        default="both",
        help="Which output(s) to generate (default: both)",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=3,
        help="Number of newspaper-style columns (default: 3)",
    )
    parser.add_argument(
        "--pagesize",
        choices=["letter", "a4"],
        default="letter",
        help="PDF page size, rendered landscape (default: letter)",
    )
    parser.add_argument("--font-regular", type=Path, default=None, help="Path to a .ttf for body text")
    parser.add_argument("--font-bold", type=Path, default=None, help="Path to a .ttf for bold headers")
    parser.add_argument("--font-mono", type=Path, default=None, help="Path to a .ttf for shortcut keys")
    parser.add_argument("--font-mono-bold", type=Path, default=None, help="Path to a bold monospace .ttf")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.columns < 1:
        parser.error("--columns must be at least 1")

    try:
        sheet = load_sheet(args.config)
    except SheetConfigError as exc:
        print(f"keycheat: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"keycheat: no such file: {args.config}", file=sys.stderr)
        return 1

    out_base = args.output if args.output is not None else args.config.with_suffix("")
    out_base.parent.mkdir(parents=True, exist_ok=True)

    if args.format in ("html", "both"):
        html = render_html(sheet, columns=args.columns)
        html_path = out_base.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        print(f"Wrote {html_path}")

    if args.format in ("pdf", "both"):
        pdf_path = out_base.with_suffix(".pdf")
        render_pdf(
            sheet,
            pdf_path,
            columns=args.columns,
            pagesize=args.pagesize,
            font_regular=str(args.font_regular) if args.font_regular else None,
            font_bold=str(args.font_bold) if args.font_bold else None,
            font_mono=str(args.font_mono) if args.font_mono else None,
            font_mono_bold=str(args.font_mono_bold) if args.font_mono_bold else None,
        )
        print(f"Wrote {pdf_path}")

    return 0
