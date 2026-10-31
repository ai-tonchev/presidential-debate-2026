# Handoff — state of play

Updated 2026-10-31. Read `AGENTS.md` first (rules, data model, workflow); this file
is the short transfer note for whoever picks the work up next — human or agent.

---

## What is done

| | |
| --- | --- |
| Coverage | **the whole recording**: cues 4–1833, 0:00:20–1:51:18, all 11 sections `complete` |
| Turns | 288 (t001–t288), every one with `confidence` and a note |
| Text | editorial readable text (`<text>/<p>`); raw ASR kept per turn in `<source>` |
| Apparatus | 188 corrections, 14 document-wide rules, 36 unclear spots (inline `[неясно]`), 15 ambiguities (**1 open**), 2 gaps |
| Artefacts | `build/debate.xml` (XSD-valid), `.md`, `.html`, `.pdf` (64 pp, 301 bookmarks), `build/overview.md/.pdf` (10 pp) |
| Integrity | raw file checksummed; build aborts on gap/overlap/dead correction |

`make all` reproduces everything. Nothing is committed to git yet — the working
tree is the deliverable; a first commit is advisable before more edits.

---

## Open questions — need the human's ears

The editor reviewed the nine open ambiguities on 2026-10-31 and answered all of
them. Eight are now closed in the data (`status: resolved` + `resolution`); the
attribution was changed where the answer required it:

| Resolved | What changed |
| --- | --- |
| `amb-a01` (0:16:02, 225) | Yotova interjects, then Gyurov resumes at 228 — aside confirmed, confidence raised |
| `amb-a02` (0:20:33, 312) | «Госпожо, и от това?» is **Zlatareva's** aside inside Yotova's turn (reversal) |
| `amb-a05` (0:00:20, 4–8) | the opening voice-over is the moderator |
| `amb-a10` (0:35:38, 602–608) | **Yotova** speaks from 602, including the Warsaw Pact jab — `t074` 588–601, `t075` 602–608 |
| `amb-a11` (0:39:11, 645–680) | Yotova defends industry, Gyurov answers «под напрежение» |
| `amb-a12` (0:45:45, 755–761) | Yotova attacks |
| `amb-a13` (1:10:15, 1110–1115) | only Yotova and the moderator speak — `t151` moved to Yotova |
| `amb-a14` (1:07:31, 1035–1052) | Yotova explains the Constitutional Court |
| `amb-a15` (1:23:51, 1363–1385) | **Yotova** asks the «възродителен процес» question — `t180` Yotova, `t181` Gyurov |

Also corrected by ear: «осветиха» → **«осуетиха»** in cues 635 and 637 (the
statesmen *prevented* Bulgaria's exit from the coalition), and the whole
1382–1389 stretch was merged and de-capitalised to read as one sentence.

**Still open — one item:**

* **0:33:02 · cues 551–553** (`amb-a09`, `t069`, `confidence="low"`) — «Това,
  което виждаме, са близо 400 милиона долара…». The editor could not find the
  passage at that time in the recording; the cue times in the transcript may drift.
  `t069` keeps `confidence="low"` until it is found.

## What remains after review

1. Close the ambiguities (`status: resolved` + `resolution`) as the editor confirms
   each one; flip `t069` etc. only if the audio says so.
2. Decision **D6**: how aggressively to copy-edit grammar. Current practice is
   per-case corrections with a `why`; the readable text still contains speech
   artefacts («най-силният съюз», «един независен» was fixed, «аз мятам» fixed).
3. Optional: **D8** — a clickable turn index by time (the PDF outline already gives
   navigation by section and turn).
4. First git commit.

---

## Traps discovered (do not re-learn these)

1. **Cue id = line number in `data/source/transcript-raw.txt`.** Editing the raw file
   invalidates every attribution. `scripts/check_source.py` guards the checksum.
2. **Corrections are a per-cue list.** The build aborts if any correction in the
   covered range never matches — that guard caught five dead entries with wrong cue
   numbers, and later a wrong cue number on «как за напред» (848, not 849).
3. **`merges: [[a, b]]`** in `corrections.yml` forbids a sentence break between two
   cues. Use it when the ASR put a full stop mid-sentence (252–253, 574–575,
   1041–1042).
4. **The abbreviation guard** protects «г.», «т.е.», «Р.С.» … but must use a
   word-boundary lookbehind: a naive `replace("с.", …)` matches the end of
   «вопрос.»/«глас.» and silently kills sentence splitting.
5. **Unknown `<unclear>` text never matches** → no inline `[неясно]`. Check with:
   `python3 -c "import sys,yaml;sys.path.insert(0,'scripts');from transcript import load_cues;_,c=load_cues();[print(u['n'],u['text'] in c[int(u['n'])].text) for u in yaml.safe_load(open('data/corrections.yml'))['unclear']]"`
6. **Partial-cue asides** (`start_at`/`end_at` inside one cue) are supported — used in
   `t070` (cue 562) and `t254`/`t255` (cue 1714, where Gyurov's one-word answer and
   the moderator's prompt share a cue).
7. **WeasyPrint is broken on this machine**; Chrome prints the PDF. Use
   `--user-data-dir` inside the workspace and `--no-pdf-header-footer`.
8. **Chrome cannot do `target-counter`** → the ToC lists times, not page numbers. The
   PDF outline is added afterwards by `scripts/add_outline.py` (pypdf).
9. `build/.chrome/` and `build/preview/` are gitignored scratch space.
10. **An `<unclear>` entry that a correction already resolved is dead weight, and it
    reads as a contradiction** (`Край, свърши. [неясно].`). Four such entries (128,
    318, 555, 562) were removed on 2026-10-31. The build does not guard this yet.
11. **Editing `corrections.yml` with a regex on `n: <cue>` hits both `corrections`
    and `unclear` lines** (same `  - {n: …` prefix). Anchor on `text:` / `original:`
    or edit by hand. If a correction is lost, `build/debate.xml` still holds it.
12. **Find the cue for a string before writing a correction**: the build tells you
    (`DEAD CORRECTION`), but strings that span two cues never match — check with the
    small locator script (regex over the raw file, print `n` for each hit).

---

## Definition of done for the whole project

- All 11 sections `complete`; every turn has `confidence`; every `low`/`medium`
  attribution has a note or an ambiguity. **Done.**
- No dead corrections, no unsatisfied `<unclear>` entries, no silently filled gaps.
  **Done.**
- PDF with cover, fonts, outline; overview with recomputed numbers. **Done.**
- Disclaimers and the BorisThoris credit present in README, XML, PDF. **Done.**
- Open: one ambiguity (`amb-a09`) and the copy-editing decision (D6).

---

## Numbers at a glance (from `build/overview.md`, never hand-edited)

| | turns | words | speaking time (approx.) |
| --- | --- | --- | --- |
| Поли Златарева | 128 | 2 383 | 17:01 |
| Илияна Йотова | 83 | 7 098 | 47:46 |
| Андрей Гюров | 77 | 5 582 | 40:24 |

Moderator interventions aimed at a candidate: 13. Candidate-on-candidate
interruptions: 3. The numbers are recomputed on every `make overview`.
