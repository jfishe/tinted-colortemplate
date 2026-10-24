# tinted-colortemplate

[Tinted Theming](https://github.com/tinted-theming/home) schemes (tinted8,
base24 and base16) generated from hand-tuned Vim colour schemes written with
[vim-colortemplate](https://codeberg.org/lifepillar/vim-colortemplate). The
terminal, dircolors, Windows Terminal, PSReadLine and anything else
[tinty](https://github.com/tinted-theming/tinty) manages can then match the
Vim colour scheme.

## Schemes

| Source | Variants | Systems |
| --- | --- | --- |
| [vim-solarized8](https://codeberg.org/lifepillar/vim-solarized8) | `solarized8`, `-flat`, `-high`, `-low` × dark, light | tinted8, base24, base16 |

Planned: [vim-wwdc16-theme](https://codeberg.org/lifepillar/vim-wwdc16-theme),
[vim-wwdc17-theme](https://codeberg.org/lifepillar/vim-wwdc17-theme),
[vim-gruvbox8](https://codeberg.org/lifepillar/vim-gruvbox8).

Scheme names are `<system>-<variant>-<background>`, for example
`tinted8-solarized8-dark` or `base16-solarized8-flat-light`.

## Using the schemes with tinty

tinty reads custom schemes from `<data-dir>/custom-schemes/<system>/`. Link
that directory to `schemes/`:

```sh
ln -s "$PWD/schemes" ~/.local/share/tinted-theming/tinty/custom-schemes
tinty list --custom-schemes
tinty apply tinted8-solarized8-dark
```

To try the schemes without changing your default ring, add a ring to
`~/.config/tinted-theming/tinty/config.toml`:

```toml
[[rings]]
name = "solarized8"
schemes = ["tinted8-solarized8-dark", "tinted8-solarized8-light"]
```

Then step through it with `tinty cycle --ring solarized8`.

## How the colours are mapped

- **tinted8** uses the template's `Term Colors` as its 16-colour palette, so
  the terminal shows what the scheme expects in 16-colour Vim. UI colours
  (foreground, background, cursor, selection, gutter, ...) and syntax scopes
  come from the default definitions of the Vim highlight groups (`Normal`,
  `Cursor`, `Visual`, `LineNr`, `Comment`, ...).
- **base16/base24** put the background in ANSI 0 and the foreground in
  ANSI 7, so they cannot use `Term Colors` directly. Their neutrals follow the
  scheme's tonal ramp, set in the mapping file. Accents follow the ANSI hues,
  so `base0E` is magenta and `base0F` is the eighth accent (violet for
  Solarized).
- Only the default definition of each highlight group is used: what gvim, or
  Vim with `termguicolors`, shows with the scheme's default options.
  Environment- and option-specific overrides are ignored.

### Deviations from the Vim schemes

- **Solarized, tinted8:** Solarized's ANSI 8 (bright black) is the dark
  background colour. eza's punctuation (the symlink `->`), zsh-autosuggestions
  and git's dim output are drawn in ANSI 8, so they would disappear. Bright
  black is set to the comment grey instead.

## Regenerating

The converter is a [uv](https://docs.astral.sh/uv/) project. Each source
scheme has a mapping file in `mappings/`. Without `--repo`, the converter makes
a shallow clone of the repository named in the mapping.

```sh
uv run colortemplate2tinty mappings/solarized8.toml
uv run colortemplate2tinty mappings/solarized8.toml --repo ../vim-solarized8
```

Generated files start with a header that records the source template, the
upstream commit and the mapping file. Do not edit them by hand. Change the
mapping and regenerate instead.

### Mapping files

`[theme]` names the repository, the templates to convert and the author
metadata. Other tables override the built-in defaults in
`src/colortemplate2tinty/convert.py`: `[base16]`, `[base24]`,
`["tinted8.palette"]`, `["tinted8.syntax"]` and `["tinted8.ui"]`. Overrides
can be limited to one template (`[variants.solarized8_low.base16]`) or to one
background (`[variants.solarized8_low.dark.base16]`).

A value is a spec. A spec can list alternatives separated by `|`, and the
first one that resolves is used:

| Spec | Meaning |
| --- | --- |
| `#rrggbb` | literal colour |
| `term:N` | entry N of the template's `Term Colors` |
| `Group.fg`, `Group.bg` | colour the highlight group displays, after links, `none` and `reverse` are resolved |
| `Group.sp` | the group's special (undercurl) colour |
| `Group.hue` | the group's declared foreground, ignoring `reverse` |
| `@key` | another key of the same table |
| `name` | a colour defined with `Color: name` |

A key whose spec resolves to nothing is left out, and the Tinted Theming
builder derives it.

### Checking a change

The schemes are only accepted if templates build from them. To build template
repositories against the generated schemes without applying them, use a
scratch data directory:

```sh
mkdir -p /tmp/tc/repos && cp -r schemes /tmp/tc/repos/schemes
cp -r ~/.local/share/tinted-theming/tinty/repos/tinted-shell /tmp/tc/
tinty build -d /tmp/tc /tmp/tc/tinted-shell
```

### Development

```sh
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run pyrefly check
```

## License

MIT, see [LICENSE](LICENSE). The scheme colours are derived from third-party
works, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
