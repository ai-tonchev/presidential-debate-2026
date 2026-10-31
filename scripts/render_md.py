"""Render build/debate.xml to Markdown (build/debate.md).

The XML already contains the readable text (<text>/<p>), so this renderer only
does layout: speaker labels, timestamps, blockquoted asides, and the apparatus
(disclaimers, participants, gaps, corrections, unclear spots).
"""

from __future__ import annotations

import sys
from pathlib import Path

from lxml import etree

REPO = Path(__file__).resolve().parent.parent
NS = {"d": "urn:debate:2026"}
LABELS = {
    "moderator": "Поли Златарева",
    "yotova": "Илияна Йотова",
    "gyurov": "Андрей Гюров",
}
ROLE_BG = {"moderator": "водеща", "candidate": "кандидат за президент"}


def main() -> int:
    root = etree.parse(str(REPO / "build" / "debate.xml")).getroot()
    meta = root.find("d:meta", NS)
    bc = meta.find("d:broadcast", NS)
    src = meta.find("d:source", NS)
    cov = meta.find("d:coverage", NS)

    out: list[str] = []
    out.append('<img src="assets/images/debate-header.png" alt="Кадър от дебата" width="100%">\n\n')
    out.append(f"# {meta.findtext('d:title', namespaces=NS)}\n\n")
    out.append(f"{bc.get('channel')} · {bc.get('date')} · {cov.get('from')}–{cov.get('to')}\n\n")
    out.append("> **За документа**\n>\n")
    for d in meta.findall("d:disclaimer", NS):
        out.append(f"> - {d.text}\n")
    out.append(f">\n> Източник: [{src.get('url')}]({src.get('url')})  \n")
    for c in meta.findall("d:credit", NS):
        out.append(f"> {c.text}  \n")
    out.append(f"> {src.get('engine')} · sha256 `{src.get('sha256')[:16]}…` · "
               f"покрити редове {cov.get('cues')} ({cov.get('turns')} реплики)\n")

    out.append("\n## Участници\n\n| Роля | Име | Бележка |\n| --- | --- | --- |\n")
    for p in meta.findall("d:participants/d:person", NS):
        out.append(f"| {ROLE_BG[p.get('role')]} | {p.get('name')} | {p.get('note') or ''} |\n")

    footnotes: list[tuple[str, str]] = []

    for sec in root.findall("d:body/d:section", NS):
        turns = sec.findall("d:turn", NS)
        if not turns:
            continue
        out.append(f"\n## {sec.get('title')}\n\n")
        out.append(f"*{sec.get('from')} – {sec.get('to')}*\n")

        for turn in turns:
            tid = turn.get("id")
            head = f"\n**{LABELS[turn.get('speaker')]}** · `{turn.get('start')}`"
            if turn.get("overlap") == "true":
                footnotes.append((f"o{tid}", "Репликите се застъпват — двама говорят едновременно."))
                head += f" [^o{tid}]"
            if turn.get("interrupts"):
                footnotes.append((f"i{tid}", f"Прекъсва реплика {turn.get('interrupts')}."))
                head += f" [^i{tid}]"
            out.append(head + "\n\n")

            text = turn.find("d:text", NS)
            for node in text:
                if node.tag.endswith("aside"):
                    body = " ".join(t.text or "" for t in node.findall("d:p", NS))
                    out.append(f"> *⟪{LABELS[node.get('speaker')]}, {node.get('start')}⟫* {body}\n\n")
                else:
                    out.append((node.text or "").strip() + "\n\n")

    gaps = root.findall(".//d:gaps/d:gap", NS)
    if gaps:
        out.append("\n## Пропуски в записа\n\n")
        for g in gaps:
            out.append(f"- **{g.get('from')}–{g.get('to')}** — {g.get('reason')}\n")

    ambs = root.findall(".//d:ambiguities/d:ambiguity", NS)
    if ambs:
        out.append("\n## Двусмислени места\n\n")
        for a in ambs:
            st = " *(отворено)*" if a.get("status") == "open" else ""
            out.append(f"**{a.get('time') or ''}** · ред {a.get('cues')}{st}  \n")
            if a.get("quote"):
                out.append(f"> {a.get('quote')}\n\n")
            out.append(f"*{a.findtext('d:question', namespaces=NS)}*\n\n")
            for r in a.findall("d:reading", NS):
                out.append(f"- {r.text}\n")
            res = a.findtext("d:resolution", namespaces=NS)
            if res:
                out.append(f"- **Решение:** {res}\n")
            out.append("\n")

    corrections = root.findall(".//d:corrections/d:correction", NS)
    if corrections:
        out.append("\n## Поправки на разпознаването\n\n")
        out.append("Оригиналните форми от машинния препис са запазени тук; в текста горе е поправеното.\n\n")
        out.append("| ред | в преписа | поправено | основание |\n| --- | --- | --- | --- |\n")
        for c in corrections:
            out.append(f"| {c.get('n')} | {c.get('original')} | {c.get('corrected')} | {c.get('why')} |\n")

    unclear = root.findall(".//d:unclear/d:unclear", NS)
    if unclear:
        out.append("\n## Неясни места\n\n")
        out.append("Тези пасажи не са поправени — чуват се неразбираемо в машинния препис.\n\n")
        for u in unclear:
            out.append(f"- ред {u.get('n')}: «{u.get('text')}» — {u.get('why')}\n")

    if footnotes:
        out.append("\n---\n\n")
        for key, txt in footnotes:
            out.append(f"[^{key}]: {txt}\n")

    dst = REPO / "build" / "debate.md"
    dst.write_text("".join(out), encoding="utf-8")
    print(f"wrote {dst.relative_to(REPO)} ({len(''.join(out))} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
