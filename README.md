# keycheat

This a vibe-coded project. I just needed something simple and working.

Turn a TOML file of keyboard shortcuts into a clean, newspaper-column
cheat sheet - as HTML and/or PDF. Styled after the classic
[VS Code keyboard shortcut PDFs](https://aka.ms/vscodekeybindings):
bold section headers, a compact key/description table per section, and
several columns that flow top-to-bottom, left-to-right like a newspaper
page.

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
uv run keycheat examples/vscode-windows.toml
```

This writes `examples/vscode-windows.html` and `examples/vscode-windows.pdf`
next to the config file. See that file for a fully working example.

```
usage: keycheat [-h] [-o OUTPUT] [--format {html,pdf,both}]
                 [--columns COLUMNS] [--pagesize {letter,a4}]
                 [--font-regular FONT_REGULAR] [--font-bold FONT_BOLD]
                 [--font-mono FONT_MONO] [--font-mono-bold FONT_MONO_BOLD]
                 config

-o, --output PATH      Output base path without extension
                        (default: same name/location as the config file)
--format {html,pdf,both}
                        Which output(s) to generate (default: both)
--columns N             Number of newspaper-style columns (default: 3)
--pagesize {letter,a4}  PDF page size, rendered landscape (default: letter)
--font-regular/--font-bold/--font-mono/--font-mono-bold PATH
                        Point at a specific .ttf if auto-detected fonts
                        don't cover a symbol you need (see Fonts, below)
```

## Writing a config

```toml
title = "My App"
subtitle = "Keyboard shortcuts for Windows"
leader = "Ctrl+K"
footer = "Optional small print shown at the bottom"

[General]
"Ctrl+S" = "Save"
"Ctrl+Shift+P" = "Show Command Palette"

[File management]
"<leader>+S" = "Save All"
```

- **`title` / `subtitle` / `footer`** are all optional strings shown at the
  top/bottom of the sheet.
- **Every other top-level table becomes one section**, in the order it
  appears in the file. Its name is used as the section header verbatim -
  quote it if it contains spaces, e.g. `["File management"]`.
- **Each entry in a section** is `"key combo" = "description"`.
- **`leader`** is a single prefix substituted anywhere the literal token
  `<leader>` appears inside a key combo - similar to the `<leader>` key in
  Neovim. It's meant for chorded shortcuts that all start the same way
  (VS Code's `Ctrl+K, ...` family, for example): set `leader = "Ctrl+K"`
  once, then write `"<leader> S"` instead of repeating `"Ctrl+K S"`
  everywhere. If `leader` isn't set, don't use `<leader>` - keycheat will
  raise a clear error telling you where.
- TOML requires a literal backslash to be written as `\\` inside a
  double-quoted string (e.g. `"Ctrl+\\"` for `Ctrl+\`).

## Fonts (PDF)

The PDF renderer looks for a real Unicode TTF on disk (DejaVu Sans on
Linux, Segoe UI/Arial on Windows, Arial on macOS) so symbols like arrows
(`↑ ↓ ← →`) render correctly - ReportLab's built-in fonts only cover
plain ASCII/Latin-1 and would otherwise show blank boxes. If none of the
built-in candidate paths exist on your machine, keycheat prints a warning
and falls back to those built-in fonts (fine for plain-ASCII shortcuts).
Use `--font-regular` / `--font-bold` / `--font-mono` / `--font-mono-bold`
to point at specific `.ttf` files if you need to override this.

## Layout notes

Both renderers share the same parsed data, but lay it out with different
engines so they stay visually consistent without a heavyweight
HTML-to-PDF conversion step (which would need system libraries like
Pango/Cairo that are painful to install on Windows):

- **HTML** uses a plain CSS `columns` layout - open it in any browser and
  Ctrl/Cmd+P to print your own PDF if you'd rather use the browser's
  renderer.
- **PDF** uses [ReportLab](https://www.reportlab.com/), with a page
  template of side-by-side frames that content flows through automatically
  (the same idiom used for newsletter layouts), so a long section can
  split across columns/pages just like in the reference sheet, while a
  section header is always kept with at least its first row.

## Project layout

```
src/keycheat/
  model.py         TOML parsing, validation, <leader> substitution
  fonts.py         Unicode font auto-detection for the PDF renderer
  render_html.py   HTML renderer (Jinja2 + CSS columns)
  render_pdf.py    PDF renderer (ReportLab multi-frame layout)
  cli.py           `keycheat` command-line entry point
  templates/
    sheet.html.jinja
examples/
  vscode-windows.toml   Full worked example (a port of the VS Code sheet)
```
