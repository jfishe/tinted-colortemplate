"""Parse the subset of vim-colortemplate files needed to derive a terminal palette.

Only the default definition of each highlight group is kept: the first plain
`Group fg bg [attrs]` line per background. Environment- and option-specific
override lines (`/256/16`, `+visibility`, ...) are ignored, which means the
result is what gvim (or Vim with termguicolors) shows with default options.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
META_RE = re.compile(
    r"^(Full name|Short name|Author|Maintainer|URL|Description):\s*(.*)$"
)
SKIP_BLOCKS = {
    "verbatim": "endverbatim",
    "auxfile": "endauxfile",
    "documentation": "enddocumentation",
    "help": "endhelp",
}


@dataclass
class Highlight:
    fg: str
    bg: str
    sp: str | None = None
    attrs: frozenset[str] = frozenset()


@dataclass
class Section:
    colors: dict[str, str] = field(default_factory=dict)
    term_colors: list[str] = field(default_factory=list)
    groups: dict[str, Highlight] = field(default_factory=dict)
    links: dict[str, str] = field(default_factory=dict)


@dataclass
class Template:
    path: Path
    meta: dict[str, str] = field(default_factory=dict)
    sections: dict[str, Section] = field(default_factory=dict)

    @property
    def backgrounds(self) -> list[str]:
        return [b for b in ("dark", "light") if b in self.sections]


def _expand(path: Path, seen: set[Path]) -> list[str]:
    """Return the lines of `path` with `Include:` directives expanded."""
    path = path.resolve()
    if path in seen:
        raise ValueError(f"recursive include: {path}")
    out: list[str] = []
    for line in path.read_text().splitlines():
        m = re.match(r"^Include:\s*(\S+)", line)
        if m:
            out.extend(_expand(path.parent / m.group(1), seen | {path}))
        else:
            out.append(line)
    return out


def _strip_comment(line: str) -> str:
    i = line.find(";")
    return line if i < 0 else line[:i]


def parse(path: Path) -> Template:
    tpl = Template(path=path)
    section = tpl.sections.setdefault("any", Section())
    end_block: str | None = None
    in_term_colors = False

    for raw in _expand(path, set()):
        if end_block:
            if raw.strip() == end_block:
                end_block = None
            continue
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        first = line.split()[0]
        if first in SKIP_BLOCKS and not line.startswith(" "):
            end_block = SKIP_BLOCKS[first]
            continue
        if line.startswith("#"):
            continue

        if in_term_colors and line[0].isspace() and len(section.term_colors) < 16:
            section.term_colors.extend(line.split())
            continue
        in_term_colors = False

        if m := META_RE.match(line):
            tpl.meta.setdefault(m.group(1), m.group(2).strip())
        elif m := re.match(r"^Background:\s*(\w+)", line):
            section = tpl.sections.setdefault(m.group(1), Section())
        elif line.startswith("Color:"):
            name, gui = line.split()[1:3]
            if not HEX_RE.match(gui):
                raise ValueError(f"{path}: unsupported GUI color {gui!r} for {name}")
            section.colors[name] = gui.lower()
        elif line.startswith("Term Colors:"):
            section.term_colors = line.split(":", 1)[1].split()
            in_term_colors = True
        elif line[0].isspace() or line[0] == "/" or ":" in first:
            continue  # override line for a non-default environment/option
        else:
            _parse_group(line.split(), section)
    return tpl


def _parse_group(tokens: list[str], section: Section) -> None:
    name = tokens[0]
    if len(tokens) >= 3 and tokens[1] == "->":
        section.links.setdefault(name, tokens[2])
        return
    if len(tokens) < 3 or tokens[1].startswith(("/", "+")) or "/" in name:
        return
    sp = None
    attrs: set[str] = set()
    for tok in tokens[3:]:
        if tok.startswith("s="):
            sp = tok[2:]
        else:
            attrs.update(a for a in tok.split(",") if a)
    section.groups.setdefault(
        name, Highlight(tokens[1], tokens[2], sp, frozenset(attrs))
    )
