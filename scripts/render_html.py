"""Render build/debate.xml to a print-ready HTML document (build/debate.html).

The HTML is the PDF source: WeasyPrint runs it through assets/styles/debate.css.
Everything (header image, fonts, page furniture, table of contents with page
numbers, internal anchors per turn) is plain HTML/CSS, so the same file opens in
a browser and prints to PDF.
"""

from __future__ import annotations

import html
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
ROLE_BG = {"moderator": "водеща", "candidate": "кандидат"}
E = html.escape


def main() -> int:
    root = etree.parse(str(REPO / "build" / "debate.xml")).getroot()
    meta = root.find("d:meta", NS)
    bc = meta.find("d:broadcast", NS)
    src = meta.find("d:source", NS)
    cov = meta.find("d:coverage", NS)
    title = meta.findtext("d:title", namespaces=NS)

    o: list[str] = []
    o.append('<!DOCTYPE html>\n<html lang="bg">\n<head>\n<meta charset="utf-8">\n')
    o.append(f"<title>{E(title)}</title>\n")
    o.append('<link rel="stylesheet" href="../assets/styles/debate.css">\n</head>\n<body>\n')

    # ---------- cover ----------
    credits = [c.text for c in meta.findall("d:credit", NS)]
    o.append('<section class="cover">\n')
    o.append('<img src="../assets/images/debate-header.png" alt="Илияна Йотова и Андрей Гюров в студиото на БНТ">\n')
    o.append('<div class="inner">\n')
    months = ["", "януари", "февруари", "март", "април", "май", "юни",
              "юли", "август", "септември", "октомври", "ноември", "декември"]
    y, m, d = (int(x) for x in bc.get("date").split("-"))
    pretty_date = f"{d} {months[m]} {y} г."
    o.append(f'<p class="kicker">{E(bc.get("channel"))} · {E(pretty_date)}</p>\n')
    o.append(f"<h1>Дебат за президент:<br>Илияна Йотова – Андрей Гюров</h1>\n")
    o.append('<p class="sub">Структуриран препис с атрибуция на говорителите</p>\n')
    o.append('<p class="credit">Кадър: БНТ, излъчване на 29.10.2026 г. '
             'Изображението е публикувано от flagman.bg и се използва с цел илюстрация. '
             f'Покритие: {E(cov.get("from"))}–{E(cov.get("to"))} · {E(cov.get("turns"))} реплики.</p>\n')
    o.append("</div>\n</section>\n")

    # ---------- front matter ----------
    o.append('<section class="front">\n<h2 id="about">За документа</h2>\n<div class="notice"><ul>\n')
    for d in meta.findall("d:disclaimer", NS):
        o.append(f"<li>{E(d.text)}</li>\n")
    o.append("</ul>\n")
    o.append("</div>\n")
    o.append('<p class="legend"><span class="flag">⧉</span> едновременна реч · '
             '<span class="flag">↳</span> репликата прекъсва предишна · '
             'намесите на други говорители са в курсив и са оградени с вертикална линия.</p>\n')

    o.append('<table class="people">\n<thead><tr><th>Роля</th><th>Име</th><th>Бележка</th></tr></thead>\n<tbody>\n')
    for p in meta.findall("d:participants/d:person", NS):
        o.append(f'<tr><td>{ROLE_BG[p.get("role")]}</td><td><strong>{E(p.get("name"))}</strong></td>'
                 f'<td>{E(p.get("note") or "")}</td></tr>\n')
    o.append("</tbody>\n</table>\n")

    o.append(f'<p class="range">Източник: {E(src.get("engine"))} · '
             f'<a href="{E(src.get("url"))}">gist на BorisThoris</a> · '
             f'sha256 {E(src.get("sha256")[:16])}…</p>\n')

    sections = root.findall("d:body/d:section", NS)
    o.append('<nav class="toc">\n<h2 id="toc">Съдържание</h2>\n<ol>\n')
    for i, sec in enumerate(sections, 1):
        if sec.get("status") == "planned":
            o.append(f'<li class="planned"><span>{i}. {E(sec.get("title"))}</span><span class="t">—</span></li>\n')
        else:
            o.append(f'<li><a href="#{sec.get("id")}">{i}. {E(sec.get("title"))}</a>'
                     f'<span class="t">{E(sec.get("from"))}</span></li>\n')
    o.append("</ol>\n</nav>\n</section>\n")

    # ---------- transcript ----------
    for i, sec in enumerate(sections, 1):
        turns = sec.findall("d:turn", NS)
        if not turns:
            continue
        o.append(f'<section class="section" id="{sec.get("id")}">\n')
        o.append(f'<h2>{i}. {E(sec.get("title"))}</h2>\n')
        o.append(f'<p class="range">{E(sec.get("from"))} – {E(sec.get("to"))}</p>\n')

        for turn in turns:
            flags = ""
            if turn.get("overlap") == "true":
                flags += '<span class="flag" title="едновременна реч">⧉</span>'
            if turn.get("interrupts"):
                flags += '<span class="flag" title="прекъсва предишна реплика">↳</span>'
            o.append(f'<article class="turn" id="{turn.get("id")}">\n')
            o.append(f'<p class="speaker"><span class="who">{LABELS[turn.get("speaker")]}</span>'
                     f'<span class="when">{E(turn.get("start"))}</span>{flags}</p>\n')
            for node in turn.find("d:text", NS):
                if node.tag.endswith("aside"):
                    body = " ".join(t.text or "" for t in node.findall("d:p", NS))
                    o.append('<blockquote class="aside">'
                             f'<span class="who">{LABELS[node.get("speaker")]} · {E(node.get("start"))}</span>'
                             f'<p>{E(body)}</p></blockquote>\n')
                else:
                    o.append(f'<p>{E(node.text or "")}</p>\n')
            o.append("</article>\n")
        o.append("</section>\n")

    # ---------- appendix ----------
    o.append('<section class="appendix" id="appendix">\n<h2>Приложение</h2>\n')

    gaps = root.findall(".//d:gaps/d:gap", NS)
    if gaps:
        o.append("<h3>Пропуски в записа</h3>\n<ul>\n")
        for g in gaps:
            o.append(f'<li><strong>{E(g.get("from"))}–{E(g.get("to"))}</strong> — {E(g.get("reason"))}</li>\n')
        o.append("</ul>\n")

    ambs = root.findall(".//d:ambiguities/d:ambiguity", NS)
    if ambs:
        o.append("<h3>Двусмислени места</h3>\n<p>Места, в които атрибуцията не е еднозначна. Показани са времето, "
                 "цитатът и решението; <em>отворено</em> значи, че въпросът остава за проверка.</p>\n")
        o.append('<ul class="amb">\n')
        for a in ambs:
            st = a.get("status")
            badge = '<span class="badge open">отворено</span>' if st == "open" else ""
            o.append(f'<li><span class="t">{E(a.get("time") or "")}</span> '
                     f'<span class="cues">ред {E(a.get("cues"))}</span> {badge}\n')
            if a.get("quote"):
                o.append(f'<blockquote class="q">{E(a.get("quote"))}</blockquote>\n')
            q = a.findtext("d:question", namespaces=NS)
            if q:
                o.append(f'<p class="ask">{E(q)}</p>\n')
            for r in a.findall("d:reading", NS):
                o.append(f'<p class="reading">— {E(r.text)}</p>\n')
            res = a.findtext("d:resolution", namespaces=NS)
            if res:
                o.append(f'<p class="res"><strong>Решение:</strong> {E(res)}</p>\n')
            o.append("</li>\n")
        o.append("</ul>\n")

    unclear = root.findall(".//d:unclear/d:unclear", NS)
    if unclear:
        o.append("<h3>Неясни места</h3>\n<p>Тези пасажи не са поправени: в машинния препис звучат неразбираемо.</p>\n<table class=\"corr\">\n")
        o.append("<thead><tr><th>ред</th><th>в преписа</th><th>защо остава неясно</th></tr></thead>\n<tbody>\n")
        for u in unclear:
            o.append(f'<tr><td>{E(u.get("n"))}</td><td>«{E(u.get("text"))}»</td><td>{E(u.get("why"))}</td></tr>\n')
        o.append("</tbody></table>\n")

    corrections = root.findall(".//d:corrections/d:correction", NS)
    if corrections:
        o.append("<h3>Поправки на разпознаването</h3>\n<p>Оригиналните форми от машинния препис; в текста е поправеното.</p>\n")
        o.append('<table class="corr">\n<thead><tr><th>ред</th><th>в преписа</th><th>поправено</th><th>основание</th></tr></thead>\n<tbody>\n')
        for c in corrections:
            o.append(f'<tr><td>{E(c.get("n"))}</td><td>{E(c.get("original"))}</td>'
                     f'<td>{E(c.get("corrected"))}</td><td>{E(c.get("why"))}</td></tr>\n')
        o.append("</tbody></table>\n")

    conv = meta.find("d/conventions", NS)
    if conv is not None:
        o.append('<div class="conventions"><h3>Как е направен текстът</h3><ul>\n')
        for r in conv.findall("d:rule", NS):
            o.append(f"<li>{E(r.text)}</li>\n")
        o.append("</ul></div>\n")

    o.append("</section>\n</body>\n</html>\n")

    dst = REPO / "build" / "debate.html"
    dst.write_text("".join(o), encoding="utf-8")
    print(f"wrote {dst.relative_to(REPO)} ({len(''.join(o))} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
