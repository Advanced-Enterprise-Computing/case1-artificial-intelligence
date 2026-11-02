# Report PDF

Builds the submitted Case 1 report from the files in this repo. It contains:

- a front page and a contents page, where every line is a link
- a list of figures
- Part 1 and Part 2
- one reference list
- the notebook as an appendix

It runs on macOS only. The layout and the PDF come from the WebKit engine that ships with macOS, so no browser, LaTeX or extra Python package is needed.

## Use

1. Copy `team.example.json` to a private place outside the repo, and fill in the names and matriculation numbers.
2. Build the PDF. The `make_pdf.sh` path is relative to the repo root:

```bash
tools/report_pdf/make_pdf.sh /path/to/team.json /path/to/report.pdf
```

The front page shows the matriculation number and email columns only when they are filled in for every member, and a link to the repository when `repo` is set.

## How it works

1. `build.py` turns `report/part1_playground.md`, `report/part2_classifier.md` and `notebooks/cats_vs_dogs_classifier.ipynb` into one HTML page. It uses A4 at 595 × 842 px, where 1 px = 1 pt.
2. `paginate.js` splits that page into A4 pages:
   - Every part starts on a new page.
   - Paragraphs, lists and code blocks can be split between lines.
   - Headings stay with what follows them.
   - It adds the page numbers and fills in the contents page.
3. `render.js` loads the page in WebKit and waits until fonts and images are settled. It then runs the paginator and checks that every part still starts at the top of a page. Finally it writes each page as vector PDF and adds the links and bookmarks.
