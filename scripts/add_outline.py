"""Add a PDF outline (bookmarks) to build/debate.pdf.

Chrome cannot generate a PDF outline, so we add it afterwards with pypdf:
sections become top-level bookmarks, individual turns become children with their
start time and speaker. Internal links were already preserved by Chrome; this
adds the navigation pane and makes the document usable in a PDF reader.

The page for each bookmark is found by searching the extracted page text — the
HTML puts "Speaker 0:31:09" at the start of every turn, so the label+time pair is
a reliable locator.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from lxml import etree
from pypdf import PdfReader, PdfWriter

REPO = Path(__file__).resolve().parent.parent
NS = {"d": "urn:debate:2026"}
LABELS = {
    "moderator": "Поли Златарева",
    "yotova": "Илияна Йотова",
    "gyurov": "Андрей Гюров",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    pdf_path = REPO / "build" / "debate.pdf"
    xml_path = REPO / "build" / "debate.xml"
    if not pdf_path.exists() or not xml_path.exists():
        print("build/debate.pdf or build/debate.xml missing; run make pdf first")
        return 1

    root = etree.parse(str(xml_path)).getroot()
    reader = PdfReader(str(pdf_path))
    pages = [norm(p.extract_text() or "") for p in reader.pages]
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    def find(text: str) -> int | None:
        for i, page in enumerate(pages):
            if text in page:
                return i
        return None

    sections = root.findall("d:body/d:section", NS)
    added = 0
    for i, sec in enumerate(sections, 1):
        if sec.get("status") == "planned":
            continue
        title = f"{i}. {sec.get('title')}"
        page = find(norm(title))
        if page is None:
            print(f"  ! section not found: {title}")
            continue
        parent = writer.add_outline_item(title, page)
        added += 1
        for turn in sec.findall("d:turn", NS):
            label = f"{LABELS[turn.get('speaker')]} {turn.get('start')}"
            p = find(label)
            if p is None:
                continue
            writer.add_outline_item(f"{turn.get('start')} · {LABELS[turn.get('speaker')]}", p, parent=parent)
            added += 1

    for title in ("За документа", "Приложение"):
        p = find(title)
        if p is not None:
            writer.add_outline_item(title, p)
            added += 1

    tmp = REPO / "build" / "debate.outline.pdf"
    with open(tmp, "wb") as fh:
        writer.write(fh)
    tmp.replace(pdf_path)
    print(f"outline: {added} bookmarks written into {pdf_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
