"""Map a parsed colortemplate onto tinted8, base24 and base16 schemes.

A mapping value is a spec, tried left to right across `|` alternatives:

    #rrggbb      literal colour
    term:N       entry N of the template's `Term Colors`
    Group.fg     colour Group displays as foreground (links, `none` and
    Group.bg     reverse/standout resolved against Normal)
    Group.sp     special (undercurl) colour
    Group.hue    declared foreground, ignoring reverse (ErrorMsg's red)
    @key         another key of the same output section
    name         colour defined with `Color: name`

A spec that resolves to nothing leaves the key out, so the tinted-theming
builder derives it.
"""

from .parser import Highlight, Template

TINTED8_PALETTE = {
    "black": "term:0",
    "red": "term:1",
    "green": "term:2",
    "yellow": "term:3",
    "blue": "term:4",
    "magenta": "term:5",
    "cyan": "term:6",
    "white": "term:7",
    "black-bright": "term:8",
    "red-bright": "term:9",
    "green-bright": "term:10",
    "yellow-bright": "term:11",
    "blue-bright": "term:12",
    "magenta-bright": "term:13",
    "cyan-bright": "term:14",
    "white-bright": "term:15",
    "orange": "orange",
    "gray": "Comment.fg",
    "brown": "brown",
}

TINTED8_SYNTAX = {
    "comment": "Comment.fg",
    "string": "String.fg",
    "string.regexp": "SpecialChar.fg",
    "constant": "Constant.fg",
    "constant.numeric": "Number.fg",
    "constant.language": "Boolean.fg",
    "constant.character.escape": "SpecialChar.fg",
    "variable": "Identifier.fg",
    "keyword": "Keyword.fg",
    "keyword.control": "Conditional.fg",
    "keyword.control.import": "Include.fg",
    "keyword.operator": "Operator.fg",
    "storage": "StorageClass.fg",
    "storage.type": "Type.fg",
    "entity.name.function": "Function.fg",
    "support.function": "Function.fg",
    "entity.name.type": "Type.fg",
    "entity.name.tag": "Tag.fg",
    "entity.name.label": "Label.fg",
    "punctuation": "Delimiter.fg",
    "invalid": "Error.hue",
    "markup.heading": "Title.fg",
    "markup.link": "Underlined.fg",
    "markup.inserted": "Added.fg|DiffAdd.fg",
    "markup.changed": "Changed.fg|DiffChange.fg",
    "markup.deleted": "Removed.fg|DiffDelete.fg",
}

TINTED8_UI = {
    "global.background.normal": "Normal.bg",
    "global.background.dark": "CursorLine.bg",
    "global.foreground.normal": "Normal.fg",
    "global.foreground.dark": "LineNr.fg",
    "chrome.background.normal": "StatusLineNC.bg",
    "chrome.foreground.normal": "StatusLineNC.fg",
    "border.normal": "VertSplit.bg",
    "accent.normal": "Directory.fg",
    "link.normal.foreground": "Underlined.fg",
    "gutter.background": "LineNr.bg",
    "gutter.foreground": "LineNr.fg",
    "whitespace.foreground": "NonText.fg",
    "cursor.normal.background": "Cursor.bg",
    "cursor.normal.foreground": "Cursor.fg",
    "selection.background": "Visual.bg",
    "selection.foreground": "Visual.fg",
    "highlight.line.background": "CursorLine.bg",
    "highlight.search.background": "Search.bg",
    "highlight.search.foreground": "Search.fg",
    "highlight.text.background": "MatchParen.bg",
    "highlight.text.foreground": "MatchParen.fg",
    "status.error": "ErrorMsg.hue",
    "status.warning": "WarningMsg.fg",
    "status.success": "Added.fg|DiffAdd.fg",
    "status.info": "MoreMsg.fg",
    "tooltip.background": "Pmenu.bg",
    "tooltip.foreground": "Pmenu.fg",
}

BASE16 = {
    "base00": "Normal.bg",
    "base01": "CursorLine.bg",
    "base02": "Visual.bg",
    "base03": "Comment.fg",
    "base04": "LineNr.fg",
    "base05": "Normal.fg",
    "base06": "term:7",
    "base07": "term:15",
    "base08": "term:1",
    "base09": "orange|term:9",
    "base0A": "term:3",
    "base0B": "term:2",
    "base0C": "term:6",
    "base0D": "term:4",
    "base0E": "term:5",
    "base0F": "term:13",
}

BASE24 = BASE16 | {
    "base10": "@base00",
    "base11": "@base00",
    "base12": "term:9",
    "base13": "term:11",
    "base14": "term:10",
    "base15": "term:14",
    "base16": "term:12",
    "base17": "term:13",
}

DEFAULTS = {
    "tinted8.palette": TINTED8_PALETTE,
    "tinted8.syntax": TINTED8_SYNTAX,
    "tinted8.ui": TINTED8_UI,
    "base16": BASE16,
    "base24": BASE24,
}


class Resolver:
    def __init__(self, tpl: Template, background: str) -> None:
        self.tpl = tpl
        self.sec = tpl.sections[background]
        self.any = tpl.sections.get("any")

    def color(self, name: str) -> str | None:
        if name in ("none", "omit"):
            return None
        if name in ("fg", "bg"):
            normal = self.group("Normal")
            if normal is None or name in (normal.fg, normal.bg):
                return None  # Normal cannot refer to itself
            return self.attr("Normal", name)
        if name in self.sec.colors:
            return self.sec.colors[name]
        if self.any and name in self.any.colors:
            return self.any.colors[name]
        return None

    def group(self, name: str) -> Highlight | None:
        for _ in range(16):
            for sec in (self.sec, self.any):
                if sec and name in sec.groups:
                    return sec.groups[name]
            target = self.sec.links.get(name) or (self.any and self.any.links.get(name))
            if not target or target == "omit":
                return None
            name = target
        raise ValueError(f"link loop at {name}")

    def attr(self, group: str, which: str) -> str | None:
        hl = self.group(group)
        if hl is None:
            return None
        if which == "sp":
            return self.color(hl.sp) if hl.sp else None
        if which == "hue":
            return self.color(hl.fg) or self.attr("Normal", "fg")
        fg, bg = self.color(hl.fg), self.color(hl.bg)
        if group != "Normal":
            fg = fg or self.attr("Normal", "fg")
            bg = bg or self.attr("Normal", "bg")
        if hl.attrs & {"reverse", "inverse", "standout"}:
            fg, bg = bg, fg
        return fg if which == "fg" else bg

    def spec(self, spec: str, done: dict[str, str]) -> str | None:
        for alt in spec.split("|"):
            alt = alt.strip()
            if alt.startswith("#"):
                value = alt.lower()
            elif alt.startswith("term:"):
                i = int(alt[5:])
                tc = self.sec.term_colors
                value = self.color(tc[i]) if i < len(tc) else None
            elif alt.startswith("@"):
                value = done.get(alt[1:])
            elif "." in alt:
                group, which = alt.rsplit(".", 1)
                value = self.attr(group, which)
            else:
                value = self.color(alt)
            if value:
                return value
        return None


def resolve_table(
    resolver: Resolver, table: str, overrides: list[dict[str, dict[str, str]]]
) -> dict[str, str]:
    specs = dict(DEFAULTS[table])
    for layer in overrides:
        specs.update(layer.get(table, {}))
    out: dict[str, str] = {}
    pending = dict(specs)
    # `@key` references can point forward, so resolve until nothing changes.
    while pending:
        progress = False
        for key, spec in list(pending.items()):
            refs = [a[1:] for a in spec.split("|") if a.strip().startswith("@")]
            if any(r in pending for r in refs):
                continue
            value = resolver.spec(spec, out) if spec else None
            if value:
                out[key] = value
            del pending[key]
            progress = True
        if not progress:
            raise ValueError(f"circular @ references in {table}: {sorted(pending)}")
    return {k: out[k] for k in specs if k in out}
