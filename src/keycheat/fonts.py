"""Best-effort Unicode font registration for the PDF renderer.

ReportLab's built-in 14 base fonts (Helvetica, Courier, ...) only cover the
WinAnsi character range, so glyphs commonly used in shortcut sheets - arrows
(up down left right), the Mac option/command symbols, etc. - render as blank
boxes. We look for a real TTF on disk (bundled DejaVu on Linux, Segoe UI /
Consolas on Windows, Helvetica/Menlo on macOS) and register it under a
stable name. If nothing is found we fall back to the base-14 fonts and warn
once, since plain ASCII shortcuts still render fine.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_SANS_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/mnt/c/Windows/Fonts/arial.ttf",
    "/mnt/c/Windows/Fonts/segoeui.ttf",
]
_SANS_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/mnt/c/Windows/Fonts/arialbd.ttf",
    "/mnt/c/Windows/Fonts/segoeuib.ttf",
]
_MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "/System/Library/Fonts/Supplemental/Menlo.ttc",
    "/Library/Fonts/Menlo.ttc",
    "/mnt/c/Windows/Fonts/consola.ttf",
]
_MONO_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/consolab.ttf",
    "/mnt/c/Windows/Fonts/consolab.ttf",
]


class FontSet:
    """Resolved font names to hand to reportlab ParagraphStyles."""

    def __init__(
        self, sans: str, sans_bold: str, mono: str, mono_bold: str, unicode_ok: bool
    ):
        self.sans = sans
        self.sans_bold = sans_bold
        self.mono = mono
        self.mono_bold = mono_bold
        self.unicode_ok = unicode_ok


def _register(name: str, candidates: list[str], extra: list[str]) -> str | None:
    for path_str in [*extra, *candidates]:
        path = Path(path_str)
        if path.is_file():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
                return name
            except Exception:
                continue
    return None


def resolve_fonts(
    font_regular: str | None = None,
    font_bold: str | None = None,
    font_mono: str | None = None,
    font_mono_bold: str | None = None,
) -> FontSet:
    """Register the best available Unicode fonts and return their names.

    `font_*` args let a user point at a specific .ttf/.otf file (useful when
    auto-detection picks nothing, e.g. a minimal Linux server, or when they
    want a specific look).
    """
    sans = _register("KCSans", _SANS_CANDIDATES, [font_regular] if font_regular else [])
    sans_bold = _register(
        "KCSansBold", _SANS_BOLD_CANDIDATES, [font_bold] if font_bold else []
    )
    mono = _register("KCMono", _MONO_CANDIDATES, [font_mono] if font_mono else [])
    mono_bold = _register(
        "KCMonoBold", _MONO_BOLD_CANDIDATES, [font_mono_bold] if font_mono_bold else []
    )

    unicode_ok = sans is not None and mono is not None

    if not unicode_ok:
        print(
            "keycheat: no Unicode TTF font found on this system - falling back to "
            "PDF base fonts. Symbols such as arrows (up down left right) may not "
            "render. Pass --font-regular/--font-mono to point at a .ttf file.",
            file=sys.stderr,
        )

    # Bold variants are only missing in unusual setups (e.g. regular found,
    # matching bold file absent). Section headers/keys are almost always
    # plain ASCII, so falling back to a base-14 bold font there is a safe
    # trade-off rather than fake-bolding a non-bold Unicode font.
    return FontSet(
        sans=sans or "Helvetica",
        sans_bold=sans_bold or "Helvetica-Bold",
        mono=mono or "Courier",
        mono_bold=mono_bold or "Courier-Bold",
        unicode_ok=unicode_ok,
    )
