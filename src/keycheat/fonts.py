"""Unicode font registration for the PDF renderer.

ReportLab's built-in 14 base fonts (Helvetica, Courier, ...) only cover the
WinAnsi character range, so glyphs commonly used in shortcut sheets - arrows
(up down left right), the Mac option/command symbols, etc. - render as blank
boxes. Resolution order, first match wins, per role (regular/bold/mono/mono
bold):

  1. an explicit path passed in (from --font-* CLI flags, or a [fonts]
     table in the TOML - the caller merges those and passes the winner here)
  2. well-known OS font locations (Linux, Windows, macOS, and WSL's view of
     the Windows drive)
  3. a DejaVu Sans / DejaVu Sans Mono font bundled with this package (see
     assets/fonts/LICENSE-DejaVu.txt) - always present, so this is a
     guaranteed-to-work fallback and nothing ever needs to be downloaded.

Because step 3 always succeeds, every role always resolves to a real Unicode
font; base-14 fonts are only ever used if the bundled files themselves were
somehow stripped from the install.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_ASSETS = Path(__file__).parent / "assets" / "fonts"

_SANS_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/mnt/c/Windows/Fonts/segoeui.ttf",
    "/mnt/c/Windows/Fonts/arial.ttf",
    str(_ASSETS / "DejaVuSans.ttf"),
]
_SANS_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/mnt/c/Windows/Fonts/segoeuib.ttf",
    "/mnt/c/Windows/Fonts/arialbd.ttf",
    str(_ASSETS / "DejaVuSans-Bold.ttf"),
]
_MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "/System/Library/Fonts/Supplemental/Menlo.ttc",
    "/Library/Fonts/Menlo.ttc",
    "/mnt/c/Windows/Fonts/consola.ttf",
    str(_ASSETS / "DejaVuSansMono.ttf"),
]
_MONO_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/consolab.ttf",
    "/mnt/c/Windows/Fonts/consolab.ttf",
    str(_ASSETS / "DejaVuSansMono-Bold.ttf"),
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
        if not path_str:
            continue
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

    `font_*` args let a caller pin a specific .ttf/.otf file, taking
    priority over every auto-detected candidate (including the bundled
    fallback). Pass whatever CLI flag / TOML [fonts] value already won by
    the time this is called - this function doesn't know about either.
    """
    sans = _register("KCSans", _SANS_CANDIDATES, [font_regular] if font_regular else [])
    sans_bold = _register(
        "KCSansBold", _SANS_BOLD_CANDIDATES, [font_bold] if font_bold else []
    )
    mono = _register("KCMono", _MONO_CANDIDATES, [font_mono] if font_mono else [])
    mono_bold = _register(
        "KCMonoBold", _MONO_BOLD_CANDIDATES, [font_mono_bold] if font_mono_bold else []
    )

    # A bold role failing to resolve while its regular counterpart succeeded
    # would normally only happen with a deliberately narrow --font-bold
    # override. Reuse the regular Unicode font rather than dropping to a
    # base-14 bold font, so symbols still render (at regular, not bold,
    # weight) instead of showing blank boxes.
    sans_bold = sans_bold or sans
    mono_bold = mono_bold or mono

    unicode_ok = sans is not None and mono is not None

    if not unicode_ok:
        # Should only happen if the bundled assets/fonts/*.ttf files were
        # stripped from this install - every other path falls back to them.
        print(
            "keycheat: could not load any Unicode font, including the bundled "
            "fallback - falling back to PDF base fonts. Symbols such as arrows "
            "(up down left right) will not render. Your keycheat install may be "
            "missing its src/keycheat/assets/fonts/ files. You can also pass "
            "--font-regular/--font-mono (or set [fonts] in the TOML) to point "
            "at a .ttf file directly.",
            file=sys.stderr,
        )

    return FontSet(
        sans=sans or "Helvetica",
        sans_bold=sans_bold or "Helvetica-Bold",
        mono=mono or "Courier",
        mono_bold=mono_bold or "Courier-Bold",
        unicode_ok=unicode_ok,
    )
