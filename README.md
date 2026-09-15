# keycheat

This a vibe-coded project. I just needed something simple and working.

Turn a TOML file of keyboard shortcuts into a clean, newspaper-column
cheat sheet - as HTML and/or PDF. Styled after the classic
[VS Code keyboard shortcut PDFs](https://aka.ms/vscodekeybindings):
bold section headers, a compact key/description table per section, and
several columns that flow top-to-bottom, left-to-right like a newspaper
page.

## Mirror

Is Project is a mirror of my own hosted [Forgejo Instance](https://forgejo.noctiswolfshadow.com/NoctisWolfshadow/keycheat).

If you have Problems or want to ask something please head to here.

## Disclaimer

If you find a Problem or Bug.
Please create a Issue on the Forgejo Instance where you explain and also add Context.

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
- **`fonts`** is an optional table for pinning PDF fonts - see
  [Fonts (PDF)](#fonts-pdf) below.
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

The PDF renderer needs a real Unicode TTF on disk - ReportLab's built-in
fonts only cover plain ASCII/Latin-1, so symbols like arrows (`↑ ↓ ← →`)
would otherwise show as blank boxes. For each of 4 roles (regular, bold,
mono, mono bold) it picks the first match, in this order:

1. a `--font-regular` / `--font-bold` / `--font-mono` / `--font-mono-bold`
   CLI flag, if given;
2. otherwise the matching key in a `[fonts]` table in the TOML, if set;
3. otherwise a well-known OS path (DejaVu on Linux, Segoe UI/Arial on
   Windows and under WSL, Arial on macOS);
4. otherwise **a DejaVu Sans / DejaVu Sans Mono font bundled with
   keycheat itself** (`src/keycheat/assets/fonts/`, license included
   alongside).

Step 4 always succeeds, so **nothing ever needs to be downloaded** - the
"no Unicode font found" warning should only ever appear if those bundled
files were somehow removed from your install.

Configure it in the TOML when you want a specific look wherever the sheet
is built, without repeating CLI flags every time:

```toml
[fonts]
regular   = "C:/Windows/Fonts/segoeui.ttf"
bold      = "C:/Windows/Fonts/segoeuib.ttf"
mono      = "C:/Windows/Fonts/consola.ttf"
mono_bold = "C:/Windows/Fonts/consolab.ttf"
```

All four keys are optional - set only the ones you want to pin; the rest
still fall through steps 3-4 above. A relative path is resolved against
the *TOML file's* location, not your current directory, so a config stays
portable if you ship a font alongside it (e.g. `regular = "fonts/My.ttf"`).
A `--font-*` CLI flag always wins over the matching `[fonts]` entry.

If a bold-role file can't be found but its regular counterpart was, that
regular Unicode font is reused for "bold" text rather than dropping to a
non-Unicode base font - text renders at regular weight instead of bold,
rather than dropping symbols altogether.

### Listing fonts / finding a `.ttf` path

<details>
<summary><b>Windows</b> (PowerShell)</summary>

```powershell
Get-ChildItem "C:\Windows\Fonts" -Filter *.ttf | Select-Object Name
```

Common built-ins: `segoeui.ttf` / `segoeuib.ttf` (Segoe UI regular/bold),
`consola.ttf` / `consolab.ttf` (Consolas regular/bold, monospace).
</details>

<details>
<summary><b>WSL</b> (Windows Subsystem for Linux)</summary>

Same files as Windows above, but reached through the mounted C: drive:

```bash
ls /mnt/c/Windows/Fonts/*.ttf
```

(keycheat already checks `/mnt/c/Windows/Fonts/segoeui.ttf` etc.
automatically, so this is mainly useful for picking something other than
Segoe UI/Consolas.)
</details>

<details>
<summary><b>macOS</b></summary>

```bash
ls /System/Library/Fonts/Supplemental /Library/Fonts ~/Library/Fonts
```

Or open **Font Book**, select a font, and check "Show in Finder" for its
file path. Note: some macOS fonts ship as `.ttc` (collections), which
aren't always loadable directly - prefer a plain `.ttf` like
`/System/Library/Fonts/Supplemental/Arial.ttf` if one is having trouble.
</details>

<details>
<summary><b>Linux</b></summary>

```bash
fc-list | grep -i dejavu   # or any family name you're looking for
```

If nothing turns up and you want an OS-native font rather than the
bundled fallback: `sudo apt install fonts-dejavu` (Debian/Ubuntu) or the
equivalent for your distro.
</details>

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
  fonts.py         Unicode font resolution (CLI/TOML/OS/bundled) for the PDF renderer
  render_html.py   HTML renderer (Jinja2 + CSS columns)
  render_pdf.py    PDF renderer (ReportLab multi-frame layout)
  cli.py           `keycheat` command-line entry point
  templates/
    sheet.html.jinja
  assets/fonts/
    DejaVuSans*.ttf, DejaVuSansMono*.ttf   Bundled Unicode fallback fonts
    LICENSE-DejaVu.txt
examples/
  vscode-windows.toml   Full worked example (a port of the VS Code sheet)
```
