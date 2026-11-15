from pathlib import Path

import pytest

from colortemplate2tinty import convert as run_convert
from colortemplate2tinty.convert import Resolver, resolve_table
from colortemplate2tinty.parser import parse

TEMPLATE = """\
; comment
Full name:  Test Scheme
Short name: test_scheme
Include: _inc.colortemplate

Background: dark
Color: black #000000 0 0
Color: white #ffffff 15 15
Color: red  #ff0000 1 1
Color: gray #808080 8 8
Term Colors: black red black black black black black white
             gray red black black black black black white
Normal       white black
Normal /256  red  red
             /16  red  red
Visual       gray black reverse  ; trailing comment
ErrorMsg     red  white reverse
Comment      gray none italic
verbatim
Normal red red
endverbatim
"""

INCLUDE = """\
Background: any
Function -> Comment
"""

MAPPING = """\
[theme]
repo = "https://example.invalid/test.git"
templates = ["test_scheme"]
author = "me"
theme-author = "them"

[base16]
base01 = "#123456"

[variants.test_scheme.dark.base16]
base02 = "@base01"
"""


@pytest.fixture
def tpl_path(tmp_path: Path) -> Path:
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "_inc.colortemplate").write_text(INCLUDE)
    path = tmp_path / "templates" / "test_scheme.colortemplate"
    path.write_text(TEMPLATE)
    return path


def test_parse_keeps_default_definitions(tpl_path: Path) -> None:
    tpl = parse(tpl_path)
    assert tpl.meta["Full name"] == "Test Scheme"
    assert tpl.backgrounds == ["dark"]
    dark = tpl.sections["dark"]
    assert dark.groups["Normal"].fg == "white"
    assert len(dark.term_colors) == 16
    assert tpl.sections["any"].links["Function"] == "Comment"


def test_resolver_handles_reverse_none_and_links(tpl_path: Path) -> None:
    r = Resolver(parse(tpl_path), "dark")
    assert r.attr("Visual", "bg") == "#808080"
    assert r.attr("ErrorMsg", "fg") == "#ffffff"
    assert r.attr("ErrorMsg", "hue") == "#ff0000"
    assert r.attr("Comment", "bg") == "#000000"
    assert r.attr("Function", "fg") == "#808080"
    assert r.spec("term:9", {}) == "#ff0000"
    assert r.spec("Missing.fg|gray", {}) == "#808080"


def test_resolve_table_orders_references(tpl_path: Path) -> None:
    r = Resolver(parse(tpl_path), "dark")
    layers = [{"base16": {"base02": "@base01", "base01": "#123456"}}]
    out = resolve_table(r, "base16", layers)
    assert out["base02"] == "#123456"
    assert list(out)[:3] == ["base00", "base01", "base02"]


def test_convert_writes_all_systems(tpl_path: Path, tmp_path: Path) -> None:
    mapping = tmp_path / "test.toml"
    mapping.write_text(MAPPING)
    written = run_convert(mapping, tpl_path.parent.parent, tmp_path / "out")
    names = sorted(p.relative_to(tmp_path / "out").as_posix() for p in written)
    assert names == [
        "base16/test-scheme-dark.yaml",
        "base24/test-scheme-dark.yaml",
        "tinted8/test-scheme-dark.yaml",
    ]
    base16 = (tmp_path / "out/base16/test-scheme-dark.yaml").read_text()
    assert 'base02: "#123456"' in base16
    tinted8 = (tmp_path / "out/tinted8/test-scheme-dark.yaml").read_text()
    assert 'red-bright: "#ff0000"' in tinted8
    assert 'status.error: "#ff0000"' in tinted8


V3_TEMPLATE = """\
Full  name: V3 Scheme
Short name: v3
helpfile
Normal red red
endhelpfile

Background: dark
Color: bg  rgb(  1, 2,  3) 0 Black
Color: fg  #FFFFFF 15 White
Term colors: bg bg bg bg bg bg bg fg
             bg bg bg bg bg bg bg fg
Normal fg bg
"""


def test_parse_colortemplate_v3_syntax(tmp_path: Path) -> None:
    path = tmp_path / "v3.colortemplate"
    path.write_text(V3_TEMPLATE)
    tpl = parse(path)
    assert tpl.meta["Full name"] == "V3 Scheme"
    dark = tpl.sections["dark"]
    assert dark.colors == {"bg": "#010203", "fg": "#ffffff"}
    assert len(dark.term_colors) == 16
    assert "Normal" not in tpl.sections["any"].groups
    assert dark.groups["Normal"].fg == "fg"


def test_parse_rejects_unknown_gui_color(tmp_path: Path) -> None:
    path = tmp_path / "bad.colortemplate"
    path.write_text("Background: dark\nColor: x rgb(256, 0, 0) 0 Black\n")
    with pytest.raises(ValueError, match="unsupported GUI color"):
        parse(path)
