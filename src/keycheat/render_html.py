"""Renders a Sheet into a standalone HTML document: CSS multi-column
layout on screen, and a clean single-column, correctly paged layout when
printed (see the template's @media print comment for why those differ)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .model import Sheet

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(sheet: Sheet, columns: int = 3, pagesize: str = "letter") -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("sheet.html.jinja")
    return template.render(
        title=sheet.title,
        subtitle=sheet.subtitle,
        footer=sheet.footer,
        sections=sheet.sections,
        columns=columns,
        pagesize=pagesize,
    )
