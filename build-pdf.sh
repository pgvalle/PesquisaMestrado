#!/usr/bin/env bash

set -euo pipefail

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
source_name="projeto-dissertacao"
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/${source_name}.XXXXXX")"

cleanup() {
  rm -rf -- "$build_dir"
}
trap cleanup EXIT HUP INT TERM

for command_name in xelatex bibtex; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$command_name" >&2
    exit 1
  fi
done

cp -- "$project_dir/$source_name.tex" "$build_dir/"
cp -- "$project_dir/refs.bib" "$build_dir/"
mkdir -p -- "$build_dir/assets"
cp -- "$project_dir/assets/uerj.png" "$build_dir/assets/"

cd -- "$build_dir"

xelatex -interaction=nonstopmode -halt-on-error "$source_name.tex"
bibtex "$source_name"
xelatex -interaction=nonstopmode -halt-on-error "$source_name.tex"
xelatex -interaction=nonstopmode -halt-on-error "$source_name.tex"

cp -- "$source_name.pdf" "$project_dir/$source_name.pdf"
printf 'Generated: %s\n' "$project_dir/$source_name.pdf"
