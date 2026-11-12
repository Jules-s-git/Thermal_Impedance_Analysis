"""Build the whole documentation as one PDF: docs/Zth_to_Foster_documentation.pdf.

Usage, from anywhere (needs pandoc and XeLaTeX):

    python thermal_analysis/docs/_scripts/make_pdf.py

Joins the pages in reading order, numbers them as sections, turns the links
between pages into links inside the PDF, uses the italic line under each
figure as its caption, and typesets everything with pandoc and XeLaTeX
(Liberation Serif, DejaVu Sans Mono, Latin Modern Math), in the layout of
the documentation of the KiCad/Icepak project.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import tempfile

DOCS = pathlib.Path(__file__).resolve().parents[1]
PDF = DOCS / "Thermal_Impedance_Analysis_tool.pdf"
TITLE = "Thermal Impedance Analysis tool"
ORDER = ["README", "installation", "tutorial", "howto", "method", "validation",
         "reference", "differences", "troubleshooting", "references", "api"]
FENCE = re.compile(r"^(```|~~~)")
LINK = re.compile(r"(?<!!)\[((?:[^\]\[]|\[[^\]]*\])*)\]\(([^)\s]+)\)")
IMAGE = re.compile(r"^!\[(.*)\]\(([^)\s]+)\)\s*$")
CAPTION = re.compile(r"^\*(.+)\*\s*$")

HEADER = r"""
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small %s}
\fancyhead[R]{\small\nouppercase{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\sectionmark}[1]{\markboth{#1}{}}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
\usepackage{titlesec}
\newcommand{\sectionbreak}{\clearpage}
\usepackage{booktabs}
\usepackage{fvextra}
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,breakanywhere,commandchars=\\\{\}}
\RecustomVerbatimEnvironment{verbatim}{Verbatim}{breaklines,breakanywhere}
\renewcommand{\_}{\textunderscore\allowbreak}
\setlength{\emergencystretch}{3em}
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\small}
\usepackage{float}
\floatplacement{figure}{H}
\let\oldtableofcontents\tableofcontents
\renewcommand{\tableofcontents}{\begingroup\renewcommand{\sectionbreak}{}\oldtableofcontents\endgroup\clearpage}
\usepackage{caption}
\captionsetup{font=small}
""" % TITLE


def slug(title: str) -> str:
    title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)
    return re.sub(r"[^\w\- ]", "", title.lower().replace("`", "")).replace(" ", "-")


def fix_link(match, page):
    text, target = match.group(1), match.group(2)
    if re.match(r"^(https?:|mailto:)", target):
        return match.group(0)
    file_part, _, anchor = target.partition("#")
    if file_part and not file_part.endswith(".md"):
        return text  # a file of the project, not a page
    dest = pathlib.Path(file_part).stem if file_part else page
    return f"[{text}](#{dest}--{anchor or 'top'})"


def column_widths(table):
    """Separator line with dashes proportional to the content of each column."""
    rows = [[c.strip() for c in r.strip().strip("|").split("|")]
            for r in table if not re.match(r"^\|[\s:|-]+\|$", r.strip())]
    n = len(rows[0])
    widths = [max(min(len(r[i]) if i < len(r) else 0, 60) for r in rows) for i in range(n)]
    widths = [max(w, 6) for w in widths]
    return "|" + "|".join("-" * w for w in widths) + "|"


def convert(page: str) -> str:
    text = (DOCS / f"{page}.md").read_text(encoding="utf-8")
    if page == "README":
        text = re.sub(r"\n## All pages\n.*?(?=\n## |\Z)", "\n", text, flags=re.S)
        text = text.replace(f"# {TITLE}\n", "# Introduction\n", 1)
    lines, out, fence, seen = text.splitlines(), [], False, {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if FENCE.match(line.strip()):
            fence = not fence
            out.append(line)
            i += 1
            continue
        if fence:
            out.append(line)
            i += 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            s = slug(title)
            title = re.sub(r"^\d+\.\s+", "", title)  # "1. Start the tool": the PDF numbers sections
            n = seen.get(s, 0)
            seen[s] = n + 1
            ident = f"{page}--{s if n == 0 else f'{s}-{n}'}"
            if level == 1:
                ident = f"{page}--top"
            out.append(f"{'#' * level} {LINK.sub(lambda m: m.group(1), title)} {{#{ident}}}")
            i += 1
            continue
        image = IMAGE.match(line)
        if image:
            alt, src = image.groups()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            caption = CAPTION.match(lines[j]) if j < len(lines) else None
            width = "100%" if "gui_" in src else "88%"
            alt = alt.replace('"', "'")
            if caption:
                out.append(f'![{caption.group(1)}]({src}){{width={width} fig-alt="{alt}"}}')
                i = j + 1
            else:
                out.append(f'![{alt}]({src}){{width={width}}}')
                i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            table = []
            while i < len(lines) and lines[i].startswith("|"):
                table.append(lines[i])
                i += 1
            sep = column_widths(table)
            table[1] = sep
            out += [LINK.sub(lambda m: fix_link(m, page), r) for r in table]
            continue
        out.append(LINK.sub(lambda m: fix_link(m, page), line))
        i += 1
    return "\n".join(out)


def main():
    body = "\n\n".join(convert(p) for p in ORDER)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        src = tmp / "all.md"
        src.write_text(body, encoding="utf-8")
        (tmp / "header.tex").write_text(HEADER, encoding="utf-8")
        cmd = [
            "pandoc", str(src), "-f", "gfm+tex_math_dollars+attributes",
            "-o", str(PDF), "--pdf-engine=xelatex", "--resource-path", str(DOCS),
            "--number-sections", "--toc", "--toc-depth=2", "--columns=20",
            "-H", str(tmp / "header.tex"),
            "--lua-filter", str(pathlib.Path(__file__).with_name("table_widths.lua")),
            "--lua-filter", str(pathlib.Path(__file__).with_name("figures.lua")),
            "-M", f"title={TITLE}", "-M", "subtitle=Documentation of the thermal_analysis package",
            "-M", "author=Jules", "-M", "date=October 2026", "-M", "lang=en-GB",
            "-V", "documentclass=article", "-V", "papersize=a4", "-V", "fontsize=11pt",
            "-V", "geometry:margin=2.2cm", "-V", "geometry:top=2.6cm",
            "-V", "mainfont=Liberation Serif", "-V", "monofont=DejaVu Sans Mono",
            "-V", "monofontoptions=Scale=0.85", "-V", "mathfont=Latin Modern Math",
            "-V", "linkcolor=black", "-V", "urlcolor=black", "-V", "toccolor=black",
            "-V", "colorlinks=true",
        ]
        if shutil.which("pandoc") is None:
            raise SystemExit("pandoc not found")
        subprocess.run(cmd, check=True)
    print("written", PDF)


if __name__ == "__main__":
    main()
