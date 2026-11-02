"""Build the Case 1 report as one HTML file (style C, TU green) from a snapshot of the repo.
Usage: python -I build.py <snapshot_dir> <team.json>
Writes <snapshot_dir>/report/case1_report.html, so the report's relative image paths keep working.
1 CSS px = 1 pt: the page is 595 x 842 px (A4); paginate.js later splits the flow into pages."""
import html
import json
import re
import sys
from pathlib import Path

SNAP, TEAM = Path(sys.argv[1]), Path(sys.argv[2])
OUT = SNAP / "report" / "case1_report.html"
team = json.loads(TEAM.read_text(encoding="utf-8"))
toc = []  # (level, number, title, id) in reading order
figures = []  # (label, title, id) of every captioned figure, for the list of figures
refs = []  # reference list entries of both parts, merged into one list at the end

CSS = """
html { font-size: 11px; }
body { width: 595px; box-sizing: border-box; padding: 64px 72px 0; margin: 0; position: relative;
       font-family: Charter, Georgia, serif; font-size: 1rem; line-height: 1.45; color: #1d1d1d; background: #fff; }
h1, h2, h3, table, figcaption, .tcap, .toc, .uni, .team, .date, .prompt, .pnum-sans { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
h1 { font-size: 1.75rem; font-weight: 500; line-height: 1.2; margin: 0 0 1.3rem; padding: 0.1rem 0 0.1rem 0.65rem; border-left: 4px solid #84b819; }
h2 { font-size: 1.22rem; font-weight: 500; line-height: 1.25; margin: 1.7rem 0 0.6rem; }
h3 { font-size: 1.05rem; font-weight: 500; margin: 1.3rem 0 0.4rem; }
h2.plain { font-size: 1.05rem; color: #4d6f12; }
.num { color: #4d6f12; }
p { margin: 0 0 0.7rem; }
ul, ol { margin: 0 0 0.8rem; padding-left: 1.3rem; }
li { margin: 0.22rem 0; }
li > ul, li > ol { margin: 0.2rem 0 0; }
code { font-family: Menlo, monospace; font-size: 0.8em; background: #f3f6ec; padding: 0 0.2em; }
a { color: #4d6f12; text-decoration: none; }
figure { margin: 1rem 0 1.2rem; text-align: center; }
figure img { max-width: 100%; }
figure.fig-part2_confusion img, figure.fig-part2_roc img { max-width: 65%; }
figure.fig-part1_b2_comparison img { max-width: 80%; }
figcaption { font-size: 0.86rem; line-height: 1.35; color: #444; text-align: left; margin-top: 0.45rem; }
figcaption strong, .tcap strong { color: #4d6f12; font-weight: 500; }
table { border-collapse: collapse; width: 100%; font-size: 0.8rem; line-height: 1.3; margin: 0.4rem 0 1.1rem; }
th { background: #f1f6e6; font-weight: 500; text-align: left; }
th, td { border-bottom: 0.5px solid #cdd7b8; padding: 0.28rem 0.45rem; vertical-align: top; }
.tcap { font-size: 0.86rem; margin: 1.1rem 0 0.25rem; }
.front .band { position: absolute; top: 0; left: 0; width: 595px; height: 14px; background: #84b819; }
.front .uni { font-size: 0.92rem; line-height: 1.45; color: #555; margin-top: 0.4rem; }
.front h1.title { font-size: 2.45rem; line-height: 1.12; border: 0; padding: 0; margin: 11rem 0 0; }
.front .subtitle { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 1.45rem; color: #4d6f12; margin: 0.45rem 0 0; }
.front .rule { width: 3.6rem; height: 3px; background: #84b819; margin: 1.4rem 0 1.1rem; }
.front .course { font-size: 1.12rem; line-height: 1.55; margin-bottom: 0.9rem; }
.front table.staff { width: auto; font-size: 0.95rem; margin: 0; }
.front table.staff td { border: 0; padding: 0.12rem 1.4rem 0.12rem 0; }
.front table.staff td:first-child { color: #666; }
.front table.team { width: 75%; font-size: 0.95rem; margin-top: 7rem; }
.front table.team.wide { width: 100%; }
.front .repo { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 0.92rem; color: #555; margin-top: 1.3rem; }
.toc h1 { border: 0; padding: 0; }
.toc h2.lof { font-size: 1.22rem; margin: 2.2rem 0 0.4rem; }
.toc .lf { font-size: 0.95rem; }
.toc .lf .tnum { min-width: 5.4rem; }
ul.refs { list-style: none; padding-left: 0; }
ul.refs li { padding-left: 1.6em; text-indent: -1.6em; margin: 0 0 0.6rem; }
.toc .entry { display: flex; align-items: baseline; margin: 0.32rem 0; }
.toc .entry a { color: #1d1d1d; }
.toc .l1 { font-weight: 500; margin-top: 1rem; }
.toc .l2 { margin-left: 2.1rem; font-size: 0.95rem; }
.toc .tnum { color: #4d6f12; display: inline-block; min-width: 2.1rem; }
.toc .fill { flex: 1; border-bottom: 1px dotted #9a9a96; margin: 0 0.45rem; position: relative; top: -0.28rem; }
.nbnote { font-size: 0.9rem; color: #555; }
.prompt { font-size: 0.7rem; color: #4d6f12; margin: 0.8rem 0 0.15rem; }
pre { font-family: Menlo, monospace; font-size: 0.72rem; line-height: 1.38; white-space: pre-wrap; word-wrap: break-word; margin: 0; }
pre.code { background: #f6f8f1; border-left: 2px solid #84b819; padding: 0.45rem 0.6rem; }
pre.code .c { color: #6f7d5c; font-style: italic; }
pre.out { border-left: 2px solid #d8d8d4; padding: 0.3rem 0.6rem; margin: 0.35rem 0 0.6rem; color: #333; }
.out-img { text-align: center; margin: 0.5rem 0 0.9rem; }
.out-img img { max-width: 100%; max-height: 300px; }
.out-html { margin: 0.4rem 0 0.8rem; }
.out-html table { font-size: 0.62rem; margin: 0; border: 0; }
.out-html th, .out-html td { padding: 0.18rem 0.22rem; text-align: right; border: 0; border-bottom: 0.5px solid #cdd7b8; }
.out-html tbody th { background: none; }
.spacer { margin: 0; padding: 0; }
.pnum { position: absolute; left: 0; width: 595px; text-align: center; font-size: 9px; color: #6b6b6b; }
"""


def inline(text):
    """Inline markdown: code spans, bold, italics, links and bare URLs."""
    codes = []

    def keep(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = html.escape(re.sub(r"`([^`]+)`", keep, text), quote=False)
    t = re.sub(r'"([^"<>]+)"', "“\\1”", t)  # typographic quotes and apostrophes (code spans are kept as they are)
    t = re.sub(r"(\w)'(\w)", "\\1’\\2", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r'(?<![">])(https?://[^\s<]+?)(?=[.,;)]?(?:\s|$))', r'<a href="\1">\1</a>', t)
    return re.sub("\x00(\\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))], quote=False)}</code>", t)


def render_list(items, ordered):
    """items = [indent, text] pairs; deeper indents become nested lists."""
    root = {"children": []}
    stack = [(-1, root)]
    for indent, text in items:
        while stack[-1][0] >= indent:
            stack.pop()
        node = {"text": text, "children": []}
        stack[-1][1]["children"].append(node)
        stack.append((indent, node))
    tag = "ol" if ordered else "ul"

    def emit(nodes):
        return f"<{tag}>" + "".join(
            f"<li>{inline(n['text'])}{emit(n['children']) if n['children'] else ''}</li>" for n in nodes) + f"</{tag}>"

    return emit(root["children"])


BLOCK_START = re.compile(r"^(#{1,3}\s|!\[|\s*\||\s*(?:[-*]|\d+\.)\s+)")


def md_blocks(md, number=None):
    """Markdown -> HTML. With a part number, headings are numbered and listed in the contents;
    without one (notebook cells) every heading becomes a plain h3."""
    lines, out, i, sec = md.split("\n"), [], 0, 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if number is None:
                out.append(f"<h3>{inline(text)}</h3>")
            elif level == 1:
                title = re.sub(r"^Part \d+\s*[–-]\s*", "", text)
                out.append(f'<h1 id="part{number}"><span class="num">{number}</span> {inline(title)}</h1>')
                toc.append((1, str(number), title, f"part{number}"))
            elif level == 2 and text.lower() != "references":
                sec += 1
                hid = f"s{number}-{sec}"
                out.append(f'<h2 id="{hid}"><span class="num">{number}.{sec}</span> {inline(text)}</h2>')
                toc.append((2, f"{number}.{sec}", text, hid))
            else:
                out.append(f'<h{level} class="plain">{inline(text)}</h{level}>')
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line.strip())
        if m:  # image, with the following "**Figure ..." paragraph as its caption
            i += 1
            while i < n and not lines[i].strip():
                i += 1
            cap = []
            if i < n and lines[i].startswith("**Figure"):
                while i < n and lines[i].strip():
                    cap.append(lines[i].strip())
                    i += 1
            caption = f"<figcaption>{inline(' '.join(cap))}</figcaption>" if cap else ""
            fid = f"fig-{Path(m.group(2)).stem}"
            label, _, title = m.group(1).partition(" – ")
            if number is not None and label.startswith("Figure"):
                figures.append((label, title or label, fid))
            out.append(f'<figure id="{fid}" class="{fid}"><img src="{m.group(2)}" alt="{html.escape(m.group(1))}">{caption}</figure>')
            continue
        if line.lstrip().startswith("|"):
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[2:]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+", line)
        if m:
            ordered, items = m.group(2)[0].isdigit(), []
            while i < n and lines[i].strip():
                mm = re.match(r"^(\s*)(?:[-*]|\d+\.)\s+(.*)", lines[i])
                if mm:
                    items.append([len(mm.group(1)), mm.group(2)])
                else:
                    items[-1][1] += " " + lines[i].strip()
                i += 1
            out.append(render_list(items, ordered))
            continue
        para = []
        while i < n and lines[i].strip() and not BLOCK_START.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        nxt = i
        while nxt < n and not lines[nxt].strip():
            nxt += 1
        is_table_caption = text.startswith("**Table") and nxt < n and lines[nxt].lstrip().startswith("|")
        out.append(f'<p class="tcap">{inline(text)}</p>' if is_table_caption else f"<p>{inline(text)}</p>")
    return "\n".join(out)


def split_comment(line):
    quote = None
    for k, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "#":
            return line[:k], line[k:]
    return line, ""


def code_html(src):
    rows = []
    for line in src.split("\n"):
        code, comment = split_comment(line)
        rows.append(html.escape(code, quote=False)
                    + (f'<span class="c">{html.escape(comment, quote=False)}</span>' if comment else ""))
    return "\n".join(rows)


def joined(v):
    return "".join(v) if isinstance(v, list) else v


def notebook_html(path):
    """Every cell part (prompt, code, output) is its own top-level block, so the paginator can place each one."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for c in nb["cells"]:
        src = joined(c["source"])
        if c["cell_type"] == "markdown":
            out.append(md_blocks(src))
            continue
        if c["cell_type"] != "code":
            continue
        count = c.get("execution_count")
        out.append(f'<div class="prompt">In [{count if count else "&nbsp;"}]</div>')
        out.append(f'<pre class="code">{code_html(src)}</pre>')
        stdout = []  # consecutive prints are shown as one block

        def flush():
            if stdout:
                out.append(f'<pre class="out">{html.escape("".join(stdout).strip(chr(10)), quote=False)}</pre>')
                stdout.clear()

        for o in c.get("outputs", []):
            kind = o["output_type"]
            if kind == "stream":
                if o.get("name") != "stderr":  # library warnings are left out
                    stdout.append(joined(o["text"]))
                continue
            flush()
            if kind in ("execute_result", "display_data"):
                data = o["data"]
                if "image/png" in data:
                    out.append(f'<div class="out-img"><img src="data:image/png;base64,{joined(data["image/png"]).strip()}"></div>')
                elif "text/html" in data:
                    out.append(f'<div class="out-html">{joined(data["text/html"])}</div>')
                elif "text/plain" in data:
                    out.append(f'<pre class="out">{html.escape(joined(data["text/plain"]), quote=False)}</pre>')
            elif kind == "error":
                out.append(f'<pre class="out">{html.escape(o["ename"] + ": " + o["evalue"], quote=False)}</pre>')
        flush()
    return "\n".join(out)


def front():
    # members: [name, matriculation number, email]; a column is shown only if it is filled in for everyone
    members = [list(m) + [""] * (3 - len(m)) for m in team["members"]]
    show_number, show_email = all(m[1] for m in members), all(m[2] for m in members)
    head = ("<th>Name</th>" if show_number or show_email else "<th>Team</th>") \
        + ("<th>Matriculation number</th>" if show_number else "") + ("<th>Email</th>" if show_email else "")
    rows = "".join(
        f"<tr><td>{html.escape(name)}</td>"
        + (f"<td>{html.escape(number)}</td>" if show_number else "")
        + (f'<td><a href="mailto:{html.escape(email)}">{html.escape(email)}</a></td>' if show_email else "")
        + "</tr>" for name, number, email in members)
    repo = team.get("repo", "")
    repo_line = (f'<p class="repo">Repository: <a href="{html.escape(repo)}">{html.escape(repo.removeprefix("https://"))}</a></p>'
                 if repo else "")
    return f"""<section class="front">
<div class="band"></div>
<p class="uni">TU Dortmund University<br>Department of Computer Science · Chair of Enterprise Computing</p>
<h1 class="title">{html.escape(team["title"])}</h1>
<p class="subtitle">{html.escape(team["subtitle"])}</p>
<div class="rule"></div>
<p class="course">{html.escape(team["course"])}<br>{html.escape(team["term"])}</p>
<table class="staff"><tr><td>Lecturer</td><td>{html.escape(team["lecturer"])}</td></tr>
<tr><td>Exercise instructor</td><td>{html.escape(team["instructor"])}</td></tr></table>
<table class="team{" wide" if show_email else ""}"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>
{repo_line}
</section>"""


def contents():
    def entry(cls, num, title, target):
        return (f'<div class="entry {cls}"><a href="#{target}"><span class="tnum">{html.escape(num)}</span> {inline(title)}</a>'
                f'<span class="fill"></span><span class="pg"></span></div>')

    rows = "".join(entry(f"l{level}", num, title, hid) for level, num, title, hid in toc)
    figs = "".join(entry("lf", label, title, fid) for label, title, fid in figures)
    return f'<section class="toc"><h1>Contents</h1>{rows}<h2 class="lof">List of figures</h2>{figs}</section>'


def body_and_refs(path):
    """Split off the "## References" section; its entries go into the one merged reference list."""
    body, _, tail = path.read_text(encoding="utf-8").partition("\n## References")
    refs.extend(line[2:].strip() for line in tail.splitlines() if line.startswith("- "))
    return body


part1 = md_blocks(body_and_refs(SNAP / "report/part1_playground.md"), 1)
part2 = md_blocks(body_and_refs(SNAP / "report/part2_classifier.md"), 2)
toc.append((1, "", "References", "refs"))
references = "".join(f"<li>{inline(r)}</li>" for r in sorted(set(refs), key=str.lower))
toc.append((1, "A", "Appendix: Jupyter notebook", "appendix"))
notebook = notebook_html(SNAP / "notebooks/cats_vs_dogs_classifier.ipynb")

OUT.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(team["title"])} – {html.escape(team["subtitle"])}</title>
<meta name="author" content="{html.escape(", ".join(m[0] for m in team["members"]))}">
<meta name="subject" content="{html.escape(team["course"])}, {html.escape(team["term"])}"><style>{CSS}</style></head>
<body>
{front()}
{contents()}
<section class="part">{part1}</section>
<section class="part">{part2}</section>
<section class="part"><h1 id="refs">References</h1><ul class="refs">{references}</ul></section>
<section class="part"><h1 id="appendix"><span class="num">A</span> Appendix: Jupyter notebook</h1>
<p class="nbnote">Rendered from <code>notebooks/cats_vs_dogs_classifier.ipynb</code> in the team repository, with the outputs as saved.
The experiment cell (In [ ]) keeps the outputs of the training run that produced <code>results/*.json</code>; the other cells were re-run afterwards.
Warnings printed by libraries are left out.</p>
{notebook}
</section>
</body></html>""", encoding="utf-8")
print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB,", len(toc), "contents entries")
