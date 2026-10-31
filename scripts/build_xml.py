"""Build build/debate.xml from the raw transcript + attribution YAML.

Inputs
------
data/debate.yml                 document metadata (title, source, people, disclaimers)
data/attribution/sections.yml   section plan, covering the whole recording
data/attribution/turns/*.yml    hand-verified speaker attribution, cue ranges
data/corrections.yml            ASR corrections, unclear spots, ambiguities, gaps

Guarantees enforced here (fail loudly instead of guessing)
---------------------------------------------------------
* Every turn is contiguous with the previous one in cue-character space.
* A cue is never assigned twice (except deliberate mid-cue splits, where the
  second turn starts exactly where the first one ended).
* Section status is computed, never declared: "complete" only if every
  character of the section is covered by turns.
* Every YAML anchor (`start_at` / `end_at`) must exist exactly once in the cue,
  otherwise the build aborts.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import re

import yaml
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcript import RAW_PATH, load_cues  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NS = "urn:debate:2026"
ASCALE = 100_000


class BuildError(RuntimeError):
    pass


@dataclass
class Seg:
    cue: int
    i: int
    j: int
    text: str
    cue_len: int

    @property
    def start_key(self) -> int:
        return self.cue * ASCALE + self.i

    @property
    def end_key(self) -> int:
        # A segment that runs to the end of its cue ends exactly where the next
        # cue begins, so consecutive cues form a contiguous key space.
        return self.cue * ASCALE + (self.j if self.j < self.cue_len else ASCALE)


def q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def e(parent, tag: str, **attrs):
    node = etree.SubElement(parent, q(tag))
    for k, v in attrs.items():
        if v is None:
            continue
        if isinstance(v, bool):
            v = "true" if v else "false"
        node.set(k, str(v))
    return node


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def slice_cue(cue_text: str, cue_id: int, start_at: str | None, end_at: str | None) -> Seg:
    i, j = 0, len(cue_text)
    if start_at:
        k = cue_text.find(start_at)
        if k < 0:
            raise BuildError(f"cue {cue_id}: start_at {start_at!r} not found")
        if cue_text.find(start_at, k + 1) >= 0:
            raise BuildError(f"cue {cue_id}: start_at {start_at!r} is ambiguous")
        i = k
    if end_at:
        k = cue_text.find(end_at, i)
        if k < 0:
            raise BuildError(f"cue {cue_id}: end_at {end_at!r} not found after offset {i}")
        j = k + len(end_at)
    if i >= j:
        raise BuildError(f"cue {cue_id}: empty slice ({i},{j})")
    return Seg(cue=cue_id, i=i, j=j, text=cue_text[i:j], cue_len=len(cue_text))


def build_segs(spec: dict, cues: dict) -> list[Seg]:
    a, b = (int(x) for x in spec["cues"])
    if a > b:
        raise BuildError(f"{spec.get('id')}: invalid cue range {a}-{b}")
    out: list[Seg] = []
    for n in range(a, b + 1):
        if n not in cues:
            raise BuildError(f"{spec.get('id')}: cue {n} does not exist")
        start_at = spec.get("start_at") if n == a else None
        end_at = spec.get("end_at") if n == b else None
        out.append(slice_cue(cues[n].text, n, start_at, end_at))
    return out


def normalize_aside(a: dict) -> dict:
    if "cues" in a:
        rng = [int(x) for x in a["cues"]]
    else:
        rng = [int(a["cue"]), int(a["cue"])]
    return {**a, "cues": rng}



ABBREV = ("г.", "г-н", "г-жа", "т.е.", "т.н.", "др.", "проф.", "Р.С.", "САЩ.", "бр.", "чл.", "ал.", "с.")


def _protect(text: str) -> str:
    # Only protect an abbreviation at a word boundary: otherwise the final "с."
    # inside a word like "въпрос." would swallow the sentence-ending period.
    for i, a in enumerate(ABBREV):
        text = re.sub(r"(?<![А-Яа-яA-Za-z])" + re.escape(a), f"\x01{i}\x01", text)
    return text


def _unprotect(text: str) -> str:
    for i, a in enumerate(ABBREV):
        text = text.replace(f"\x01{i}\x01", a)
    return text


def _terminal(ch: str) -> bool:
    return ch in ".!?…:;,"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()).strip(" .,!?…:;—")


def assemble(pieces: list[tuple[int, str]], merges: set[tuple[int, int]] | None = None) -> list[str]:
    """Turn ASR cues into readable paragraphs: sentence punctuation by meaning,
    duplicated sentences dropped, sentences grouped into paragraphs."""
    pieces = [(c, p.strip()) for c, p in pieces if p and p.strip()]
    if not pieces:
        return []
    merges = merges or set()
    buf = pieces[0][1]
    prev_cue = pieces[0][0]
    for cue, t in pieces[1:]:
        cur = buf.rstrip()
        if (prev_cue, cue) in merges:
            buf = cur + " " + t
        elif _terminal(cur[-1]) or cur.endswith("—"):
            buf = cur + " " + t
        elif t[0].isupper() or t[0].isdigit() or t[0] in "«„\"'":
            buf = cur + ". " + t
        else:
            buf = cur + " " + t
        prev_cue = cue

    text = _protect(buf)
    raw_sents = re.split(r"(?<=[.!?…])\s+", text)
    sents: list[str] = []
    for raw in raw_sents:
        raw = _unprotect(raw.strip())
        if not raw:
            continue
        if sents and raw[:1].islower():
            prev = sents[-1].rstrip()
            if prev and prev[-1] in ".!?…":
                # ASR lowered the start of a new sentence: capitalise, do not glue.
                raw = raw[:1].upper() + raw[1:]
            else:
                sents[-1] = prev + " " + raw
                continue
        if sents and _norm(sents[-1]) == _norm(raw):
            continue  # ASR duplicated a sentence
        sents.append(raw)
    if not sents:
        return []

    sents[0] = sents[0][:1].upper() + sents[0][1:]
    sents[-1] = sents[-1].rstrip()
    if sents[-1][-1] not in ".!?…":
        sents[-1] += "."

    paras: list[str] = []
    cur: list[str] = []
    words = 0
    for sent in sents:
        cur.append(sent)
        words += len(sent.split())
        if words >= 55:
            paras.append(" ".join(cur))
            cur, words = [], 0
    if cur:
        paras.append(" ".join(cur))
    return paras

def render_seg(parent, s: Seg, cues, fixer=None):
    node = etree.SubElement(parent, q("seg"))
    node.set("n", str(s.cue))
    if s.i:
        node.set("from", str(s.i))
    if s.j != len(cues[s.cue].text):
        node.set("to", str(s.j))
    text, changed = (fixer(s.cue, s.text) if fixer else (s.text, False))
    if changed:
        node.set("corrected", "true")
    node.text = text


def main() -> int:
    _header, cues = load_cues()
    sha = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()

    doc = load_yaml(REPO / "data" / "debate.yml")
    corr_pre = load_yaml(REPO / "data" / "corrections.yml")
    fix_by_cue: dict[int, list[dict]] = {}
    for c in (corr_pre.get("corrections") or []):
        fix_by_cue.setdefault(int(c["n"]), []).append(c)
    fix_rules = [(r["pattern"], r["replacement"]) for r in (corr_pre.get("rules") or [])]
    merges = {tuple(int(x) for x in m) for m in (corr_pre.get("merges") or [])}
    unclear_by_cue = {int(u["n"]): u for u in (corr_pre.get("unclear") or [])}
    fired: set[int] = set()

    def fix_text(cue_n: int, text: str) -> tuple[str, bool]:
        """Apply the recorded corrections to a segment; the raw form stays in the appendix."""
        changed = False
        for idx, c in enumerate(fix_by_cue.get(cue_n, [])):
            if c["original"] in text:
                text = text.replace(c["original"], c["corrected"], 1)
                fired.add(id(c))
                changed = True
        for pat, rep in fix_rules:
            if pat in text:
                text = text.replace(pat, rep)
                changed = True
        u = unclear_by_cue.get(cue_n)
        if u and u["text"] in text:
            text = text.replace(u["text"], u["text"] + " [неясно]", 1)
            changed = True
        return text, changed
    sections = load_yaml(REPO / "data" / "attribution" / "sections.yml")["sections"]
    turns: list[dict] = []
    for path in sorted((REPO / "data" / "attribution" / "turns").glob("*.yml")):
        turns.extend((load_yaml(path) or {}).get("turns", []))
    corr = corr_pre

    if not turns:
        raise BuildError("no turns found")

    def start_offset(t: dict) -> int:
        a = int(t["cues"][0])
        return cues[a].text.find(t["start_at"]) if t.get("start_at") else 0

    turns.sort(key=lambda t: (int(t["cues"][0]), start_offset(t)))

    ids = {t["id"] for t in turns}
    if len(ids) != len(turns):
        raise BuildError("duplicate turn ids")
    for t in turns:
        if t.get("interrupts") and t["interrupts"] not in ids:
            raise BuildError(f"{t['id']}: interrupts unknown turn {t['interrupts']}")

    # ---- build items (segments and nested asides) ----------------------------
    built: list[tuple[dict, list[tuple[str, object]]]] = []
    occupied: list[tuple[int, int, str]] = []

    for t in turns:
        items: list[tuple[str, object]] = []
        asides = [normalize_aside(raw) for raw in (t.get("asides") or [])]
        full_asides = [a for a in asides if not (a.get("start_at") or a.get("end_at"))]
        partial_asides = [a for a in asides if a not in full_asides]
        for a in full_asides:
            asec = build_segs({"id": t["id"] + "/aside", **a}, cues)
            items.append(("aside", (a, asec)))
        full_cues = {n for a in full_asides
                     for n in range(int(a["cues"][0]), int(a["cues"][1]) + 1)}

        # A short interjection can sit inside one cue; cut that cue around it.
        cut_map: dict[int, list[tuple[int, int, dict]]] = {}
        for a in partial_asides:
            n = int(a["cues"][0])
            text = cues[n].text
            ai = text.find(a["start_at"]) if a.get("start_at") else 0
            if ai < 0:
                raise BuildError(f"{t['id']}: aside start_at {a.get('start_at')!r} not found in cue {n}")
            if a.get("end_at"):
                k = text.find(a["end_at"], ai)
                if k < 0:
                    raise BuildError(f"{t['id']}: aside end_at {a.get('end_at')!r} not found in cue {n}")
                aj = k + len(a["end_at"])
            else:
                aj = len(text)
            if aj <= ai:
                raise BuildError(f"{t['id']}: empty aside in cue {n}")
            cut_map.setdefault(n, []).append((ai, aj, a))

        for s in build_segs(t, cues):
            if s.cue in full_cues:
                continue
            cur = s.i
            for ai, aj, a in sorted(cut_map.get(s.cue, [])):
                if ai < s.i or aj > s.j:
                    raise BuildError(f"{t['id']}: aside cut falls outside cue {s.cue} segment")
                if ai > cur:
                    items.append(("seg", Seg(s.cue, cur, ai, cues[s.cue].text[cur:ai], s.cue_len)))
                items.append(("aside", (a, [Seg(s.cue, ai, aj, cues[s.cue].text[ai:aj], s.cue_len)])))
                cur = aj
            if cur < s.j:
                items.append(("seg", Seg(s.cue, cur, s.j, cues[s.cue].text[cur:s.j], s.cue_len)))
        items.sort(key=lambda it: (it[1] if it[0] == "seg" else it[1][1][0]).start_key)

        for kind, obj in items:
            segs = [obj] if kind == "seg" else obj[1]
            occupied.extend((s.start_key, s.end_key, t["id"]) for s in segs)
        built.append((t, items))

    def ws_only_gap(e1: int, s2: int) -> bool:
        """A gap caused only by the space between two sentences in one cue."""
        if e1 // ASCALE != s2 // ASCALE:
            return False
        cue = cues[e1 // ASCALE]
        return cue.text[e1 % ASCALE:s2 % ASCALE].strip() == ""

    occupied.sort()
    for (s1, e1, who1), (s2, e2, who2) in zip(occupied, occupied[1:]):
        if s2 < e1:
            raise BuildError(f"overlap between {who1} and {who2} near cue {s2 // ASCALE}")
        if s2 > e1 and not ws_only_gap(e1, s2):
            raise BuildError(
                f"uncovered text between {who1} and {who2}: "
                f"cue {e1 // ASCALE}+{e1 % ASCALE} .. cue {s2 // ASCALE}+{s2 % ASCALE}"
            )
    if occupied[0][0] != min(cues) * ASCALE:
        raise BuildError("built range does not start at the first cue")

    last_cue = (max(e for _s, e, _w in occupied) - 1) // ASCALE

    # ---- document ------------------------------------------------------------
    root = etree.Element(q("debate"), nsmap={None: NS})
    root.set("id", doc["id"])
    root.set("lang", doc.get("lang", "bg"))
    root.set("version", doc["version"])
    root.set("status", doc["status"])
    root.set("text-mode", "corrected" if (corr.get("corrections") or corr.get("rules")) else "verbatim")

    meta = e(root, "meta")
    e(meta, "title").text = doc["title"]
    e(meta, "broadcast", channel=doc["broadcast"]["channel"], date=doc["broadcast"]["date"],
      duration=doc["broadcast"]["duration"], language=doc["broadcast"]["language"])
    e(meta, "source", type=doc["source"]["type"], engine=doc["source"]["engine"],
      url=doc["source"]["url"], retrieved=doc["source"]["retrieved"],
      sha256=sha, cues=len(cues))
    for c in doc.get("credits") or []:
        e(meta, "credit").text = c
    e(meta, "generated", tool=doc["generated"]["tool"], model=doc["generated"]["model"],
      date=date.today().isoformat(), method=doc["generated"]["method"])
    people = e(meta, "participants")
    for p in doc["participants"]:
        e(people, "person", id=p["id"], role=p["role"], name=p["name"],
          **{"name-lat": p.get("name_lat")}, affiliation=p.get("affiliation"),
          note=p.get("note"), verified=bool(p.get("verified")))
    for d in doc["disclaimers"]:
        e(meta, "disclaimer").text = d
    conv = e(meta, "conventions")
    for r in doc["conventions"]:
        e(conv, "rule").text = r
    e(meta, "coverage", **{"from": cues[min(cues)].tc, "to": cues[last_cue].tc,
                           "cues": f"{min(cues)}-{last_cue}", "turns": len(turns)})

    body = e(root, "body")
    idx = 0
    for sec in sections:
        sa, sb = int(sec["cues"][0]), int(sec["cues"][1])
        sec_el = e(body, "section", id=sec["id"], title=sec["title"],
                   **{"from": cues[sa].tc, "to": cues[sb].tc})
        covered: list[tuple[int, int]] = []
        while idx < len(built) and sa <= int(built[idx][0]["cues"][0]) <= sb:
            t, items = built[idx]
            first = items[0][1] if items[0][0] == "seg" else items[0][1][1][0]
            last = items[-1][1] if items[-1][0] == "seg" else items[-1][1][1][-1]
            turn_el = e(sec_el, "turn", id=t["id"], speaker=t["speaker"], kind=t["kind"],
                        start=cues[first.cue].tc, end=cues[last.cue].tc,
                        confidence=t.get("confidence", "medium"),
                        overlap=t.get("overlap") or None,
                        interrupts=t.get("interrupts"),
                        truncated=t.get("truncated") or None)
            texts_el = e(turn_el, "text")
            if t.get("text"):
                # editorial override: paragraphs, with {{aN}} marking asides
                asides = [obj for kind, obj in items if kind == "aside"]
                blocks = [b.strip() for b in str(t["text"]).strip().split("\n\n")]
                for block in blocks:
                    m = PLACEHOLDER.match(block)
                    if not m:
                        e(texts_el, "p").text = " ".join(block.split())
                        continue
                    a, asec = asides[int(m.group(1)) - 1]
                    a_el = e(texts_el, "aside", speaker=a["speaker"], kind=a["kind"],
                             start=cues[asec[0].cue].tc, cue=asec[0].cue,
                             confidence=a.get("confidence", "medium"),
                             overlap=a.get("overlap") or None)
                    for chunk in assemble([(x.cue, fix_text(x.cue, x.text)[0]) for x in asec], merges):
                        e(a_el, "p").text = chunk
                src_el = e(turn_el, "source")
                for kind, obj in items:
                    for x in ([obj] if kind == "seg" else obj[1]):
                        render_seg(src_el, x, cues, None)
                covered.append((first.start_key, last.end_key))
                idx += 1
                continue

            para: list[str] = []

            def flush_para():
                nonlocal para
                if para:
                    for chunk in assemble(para, merges):
                        e(texts_el, "p").text = chunk
                    para = []

            for kind, obj in items:
                if kind == "seg":
                    para.append((obj.cue, fix_text(obj.cue, obj.text)[0]))
                else:
                    flush_para()
                    a, asec = obj
                    a_el = e(texts_el, "aside", speaker=a["speaker"], kind=a["kind"],
                             start=cues[asec[0].cue].tc, cue=asec[0].cue,
                             confidence=a.get("confidence", "medium"),
                             overlap=a.get("overlap") or None)
                    for chunk in assemble([(x.cue, fix_text(x.cue, x.text)[0]) for x in asec], merges):
                        e(a_el, "p").text = chunk
            flush_para()

            src_el = e(turn_el, "source")
            for kind, obj in items:
                segs = [obj] if kind == "seg" else obj[1]
                for x in segs:
                    render_seg(src_el, x, cues, None)
            covered.append((first.start_key, last.end_key))
            idx += 1

        sec_start, sec_end = sa * ASCALE, (sb + 1) * ASCALE
        joined = all(
            covered[i][1] == covered[i + 1][0] or ws_only_gap(covered[i][1], covered[i + 1][0])
            for i in range(len(covered) - 1)
        )
        if not covered:
            status = "planned"
        elif covered[0][0] == sec_start and covered[-1][1] == sec_end and joined:
            status = "complete"
        else:
            status = "partial"
        sec_el.set("status", status)

    if idx != len(built):
        raise BuildError(f"turn {built[idx][0]['id']} falls outside the section plan")

    dead = [c for c in (corr.get("corrections") or [])
            if int(c["n"]) <= last_cue and id(c) not in fired]
    if dead:
        for c in dead:
            print(f"DEAD CORRECTION: cue {c['n']}: {c['original']!r} -> {c['corrected']!r}", file=sys.stderr)
        raise BuildError(f"{len(dead)} correction(s) never matched the text")

    # ---- appendix ------------------------------------------------------------
    app = e(root, "appendix")
    if corr.get("ambiguities"):
        ambs = e(app, "ambiguities")
        for a in sorted(corr["ambiguities"], key=lambda x: x["id"]):
            a_el = e(ambs, "ambiguity", id=a["id"], turn=a.get("turn"),
                     cues=str(a["cues"]), time=a.get("time"), quote=a.get("quote"),
                     status=a.get("status", "open"))
            e(a_el, "question").text = a["question"]
            for r in a["readings"]:
                e(a_el, "reading").text = r
            if a.get("resolution"):
                e(a_el, "resolution").text = a["resolution"]
    if corr.get("corrections") or corr.get("rules"):
        cs = e(app, "corrections")
        if corr.get("rules"):
            cs.set("rule", "; ".join(f"{r['pattern']}→{r['replacement']}" for r in corr["rules"]))
        for c in corr.get("corrections") or []:
            e(cs, "correction", n=c["n"], original=c["original"],
              corrected=c["corrected"], why=c["why"])
    if corr.get("unclear"):
        un = e(app, "unclear")
        for u in corr["unclear"]:
            e(un, "unclear", n=u["n"], text=u["text"], why=u["why"])
    if corr.get("gaps"):
        gp = e(app, "gaps")
        for g in corr["gaps"]:
            e(gp, "gap", **{"from": g["from"], "to": g["to"], "reason": g["reason"]})

    out = REPO / "build" / "debate.xml"
    out.parent.mkdir(exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(out, encoding="utf-8", xml_declaration=True, pretty_print=True)

    schema = etree.XMLSchema(etree.parse(str(REPO / "schema" / "debate.xsd")))
    if not schema.validate(tree):
        for err in schema.error_log:
            print(f"XSD: {err}", file=sys.stderr)
        raise BuildError("XML does not validate against schema/debate.xsd")

    print(f"wrote {out.relative_to(REPO)}: {len(turns)} turns, cues {min(cues)}-{last_cue}")
    for sec in body:
        print(f"  {sec.get('id')}  {sec.get('status'):9s} {len(sec):3d} turns  {sec.get('title')}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
