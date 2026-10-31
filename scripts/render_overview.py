"""Build the overview document: build/overview.md and build/overview.html.

Two kinds of content, kept apart:

* editorial summaries come from data/overview.yml (interpretation);
* every number, quote and time is computed here from build/debate.xml and the raw
  cue timings — so the overview can never drift from the transcript.

The numbers are estimates and say so in the document: speaking time is derived
from cue start times (a cue lasts until the next cue starts, capped), overlapping
speech is counted once for the cue's owner, and only the covered part of the
recording is measured.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import yaml
from lxml import etree

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from transcript import fmt_tc, load_cues  # noqa: E402

NS = {"d": "urn:debate:2026"}
LABELS = {"moderator": "Поли Златарева", "yotova": "Илияна Йотова", "gyurov": "Андрей Гюров"}
SHORT = {"moderator": "водеща", "yotova": "Йотова", "gyurov": "Гюров"}
CANDIDATES = ("yotova", "gyurov")
KIND_BG = {"time_call": "време", "procedure": "процедура", "prompt": "подкана",
           "interjection": "намеса", "question": "въпрос", "transition": "ред"}
CAP = 12  # a cue lasts at most this long, in seconds


def text_of(node) -> str:
    return " ".join((p.text or "") for p in node.findall("d:p", NS))


def main() -> int:
    _h, cues = load_cues()
    root = etree.parse(str(REPO / "build" / "debate.xml")).getroot()
    ed = yaml.safe_load(open(REPO / "data" / "overview.yml", encoding="utf-8"))

    sections = root.findall("d:body/d:section", NS)

    # ---- cue attribution and durations ---------------------------------------
    aside_cues: set[int] = set()
    cue_owner: dict[int, str] = {}
    for turn in root.findall(".//d:turn", NS):
        for a in turn.findall("d:text/d:aside", NS):
            for seg in a.findall("d:p", NS):
                pass
            aside_cues.add(int(a.get("cue")))
    for turn in root.findall(".//d:turn", NS):
        for seg in turn.findall("d:source/d:seg", NS):
            n = int(seg.get("n"))
            if n not in aside_cues:
                cue_owner[n] = turn.get("speaker")

    order = sorted(cues)
    dur: dict[int, int] = {}
    for i, n in enumerate(order):
        nxt = cues[order[i + 1]].sec if i + 1 < len(order) else cues[n].sec + 5
        dur[n] = max(1, min(nxt - cues[n].sec, CAP))

    speaking = {k: 0 for k in ("moderator", "yotova", "gyurov")}
    for n, owner in cue_owner.items():
        speaking[owner] += dur[n]

    # ---- per-turn stats -------------------------------------------------------
    turn_rows = []
    for turn in root.findall(".//d:turn", NS):
        words = len(text_of(turn.find("d:text", NS)).split())
        first = int(turn.get("start").split(":")[0]) * 3600 + int(turn.get("start").split(":")[1]) * 60 + int(turn.get("start").split(":")[2])
        spans = [int(s.get("n")) for s in turn.findall("d:source/d:seg", NS)]
        t_dur = sum(dur[n] for n in spans if n not in aside_cues)
        turn_rows.append({"turn": turn, "words": words, "sec": t_dur, "start": first})

    by = {k: {"turns": [], "words": 0, "sec": 0} for k in ("moderator", "yotova", "gyurov")}
    for r in turn_rows:
        sp = r["turn"].get("speaker")
        by[sp]["turns"].append(r)
        by[sp]["words"] += r["words"]
        by[sp]["sec"] += r["sec"]

    total_words = sum(v["words"] for v in by.values())
    total_sec = sum(v["sec"] for v in by.values())

    # ---- moderator interventions ---------------------------------------------
    events = []
    for turn in root.findall(".//d:turn", NS):
        for a in turn.findall("d:text/d:aside", NS):
            if a.get("speaker") != "moderator":
                continue
            events.append({
                "time": a.get("start"), "target": turn.get("speaker"),
                "kind": a.get("kind"), "text": text_of(a),
                "where": f"{turn.get('id')} (вложена)", "overlap": a.get("overlap") == "true",
            })

    # standalone time calls right after a candidate turn
    turns = root.findall(".//d:turn", NS)
    for prev, cur in zip(turns, turns[1:]):
        if cur.get("speaker") == "moderator" and cur.get("kind") == "time_call" and prev.get("speaker") in CANDIDATES:
            events.append({
                "time": cur.get("start"), "target": prev.get("speaker"),
                "kind": "time_call", "text": text_of(cur.find("d:text", NS)),
                "where": cur.get("id"), "overlap": False,
            })
    events.sort(key=lambda e: e["time"])

    per_target = {c: [e for e in events if e["target"] == c] for c in CANDIDATES}

    # ---- interruptions between the candidates --------------------------------
    cross = []
    for turn in turns:
        if turn.get("interrupts") and turn.get("speaker") in CANDIDATES:
            victim = turn.get("interrupts")
            v = root.xpath(f"//d:turn[@id='{victim}']", namespaces=NS)
            if v and v[0].get("speaker") in CANDIDATES:
                cross.append({"time": turn.get("start"), "by": turn.get("speaker"),
                              "victim": v[0].get("speaker"), "turn": turn.get("id"),
                              "victim_turn": victim, "text": text_of(turn.find("d:text", NS))[:90],
                              "confidence": turn.get("confidence")})

    # ---- render markdown ------------------------------------------------------
    def mmss(s: int) -> str:
        return f"{s // 60}:{s % 60:02d}"

    cov = root.find("d:meta/d:coverage", NS)
    cov_from, cov_to = (cov.get("from"), cov.get("to")) if cov is not None else ("?", "?")

    out = []
    out.append("# Обзор на дебата\n\n")
    out.append("**Илияна Йотова – Андрей Гюров · БНТ · 29.10.2026**\n\n")
    out.append(f"Анализът се отнася за {mmss(total_sec)} разговор във вече обработената част "
               f"от дебата ({cov_from}–{cov_to}).\n\n")
    out.append(ed["intro"].strip() + "\n\n")

    out.append("## 1. Структура на дебата\n\n")
    out.append("| № | Раздел | Време | Реплики | Думи |\n| --- | --- | --- | --- | --- |\n")
    for i, sec in enumerate(sections, 1):
        ts = sec.findall("d:turn", NS)
        if not ts:
            out.append(f"| {i} | {sec.get('title')} (не е обработен) | {sec.get('from')}–{sec.get('to')} | — | — |\n")
            continue
        w = sum(len(text_of(t.find("d:text", NS)).split()) for t in ts)
        out.append(f"| {i} | {sec.get('title')} | {sec.get('from')}–{sec.get('to')} | {len(ts)} | {w} |\n")

    out.append("\n## 2. Аргументите по теми\n")
    for item in ed["sections"]:
        sec = root.xpath(f"//d:section[@id='{item['id']}']", namespaces=NS)
        title = sec[0].get("title") if sec else item["id"]
        out.append(f"\n### {title}\n\n{item['summary'].strip()}\n\n")
        if item.get("yotova"):
            out.append("**Йотова:**\n\n")
            for c in item["yotova"]:
                out.append(f"- {c}\n")
        if item.get("gyurov"):
            out.append("\n**Гюров:**\n\n")
            for c in item["gyurov"]:
                out.append(f"- {c}\n")
        if item.get("clash"):
            out.append(f"\n**Сблъсъкът:** {item['clash'].strip()}\n")

    out.append("\n## 3. Кой колко говори\n\n")
    out.append("| | Реплики | Думи | Време с думата (прибл.) | Дял от думите |\n| --- | --- | --- | --- | --- |\n")
    for k in ("moderator", "yotova", "gyurov"):
        v = by[k]
        out.append(f"| {LABELS[k]} | {len(v['turns'])} | {v['words']} | {mmss(v['sec'])} | "
                   f"{100 * v['words'] / total_words:.0f}% |\n")

    out.append("\n## 4. Намеси на водещата\n\n")
    out.append("Броят се само намесите, насочени към кандидат: вложени реплики в рамките на "
               "неговото изказване и отделни напомняния за времето веднага след него. Процедурните "
               "размени, в които водещата говори между двамата кандидати (напр. 0:31:07–0:31:18), "
               "не се броят тук, макар да са част от воденето на дебата.\n\n")
    out.append("| Кандидат | Намеси | От тях за време | На 10 мин. реч |\n| --- | --- | --- | --- |\n")
    for c in CANDIDATES:
        n = len(per_target[c])
        tc = sum(1 for e in per_target[c] if e["kind"] == "time_call")
        rate = n / (by[c]["sec"] / 600) if by[c]["sec"] else 0
        out.append(f"| {LABELS[c]} | {n} | {tc} | {rate:.1f} |\n")

    out.append(f"\nОбщо {len(events)} намеси към двамата кандидати за {mmss(total_sec)} дебат.\n")

    for c in CANDIDATES:
        if not per_target[c]:
            continue
        out.append(f"\n### Намесите към {LABELS[c]}\n\n")
        out.append("| Време | Вид | Текст | Къде |\n| --- | --- | --- | --- |\n")
        for e in per_target[c]:
            out.append(f"| {e['time']} | {KIND_BG.get(e['kind'], e['kind'])} | „{e['text']}“ | {e['where']} |\n")

    out.append("\n## 5. Прекъсвания между кандидатите\n\n")
    if cross:
        out.append("| Време | Кой прекъсва | Кого | Текст (начало) |\n| --- | --- | --- | --- |\n")
        for e in cross:
            mark = " (?)" if e.get("confidence") == "low" else ""
            out.append(f"| {e['time']} | {SHORT[e['by']]}{mark} | {SHORT[e['victim']]} | „{e['text']}…“ |\n")
    else:
        out.append("Няма отбелязани прекъсвания между кандидатите в обработената част.\n")
    out.append("\n«(?)» отбелязва прекъсване, чиято атрибуция е с ниска увереност (вж. amb-a09).\n")

    out.append("\n## 6. Как са изчислени числата\n\n")
    out.append("- Времето с думата се изчислява от началото на всеки ред от преписа до началото на "
               "следващия, с таван от 12 секунди; това е приближение, а не измерване по звук.\n")
    out.append("- При едновременна реч времето се брои на този, на когото е приписан редът, така че "
               "сумата може леко да надхвърля реалното време.\n")
    out.append("- Броят на намесите зависи от атрибуцията: всяка намеса е изброена с време и текст, "
               "за да може да се провери.\n")
    out.append("- Измерена е само обработената част от дебата (секции 1–3). След като бъдат "
               "обработени останалите секции, числата ще се обновят автоматично.\n")

    md = "".join(out)
    (REPO / "build" / "overview.md").write_text(md, encoding="utf-8")

    # ---- render HTML ---------------------------------------------------------
    E = html.escape
    h = []
    h.append('<!DOCTYPE html>\n<html lang="bg">\n<head>\n<meta charset="utf-8">\n')
    h.append('<title>Обзор на дебата Йотова – Гюров</title>\n')
    h.append('<link rel="stylesheet" href="../assets/styles/debate.css">\n')
    h.append("<style>@page{margin:20mm 18mm} .ov h2{page-break-before:auto;margin-top:9mm}"
             ".ov h3{margin-top:6mm;font-size:11.5pt} .ov table{width:100%;border-collapse:collapse;"
             "font-size:8.8pt;margin:3mm 0} .ov th,.ov td{border-bottom:.3pt solid var(--rule);"
             "padding:1.3mm 2mm 1.3mm 0;text-align:left;vertical-align:top}"
             ".ov table.struct td:nth-child(3){white-space:nowrap}"
             ".ov table.struct td:first-child{width:6%}"
             ".ov th{font-family:'Ysabeau';font-size:7.6pt;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}"
             ".ov li{font-size:9.6pt;margin-bottom:1mm} .ov p{font-size:9.8pt}</style>\n")
    h.append("</head>\n<body class=\"ov\">\n")
    h.append('<img src="../assets/images/debate-header.png" alt="" style="width:100%;height:52mm;object-fit:cover;object-position:50% 30%">\n')
    h.append('<div style="padding:8mm 0 0">\n')
    h.append('<p class="kicker" style="font-family:Ysabeau;font-size:8pt;letter-spacing:.16em;text-transform:uppercase;color:#8a1c24">Обзор</p>\n')
    h.append("<h1 style=\"font-family:Ysabeau;font-size:23pt;color:#123a63;margin:2mm 0 2mm\">Дебатът в цифри и аргументи</h1>\n")
    h.append(f'<p class="sub" style="color:#6b6b6b">Илияна Йотова – Андрей Гюров · БНТ · 29.10.2026 · '
             f'анализирани {mmss(total_sec)}</p>\n')
    h.append("</div>\n")

    h.append("<p style=\"font-size:9.6pt\">" + E(" ".join(ed["intro"].split())) + "</p>\n")

    def table(headers, rows, cls=""):
        s = f"<table class=\"{cls}\">\n<thead><tr>" + "".join(f"<th>{E(x)}</th>" for x in headers) + "</tr></thead>\n<tbody>\n"
        for r in rows:
            s += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>\n"
        s += "</tbody></table>\n"
        return s

    h.append("<h2>1. Структура на дебата</h2>\n")
    rows = []
    for i, sec in enumerate(sections, 1):
        ts = sec.findall("d:turn", NS)
        if not ts:
            rows.append([str(i), E(sec.get("title")) + " <em>(не е обработен)</em>",
                         f"{E(sec.get('from'))}–{E(sec.get('to'))}", "—", "—"])
            continue
        w = sum(len(text_of(t.find("d:text", NS)).split()) for t in ts)
        rows.append([str(i), E(sec.get("title")), f"{E(sec.get('from'))}–{E(sec.get('to'))}", str(len(ts)), str(w)])
    h.append(table(["№", "Раздел", "Време", "Реплики", "Думи"], rows, cls="struct"))

    h.append("<h2>2. Аргументите по теми</h2>\n")
    for item in ed["sections"]:
        sec = root.xpath(f"//d:section[@id='{item['id']}']", namespaces=NS)
        title = sec[0].get("title") if sec else item["id"]
        h.append(f"<h3>{E(title)}</h3>\n<p>{E(' '.join(item['summary'].split()))}</p>\n")
        if item.get("yotova"):
            h.append("<p><strong>Йотова:</strong></p>\n<ul>")
            for c in item["yotova"]:
                h.append(f"<li>{E(c)}</li>")
            h.append("</ul>\n")
        if item.get("gyurov"):
            h.append("<p><strong>Гюров:</strong></p>\n<ul>")
            for c in item["gyurov"]:
                h.append(f"<li>{E(c)}</li>")
            h.append("</ul>\n")
        if item.get("clash"):
            h.append(f"<p><strong>Сблъсъкът:</strong> {E(' '.join(item['clash'].split()))}</p>\n")

    h.append("<h2>3. Кой колко говори</h2>\n")
    rows = []
    for k in ("moderator", "yotova", "gyurov"):
        v = by[k]
        rows.append([E(LABELS[k]), str(len(v["turns"])), str(v["words"]),
                     mmss(v["sec"]), f"{100 * v['words'] / total_words:.0f}%"])
    h.append(table(["", "Реплики", "Думи", "Време (прибл.)", "Дял от думите"], rows))

    h.append("<h2>4. Намеси на водещата</h2>\n")
    h.append("<p>Броят се само намесите, насочени към кандидат: вложени реплики в рамките на "
             "неговото изказване и отделни напомняния за времето веднага след него. Процедурните "
             "размени, в които водещата говори между двамата кандидати (напр. 0:31:07–0:31:18), "
             "не се броят тук.</p>\n")
    rows = []
    for c in CANDIDATES:
        n = len(per_target[c])
        tc = sum(1 for e in per_target[c] if e["kind"] == "time_call")
        rate = n / (by[c]["sec"] / 600) if by[c]["sec"] else 0
        rows.append([E(LABELS[c]), str(n), str(tc), f"{rate:.1f}"])
    h.append(table(["Кандидат", "Намеси", "От тях за време", "На 10 мин. реч"], rows))

    h.append(f"<p>Общо {len(events)} намеси към двамата кандидати за {mmss(total_sec)} дебат.</p>\n")

    for c in CANDIDATES:
        if not per_target[c]:
            continue
        h.append(f"<h3>Намесите към {E(LABELS[c])}</h3>\n")
        rows = [[E(e["time"]), E(KIND_BG.get(e["kind"], e["kind"])), f"„{E(e['text'])}“", E(e["where"])] for e in per_target[c]]
        h.append(table(["Време", "Вид", "Текст", "Къде"], rows))

    h.append("<h2>5. Прекъсвания между кандидатите</h2>\n")
    if cross:
        rows = [[E(e["time"]), E(SHORT[e["by"]]) + (" (?)" if e.get("confidence") == "low" else ""),
                 E(SHORT[e["victim"]]), f"„{E(e['text'])}…“"] for e in cross]
        h.append(table(["Време", "Кой прекъсва", "Кого", "Текст (начало)"], rows))
    else:
        h.append("<p>Няма отбелязани прекъсвания между кандидатите в обработената част.</p>\n")

    h.append("<h2>6. Как са изчислени числата</h2>\n<ul>")
    for li in ("Времето с думата се изчислява от началото на всеки ред от преписа до началото на следващия, с таван от 12 секунди.",
               "При едновременна реч времето се брои на този, на когото е приписан редът.",
               "Броят на намесите зависи от атрибуцията; всяка е изброена с време и текст.",
               "Измерена е само обработената част от дебата (секции 1–3)."):
        h.append(f"<li>{E(li)}</li>")
    h.append("</ul>\n")
    h.append("</body>\n</html>\n")

    (REPO / "build" / "overview.html").write_text("".join(h), encoding="utf-8")
    print(f"wrote build/overview.md and build/overview.html")
    print(f"  speaking: " + ", ".join(f"{SHORT[k]} {mmss(v['sec'])}" for k, v in by.items()))
    print(f"  moderator interventions: " + ", ".join(f"{SHORT[c]} {len(per_target[c])}" for c in CANDIDATES))
    print(f"  candidate interruptions: {len(cross)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
