#!/bin/bash
# Build the Case 1 report PDF from the files in this repo (macOS only).
# Usage: tools/report_pdf/make_pdf.sh <team.json> <out.pdf>
# team.json fills the front page (see team.example.json). Keep the copy with matriculation numbers outside the repo.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TEAM="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
PYTHON="$REPO/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON=python3

# work on a copy, so nothing generated ends up in the repo
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/report" "$WORK/notebooks"
cp -R "$REPO/report/img" "$REPO/report/part1_playground.md" "$REPO/report/part2_classifier.md" "$WORK/report/"
cp "$REPO/notebooks/cats_vs_dogs_classifier.ipynb" "$WORK/notebooks/"

"$PYTHON" -I "$HERE/build.py" "$WORK" "$TEAM"
osascript -l JavaScript "$HERE/render.js" "$WORK/report/case1_report.html" "$HERE/paginate.js" "$OUT"
