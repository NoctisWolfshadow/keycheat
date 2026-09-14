"""Renders a Sheet into a PDF using a landscape page split into several
side-by-side reportlab Frames. Content flows from frame to frame (and then
page to page) automatically, giving the same newspaper-column effect as the
HTML/CSS renderer."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .fonts import resolve_fonts
from .model import Sheet

_PAGE_SIZES = {"letter": LETTER, "a4": A4}

_INK = colors.HexColor("#1f1f1f")
_MUTED = colors.HexColor("#6e6e6e")
_FAINT = colors.HexColor("#9a9a9a")
_RULE = colors.HexColor("#d9d9d9")
_ROW_ALT = colors.HexColor("#f6f6f7")
_DESC = colors.HexColor("#333333")

_MARGIN = 0.55 * inch
_COLUMN_GAP = 0.32 * inch
_HEADER_RESERVED = 0.78 * inch
_FOOTER_RESERVED = 0.32 * inch


def render_pdf(
    sheet: Sheet,
    output_path: Path,
    *,
    columns: int = 3,
    pagesize: str = "letter",
    font_regular: str | None = None,
    font_bold: str | None = None,
    font_mono: str | None = None,
    font_mono_bold: str | None = None,
) -> None:
    fonts = resolve_fonts(font_regular, font_bold, font_mono, font_mono_bold)
    base_size = _PAGE_SIZES.get(pagesize, LETTER)
    page_w, page_h = landscape(base_size)

    has_head = bool(sheet.title or sheet.subtitle)
    top_margin = _MARGIN + (_HEADER_RESERVED if has_head else 0)
    bottom_margin = _MARGIN + (_FOOTER_RESERVED if sheet.footer else 0)

    usable_w = page_w - 2 * _MARGIN - _COLUMN_GAP * (columns - 1)
    col_w = usable_w / columns
    frame_h = page_h - top_margin - bottom_margin

    frames = []
    for i in range(columns):
        x = _MARGIN + i * (col_w + _COLUMN_GAP)
        frames.append(
            Frame(
                x,
                bottom_margin,
                col_w,
                frame_h,
                id=f"col{i}",
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
            )
        )

    def draw_static(canv, _doc):
        canv.saveState()
        if sheet.title:
            canv.setFont(fonts.sans_bold, 18)
            canv.setFillColor(_INK)
            canv.drawString(_MARGIN, page_h - _MARGIN - 0.28 * inch, sheet.title)
        if sheet.subtitle:
            canv.setFont(fonts.sans, 10.5)
            canv.setFillColor(_MUTED)
            canv.drawString(_MARGIN, page_h - _MARGIN - 0.5 * inch, sheet.subtitle)
        if sheet.footer:
            canv.setStrokeColor(_RULE)
            canv.setLineWidth(0.5)
            canv.line(_MARGIN, bottom_margin - 0.14 * inch, page_w - _MARGIN, bottom_margin - 0.14 * inch)
            canv.setFont(fonts.sans, 7.5)
            canv.setFillColor(_FAINT)
            canv.drawString(_MARGIN, bottom_margin - 0.28 * inch, sheet.footer)
        canv.setFont(fonts.sans, 7.5)
        canv.setFillColor(_FAINT)
        canv.drawRightString(page_w - _MARGIN, 0.3 * inch, str(canv.getPageNumber()))
        canv.restoreState()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=(page_w, page_h),
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title=sheet.title or "Keyboard Shortcuts",
    )
    doc.addPageTemplates([PageTemplate(id="columns", frames=frames, onPage=draw_static)])

    header_style = ParagraphStyle(
        "SectionHeader",
        fontName=fonts.sans_bold,
        fontSize=10.5,
        textColor=_INK,
        leading=13,
    )
    key_style = ParagraphStyle(
        "Key",
        fontName=fonts.mono_bold,
        fontSize=8.2,
        leading=11,
        textColor=_INK,
    )
    desc_style = ParagraphStyle(
        "Desc",
        fontName=fonts.sans,
        fontSize=8.4,
        leading=11,
        textColor=_DESC,
    )

    key_w = col_w * 0.40
    desc_w = col_w * 0.60

    def row_style(start_index: int, count: int) -> TableStyle:
        cmds = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 1.6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, -1), 8),
        ]
        for r in range(count):
            if (start_index + r) % 2 == 1:
                cmds.append(("BACKGROUND", (0, r), (-1, r), _ROW_ALT))
        return TableStyle(cmds)

    def make_table(rows_subset, start_index):
        t = Table(rows_subset, colWidths=[key_w, desc_w], hAlign="LEFT")
        t.setStyle(row_style(start_index, len(rows_subset)))
        return t

    story = []
    for section in sheet.sections:
        header = Paragraph(escape(section.name), header_style)
        rows = [
            [Paragraph(escape(s.keys), key_style), Paragraph(escape(s.description), desc_style)]
            for s in section.shortcuts
        ]

        # Glue the header to at least its first row so a section title never
        # ends up alone at the bottom of a column with its table starting in
        # the next one. The remaining rows are free to flow/split normally,
        # matching how the reference sheet lets long sections span columns.
        head_rows = rows[:1]
        rest_rows = rows[1:]

        block = [header, Spacer(1, 3), make_table(head_rows, start_index=0)]
        story.append(KeepTogether(block))
        if rest_rows:
            story.append(make_table(rest_rows, start_index=1))
        story.append(Spacer(1, 9))

    doc.build(story)
