#!/usr/bin/env bash
# Build a template repository against this repo's schemes, without applying
# them. Fails if any scheme does not render. Needs tinted-builder-rust.
#
#   scripts/build-check.sh [template-repo-url]   (default: tinted-shell)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
template="${1:-https://github.com/tinted-theming/tinted-shell}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/schemes"
cp -r "$root/base16" "$root/base24" "$root/tinted8" "$work/schemes/"
git clone --quiet --depth 1 "$template" "$work/template"
tinted-builder-rust build --schemes-dir "$work/schemes" "$work/template"
