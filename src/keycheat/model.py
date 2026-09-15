"""Data model for a keycheat sheet: parses the TOML config into a Sheet."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Top-level TOML keys that are metadata, not shortcut tables.
_META_KEYS = {"title", "subtitle", "leader", "footer", "fonts"}
_FONT_ROLES = {"regular", "bold", "mono", "mono_bold"}

_LEADER_TOKEN = "<leader>"


@dataclass
class Shortcut:
    keys: str
    description: str


@dataclass
class Section:
    name: str
    shortcuts: list[Shortcut] = field(default_factory=list)


@dataclass
class FontPaths:
    regular: str | None = None
    bold: str | None = None
    mono: str | None = None
    mono_bold: str | None = None


@dataclass
class Sheet:
    title: str | None
    subtitle: str | None
    leader: str | None
    footer: str | None
    fonts: FontPaths
    sections: list[Section]


class SheetConfigError(ValueError):
    """Raised when the TOML config is malformed or invalid."""


def load_sheet(path: Path) -> Sheet:
    """Load and validate a shortcut-sheet TOML file into a Sheet."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise SheetConfigError(f"Could not parse '{path}': {exc}") from exc

    title = _optional_str(data, "title")
    subtitle = _optional_str(data, "subtitle")
    leader = _optional_str(data, "leader")
    footer = _optional_str(data, "footer")
    fonts = _parse_fonts(data)

    sections: list[Section] = []
    for key, value in data.items():
        if key in _META_KEYS:
            continue
        if not isinstance(value, dict):
            raise SheetConfigError(
                f"Top-level key '{key}' must be a table of shortcuts, e.g.:\n\n"
                f"  [{key}]\n"
                f'  "Ctrl+X" = "Some action"\n'
            )

        shortcuts: list[Shortcut] = []
        for combo, description in value.items():
            if isinstance(description, dict):
                raise SheetConfigError(
                    f"[{key}] entry '{combo}' looks like a nested table. "
                    "Shortcut tables must map a key combo string to a plain "
                    "description string, not another table."
                )
            resolved_combo = _resolve_leader(combo, leader, context=f"[{key}] \"{combo}\"")
            shortcuts.append(Shortcut(keys=resolved_combo, description=str(description)))

        if not shortcuts:
            raise SheetConfigError(f"Section [{key}] has no shortcuts defined.")

        sections.append(Section(name=key, shortcuts=shortcuts))

    if not sections:
        raise SheetConfigError(
            "No shortcut sections found. Define at least one table, e.g.:\n\n"
            "  [General]\n"
            '  "Ctrl+S" = "Save"\n'
        )

    return Sheet(
        title=title,
        subtitle=subtitle,
        leader=leader,
        footer=footer,
        fonts=fonts,
        sections=sections,
    )


def _optional_str(data: dict, key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise SheetConfigError(f"Top-level key '{key}' must be a string.")
    return value


def _parse_fonts(data: dict) -> FontPaths:
    value = data.get("fonts")
    if value is None:
        return FontPaths()
    if not isinstance(value, dict):
        raise SheetConfigError(
            "Top-level key 'fonts' must be a table, e.g.:\n\n"
            "  [fonts]\n"
            '  regular = "C:/Windows/Fonts/segoeui.ttf"\n'
            '  mono = "C:/Windows/Fonts/consola.ttf"\n'
        )

    unknown = set(value) - _FONT_ROLES
    if unknown:
        raise SheetConfigError(
            f"[fonts] has unknown key(s) {sorted(unknown)}. "
            f"Valid keys are: {', '.join(sorted(_FONT_ROLES))}."
        )

    paths: dict[str, str | None] = {}
    for role in _FONT_ROLES:
        role_value = value.get(role)
        if role_value is None:
            paths[role] = None
        elif isinstance(role_value, str):
            paths[role] = role_value
        else:
            raise SheetConfigError(f"[fonts] {role} must be a string path to a .ttf file.")

    return FontPaths(**paths)


def _resolve_leader(combo: str, leader: str | None, *, context: str) -> str:
    if _LEADER_TOKEN not in combo:
        return combo
    if not leader:
        raise SheetConfigError(
            f"{context} uses {_LEADER_TOKEN} but no top-level 'leader' key is set.\n"
            f'Add e.g.  leader = "Ctrl+K"  near the top of the file.'
        )
    return combo.replace(_LEADER_TOKEN, leader)
