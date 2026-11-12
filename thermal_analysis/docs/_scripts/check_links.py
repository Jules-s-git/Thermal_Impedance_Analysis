"""Check the links of the documentation.

Usage, from anywhere:

    python thermal_analysis/docs/_scripts/check_links.py

Checks every Markdown link and image in README.md and docs/*.md: the target
file must exist and, for a link with #anchor, the target page must have a
heading with that anchor (GitHub rules). External links (http, https,
mailto) are not checked. Exits with status 1 if a link is broken.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parent
LINK = re.compile(r"!?\[(?:[^\]\[]|\[[^\]]*\])*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~)")


def strip_code(text):
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def anchors(path):
    seen, result = {}, set()
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line.strip()):
            in_fence = not in_fence
        if in_fence or not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)
        slug = re.sub(r"[^\w\- ]", "", title.lower().replace("`", "")).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        result.add(slug if n == 0 else f"{slug}-{n}")
    return result


def main():
    pages = [ROOT / "README.md", *sorted(DOCS.glob("*.md"))]
    errors = 0
    for page in pages:
        if not page.exists():
            continue
        for target in LINK.findall(strip_code(page.read_text(encoding="utf-8"))):
            if re.match(r"^(https?:|mailto:)", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (page.parent / file_part).resolve() if file_part else page
            if not dest.exists():
                print(f"{page.relative_to(ROOT)}: missing file {target}")
                errors += 1
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                print(f"{page.relative_to(ROOT)}: missing heading {target}")
                errors += 1
    print(f"{len(pages)} pages checked, {errors} broken link(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
