"""Renders a Sheet into a standalone HTML document using CSS multi-column
layout, so it flows like a newspaper page both on screen and when printed."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .model import Sheet

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(sheet: Sheet, columns: int = 3) -> str:
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
    )
