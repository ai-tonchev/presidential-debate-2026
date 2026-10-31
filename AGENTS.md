# AGENTS.md — дебат Йотова – Гюров (БНТ, 29.10.2026)

Instructions for anyone (human or AI agent) continuing this project.
Read this file before touching anything. **If you are picking the project up cold,
read `HANDOFF.md` first** — it is the short state transfer (what is done, what is
open, which traps have already been paid for). This file records *what* we are
building, *how* the data is structured, *what was decided and why*, and *where the
uncertainty is*. If you change a convention, change this file in the same commit.

---

## 1. The job

Turn a raw, un-labelled Whisper transcript of the BNT presidential debate
(Yotova – Gyurov, 29.10.2026) into a structured, attributable, reproducible text:

```
data/source/transcript-raw.txt     (immutable, checksummed)
        │
        ├── data/attribution/*.yml  (hand-verified speaker attribution)
        ├── data/corrections.yml    (ASR fixes, unclear spots, ambiguities, gaps)
        ▼
build/debate.xml                   (canonical structured text, XSD-validated)
        ▼
build/debate.md / debate.html      (readable renderings)
        ▼
build/debate.pdf                   (print artefact: A4, header image, anchors)
```

The XML is the contract. Markdown and PDF are renderings of it. Never edit
`build/debate.xml` by hand — it is generated and will be overwritten.

**Speakers: exactly three.** The moderator, Илияна Йотова and Андрей Гюров.
If a fourth voice seems to appear, it is a modelling problem, not a new speaker
(see `amb-a05` about the opening voice-over).

---

## 2. Non-negotiables

1. **The raw transcript is immutable.** `data/source/transcript-raw.txt` must stay
   byte-identical (`sha256 83b8f6c6…b6c78`). Cue numbers are line numbers; editing
   the file silently invalidates every attribution. Run `scripts/check_source.py`.
2. **No invented speech — but the audio, not the ASR, is the authority.** The
   transcript is a lossy instrument: it drops words, mangles names and misses
   interjections. A word the editor hears in the recording but the ASR missed is a
   *restoration*, recorded in `<corrections>` with `why` naming the editor as the
   source (e.g. «Край, свърши.», cue 562). What is forbidden is plausible invention
   without a listening source. Missing audio is a `<gap>`, garbled audio is
   `<unclear>`, a doubtful attribution is an `<ambiguity>` with a confidence level.
3. **Attribution is a judgement, and it is recorded as one.** Every turn carries
   `confidence` (`high` / `medium` / `low`). Low is not a failure; hiding doubt is.
4. **The build must fail loudly.** If the turn map has a gap, an overlap, a cue
   assigned twice, or an anchor string that does not exist exactly once, the build
   aborts. Do not "fix" the build by widening a range until it passes.
5. **Transparency over polish.** The document states on its face that it is a
   machine transcript with AI attribution. See §8.

---

## 3. Current state (keep this table up to date)

| Section | Cues | Time | Turns | Status |
| --- | --- | --- | --- | --- |
| s01 Встъпление | 4–18 | 0:00:20–0:01:27 | 7 | **complete** |
| s02 Избирателна активност и партийна подкрепа | 19–91 | 0:01:31–0:07:02 | 11 | **complete** |
| s03 Външна политика и сигурност | 92–562 | 0:07:05–0:34:17 | 52 | **complete** |
| s04 Национален суверенитет и съюзническо присъствие | 563–680 | 0:34:19–0:40:21 | 18 | **complete** |
| s05 Отношения със Скопие | 681–766 | 0:40:22–0:46:49 | 12 | **complete** |
| s06 Институции, Конституция, служебни кабинети | 767–1006 | 0:46:54–1:05:46 | 28 | **complete** |
| s07 Бюджет, цени и инфлация | 1007–1297 | 1:05:47–1:19:46 | 38 | **complete** |
| s08 Взаимни въпроси между кандидатите | 1298–1608 | 1:20:02–1:37:33 | 39 | **complete** |
| s09 Лични въпроси | 1609–1779 | 1:37:43–1:48:33 | 73 | **complete** |
| s10 Заключителни думи | 1780–1814 | 1:48:37–1:50:27 | 4 | **complete** |
| s11 Закриване | 1815–1833 | 1:50:36–1:51:18 | 6 | **complete** |

Coverage: **1833 of 1833 cues (the whole 1:51:18)**, 288 turns (t001–t288), 11 sections
`complete`. `status` is computed by the builder from actual coverage; never set it by hand.
Coverage work is done; of the 15 recorded ambiguities, 14 are resolved and only
`amb-a09` (cues 551–553) is still open — see `docs/QUESTIONS.md`.

---

## 4. Repository layout

```
data/
  debate.yml                  document metadata, people, disclaimers, conventions
  corrections.yml             per-cue fixes, rule layer, merges, unclear spots,
                              ambiguities (with time+quote), gaps
  source/
    transcript-raw.txt        immutable source (do not edit)
    SOURCE.md                 provenance, checksum, known gaps, reuse caveats
  overview.yml                editorial summaries per section (interpretation)
  attribution/
    sections.yml              section plan for the whole recording
    turns/NN-*.yml            verified turns, cue ranges + confidence + notes
schema/
  debate.xsd                  the contract; build validates against it
scripts/
  transcript.py               cue parser (cue id = raw line number)
  build_xml.py                YAML + raw text → build/debate.xml (+validation, readable text)
  render_md.py                XML → build/debate.md
  render_html.py              XML → build/debate.html (PDF source)
  render_overview.py          XML + overview.yml → build/overview.md/.html (analytics)
  check_source.py             checksum guard
assets/
  images/debate-header.png    cover still (flagman.bg / БНТ)
  fonts/                      Source Serif 4 + Ysabeau, static instances (OFL)
  styles/debate.css           print stylesheet (A4, running heads, turn blocks)
build/
  debate.xml, .md, .html, .pdf  transcript artefacts (safe to delete, never edit)
  overview.md, .html, .pdf      analytics artefacts (same rule)
docs/
  METHOD.md                   attribution method + confidence rubric
  DISCLAIMERS.md              exact disclaimer texts to reuse
  QUESTIONS.md                open decisions, with examples
```

---

## 5. Data model (what each XML element means)

Read `schema/debate.xsd` for the full contract; this is the intent.

| Element | Meaning |
| --- | --- |
| `<debate text-mode="corrected">` | Root. `corrected` = obvious ASR errors fixed in place; raw forms preserved in `<appendix>`. |
| `<meta>` | Title, broadcast, provenance (`sha256`, URL, retrieval date), participants, disclaimers, conventions, computed coverage. |
| `<section status>` | Editorial topic block. `complete` only if the builder proved full coverage; `partial`, `planned` otherwise. |
| `<turn id speaker kind start end confidence>` | One uninterrupted utterance by one speaker. `start`/`end` are the first/last cue times, not measured acoustically. |
| `<turn>/<text>` + `<p>` | The **readable** text: editorial sentences and paragraphs, not ASR segments. This is what MD/PDF render. |
| `<turn>/<source>` | The raw ASR text of the same turn, verbatim (errors included). Diff `<source>` against `<text>` to see every editorial change. |
| `<turn overlap interrupts truncated>` | `overlap` = simultaneous speech with the previous turn; `interrupts` points at the interrupted turn; `truncated` = the speaker was cut off. |
| `<aside speaker kind start cue overlap>` | A brief interjection **inside** a turn, after which the main speaker continues. Preserves document order. |
| `<seg n from to corrected>` | One raw cue. `n` = line number in the raw file. `from`/`to` = character offsets when a turn starts/ends mid-cue (overlaps, moderator interjections merged into one cue). |

### Modelling rules (decided 2026-10-31)

* **Brief interjection + main speaker resumes** → nested `<aside>`.
  Example: the moderator's «30 секунди.» at 0:13:46 sits inside Yotova's answer
  (`t024`); Yotova's attempt to take the floor at 0:16:02 and the moderator's
  «Само секунда…» sit inside Gyurov's answer (`t026`).
* **Floor grab, main speaker does not resume** → separate `<turn>` with
  `overlap="true"` and `interrupts="#id"`. Examples: `t031` (Yotova takes over from
  Gyurov at 0:18:51), `t069` (Yotova cuts Gyurov at 0:33:02). Note `t048` (0:27:07)
  is *not* an interruption — the editor confirmed Gyurov simply takes the floor.
* **Mid-cue split** → two turns sharing a cue, the second starting exactly where
  the first ends, using `start_at`/`end_at` anchors in YAML. Example: cue 88 holds
  both Gyurov's «Това е отговора.» and the moderator's «Вие имате още 10 секунди.»
  (`t016`/`t017`).
* **Never** merge two speakers into one turn "to keep it tidy".

### Invariants the builder enforces

1. Turns tile the covered range exactly: no gap (except a whitespace-only gap inside
   a cue), no overlap, no cue assigned twice.
2. Every YAML anchor exists **exactly once** in its cue.
3. Section `status` is derived from coverage.
4. Output validates against `schema/debate.xsd`.

---

## 6. Attribution method (and why it is not rules-based)

There is **no diarization** in the source and no speaker-classifier in this repo.
Attribution was produced by reading the dialogue semantically and writing down a
decision per turn. That is deliberate: name-based heuristics were measured and
rejected — of 1830 cues only 12 are bare hand-offs («Илияна Йотова.»), while 55
cues end in a participant's name, and most of those are the candidates *addressing
each other* («…какво им обещахте господин Гюров»). A regex attributor would
mislabel roughly half of them.

How boundaries were decided, in order of strength:

1. **Explicit hand-off**: the moderator names the next speaker («Андрей Гюров.»,
   «Реплика Илияна Йотова.», «Бърз отговор, Андрей Гюров.»).
2. **Addressee shift**: «вашата теза, господин Гюров» ⇒ speaker is Yotova;
   «госпожо Йотова» ⇒ speaker is Gyurov. Third person ⇒ the moderator.
3. **Discourse role**: questions with procedural phrasing («Имате още 30 секунди.»,
   «Следваме регламента.») ⇒ moderator; first-person policy claims ⇒ candidate.
4. **Timer/format logic**: a turn is cut when the moderator invokes time.

Confidence rubric (`docs/METHOD.md` has the full version):

* `high` — hand-off or unambiguous addressee shift.
* `medium` — inferred from topic continuity or from a sequence of short cues.
* `low` — the fragment could plausibly belong to two speakers; must have an
  `<ambiguity>` entry.

When two readings are possible: choose the one that makes the *exchange* coherent
(who could plausibly answer whom), write both readings into `<ambiguities>`, mark
`status` honestly (`resolved` only if the text itself decides it).

---

## 7. Overlap / interruption inventory (as found so far)

These are the cases the user asked to be shown explicitly. They are the places
where the transcript is least like a clean script.

| Time | Type | What happens | Handled as |
| --- | --- | --- | --- |
| 0:04:20 | time warning | moderator warns Yotova about the clock right after her answer | `t012` (separate turn, `time_call`) |
| 0:13:46 | time call inside answer | «30 секунди.» while Yotova is speaking | `<aside>` in `t024` |
| 0:16:02–0:16:09 | three-way crosstalk | Yotova tries to take the floor, moderator blocks her, Gyurov resumes | `amb-a01`, `<aside>`×2 in `t026` |
| 0:18:51 | floor grab | Yotova speaks over Gyurov for ~1 min and questions him | `t031` `overlap`+`interrupts` |
| 0:19:44 | hand-back | «Бърз отговор, Андрей Гюров.» | `t032` |
| 0:27:07 | floor-taking | Gyurov simply takes the floor here — editor confirms it is not an interruption | `t048` (no `overlap`) |
| 0:28:57 | clarification cut | moderator interrupts Gyurov: «Какво искате да кажете с това?» | `<aside>` in `t051` |
| 0:31:07–0:31:18 | procedural crosstalk | Gyurov asks for the floor; Yotova «Само секунда»; moderator «Ще имате право на реплика»; Yotova «Както аз ви чакам…» and «Само да не ми хапвате от секундите». They talk over each other and parts are unintelligible | `t054`–`t058` (editor-corrected) |
| 0:32:06 | one-line interjection | «Това е абсолютна манипулация.» — Gyurov, confirmed | `t065`, `amb-a08` |
| 0:33:02 | floor grab — disputed | «Това, което виждаме…» assigned to Yotova, but the content continues Gyurov's answer; `confidence="low"`, `amb-a09` open | `t069` |
| 0:34:17 | interjection inside a sentence | «Край, свърши.» — the moderator, cutting Gyurov's last sentence; the word «край» is not in the ASR | `<aside>` inside `t070` |
| 0:35:38–0:35:57 | floor taking | «Само още едно допълнение…» — Yotova takes over once Gyurov's answer ends, adds the brigade detail and the Warsaw Pact jab (602–608) | `t074` 588–601 / `t075` 602–608, `amb-a10` |
| 0:36:26 | mandatory reply | Yotova: «Само, че тук имам право наистина на една задължителна реплика.»; the moderator gives her seconds and she continues | `<aside>` in `t078` |
| 0:37:25 | floor grab | Yotova jumps in with «Може ли един въпрос?» before the moderator grants her the floor, then questions Gyurov about the coalition | `t080` |
| 0:39:08 / 0:39:31 | time blocks | «Имате по 30 секунди и двамата. Искате ли още реплики?» and «20 секунди за вас.» — the second block runs 48 s | `t085`, `t087` |
| 0:39:11–0:40:21 | disputed attribution | «Българската индустрия се развива твърде добре» vs «В момента българската индустрия е под напрежение» — who says which | `t086`/`t088`, `amb-a11` |
| 1:07:31–1:08:04 | argument inside an answer | «Господин Гюров, все пак трябва да сме коректни…» — Yotova explains the Constitutional Court's objection to him | `t140`, `amb-a14` |
| 1:10:15–1:10:30 | procedural crosstalk | «Ако не говорите върху мен…» / «Не говоря върху вас…» / «Защо като дойде новото правителство…» — Yotova and the moderator only, every line 1–2 cues | `t147`–`t151`, `amb-a13` |
| 1:23:51–1:24:51 | rules crosstalk | «Какъв е регламентът?» … «тук нямате право на дуплика» … «А що се отнася до моя конкретен въпрос?» | `t176`–`t181`, `amb-a15` |
| 1:31:27 / 1:37:43 | missing audio | transcript jumps mid-sentence | `<gap>` (see SOURCE.md) |

All of these were reviewed by the editor on 2026-10-31. Resolved: `amb-a01` (cue
225 — Yotova, then Gyurov resumes at 228), `amb-a02` (cue 312 — **Zlatareva's**
aside inside Yotova's turn), `amb-a03`, `amb-a04`, `amb-a05` (opening voice-over =
the moderator), `amb-a06`, `amb-a07` (cue 540 = moderator, cue 541 = Yotova),
`amb-a08` (Gyurov), `amb-a10` (cues 602–608 — **Yotova** throughout, `t074`
588–601), `amb-a11` (Yotova defends industry, Gyurov answers «под напрежение»),
`amb-a12` (Yotova attacks), `amb-a13` (cues 1110–1115 — only Yotova and the
moderator), `amb-a14` (Yotova), `amb-a15` (cues 1363–1385 — **Yotova** asks the
«възродителен процес» question). Still open: `amb-a09` (cues 551–553 at 0:33:02 —
the editor could not find the passage at that time; `t069` stays `low`).

Also confirmed by the editor: «осветиха» is **«осуетиха»** in cues 635 and 637.

**Interjections that cut a sentence in half** are modelled as `<aside>` with
`start_at`/`end_at` inside a single cue — see `t070` (cue 562), where the
moderator's «Край, свърши.» interrupts Gyurov mid-sentence and he finishes it
afterwards. The builder splits the cue into segments around the aside.

---

## 8. Transparency & disclaimers (do not weaken these)

The final document must carry, on its first page:

1. The transcript is **machine-generated** (Whisper large-v3) without diarization;
   errors and missing fragments are possible.
2. Speaker attribution was produced **with AI assistance** and has not been checked
   against an official recording; confidence is stated per turn.
3. It is **not an official record** and must not be used as evidence; verify against
   the broadcast before quoting.
4. Corrections are listed with their original forms; unclear spots are marked inline.
5. Gaps in the source are shown, not silently closed.
6. **The transcript author is credited by name** — BorisThoris (GitHub gist). The
   credit appears in `README.md`, in `<meta>/<credit>` of the XML and in the rendered
   header. Never strip it when re-rendering; the rest of the document is built *on*
   that transcript.

These live in `data/debate.yml` (`disclaimers`, `conventions`), are copied into the
XML `<meta>`, and are rendered into the markdown header by `render_md.py`. The
canonical wording is in `docs/DISCLAIMERS.md`.

The repository must also state that the *editing* (attribution, topic segmentation,
corrections) is AI-assisted work — see `docs/METHOD.md` §"What is ours".

---

## 9. Commands

```bash
python3 scripts/check_source.py     # verify raw file checksum
python3 scripts/build_xml.py        # build + XSD validate build/debate.xml
python3 scripts/render_md.py        # build/debate.md
python3 scripts/render_html.py      # build/debate.html
make pdf                            # headless Chrome → build/debate.pdf
make overview-pdf                   # build/overview.pdf (numbers + arguments)
make all                            # everything
```

### Overview document

`scripts/render_overview.py` builds a short analytical companion to the
transcript: section structure, the arguments per topic, speaking time per
participant, and every moderator intervention (time, type, quote, target).
Editorial prose lives in `data/overview.yml`; **all numbers and quotes are
computed from `build/debate.xml` and the raw cue times**, so they cannot drift
from the transcript.

Measurement caveats, stated in the document itself: speaking time is derived from
cue start times capped at 12 s; overlapping speech is counted once, for the cue's
owner; and only the covered part of the recording is measured. When more sections
are attributed, the numbers update automatically — never hand-edit them.

### PDF pipeline (decided 2026-10-31)

HTML + CSS is the PDF source (`build/debate.html` + `assets/styles/debate.css`),
printed by **headless Chrome**. WeasyPrint would give PDF bookmarks and
`target-counter` TOC page numbers, but it is unusable on this machine: the
system `libpangoft2` resolves against the conda `libfontconfig` 1.12 and fails
with `undefined symbol: FcConfigSetDefaultSubstitute`; preloading the system
fontconfig segfaults. Chrome is therefore the renderer of record for now.

Typography:

| Role | Family | File |
| --- | --- | --- |
| Body | Source Serif 4 (OFL), instanced at `opsz=12` | `assets/fonts/SourceSerif4-*.ttf` |
| Headings / labels | Ysabeau (OFL), instanced at `wght=500/700` | `assets/fonts/Ysabeau-*.ttf` |

Both carry Bulgarian Cyrillic localised forms (`locl` / `BGR`), which the CSS
activates through `<html lang="bg">`. Do not swap in a font that lacks `locl`
without checking `в`, `д`, `ж`, `з`, `и`, `к`, `л`, `п`, `т`, `ц`, `ш`, `щ` —
Russian forms read wrong to a Bulgarian eye.

Header image: `assets/images/debate-header.png` (split-screen still of both
candidates, published by flagman.bg from the BNT broadcast). Credit line is
printed under the title on the cover; the rights remain with БНТ.

Chrome limitation: `target-counter` is unsupported, so the table of contents lists
start times instead of page numbers. Everything else is covered: internal anchors
(`#s01`, `#t042`) survive as links, and `scripts/add_outline.py` post-processes the
PDF with **pypdf** to add a real outline — sections as top-level bookmarks and every
turn as a child (`0:31:09 · Илияна Йотова`). 301 bookmarks for the current 288 turns
(eleven sections + the two appendix entries).

Build output is the review interface: it prints every section with its computed
status and turn count. A section that should be `complete` but prints `partial`
means the turn map does not tile it — fix the map, not the status.

Common build failures and what they mean:

| Message | Cause |
| --- | --- |
| `uncovered text between tX and tY` | a cue range was skipped, or an anchor forgot a trailing word |
| `overlap between tX and tY` | two turns claim the same cue; usually a shared cue needs `start_at`/`end_at` |
| `start_at '…' not found` / `ambiguous` | anchor text has a typo or occurs twice in the cue |
| `turn … falls outside the section plan` | section boundaries in `sections.yml` are wrong |

---

## 10. How to extend coverage (the loop)

One section at a time, in order:

1. Read the cue range for the section, in full, with line numbers:
   `awk 'NR>=A && NR<=B {printf "%d|%s\n", NR, $0}' data/source/transcript-raw.txt`
2. Write `data/attribution/turns/NN-<slug>.yml`: one entry per speaker turn, with
   `speaker`, `kind`, `cues`, `confidence`, `note`; add `asides`, `start_at`,
   `end_at`, `overlap`, `interrupts`, `truncated` only where they apply.
3. Run `python3 scripts/build_xml.py`. Resolve every error by improving the map.
4. Update the section table in §3 and any new ambiguity in `docs/QUESTIONS.md`.
5. Ask the user to review the section (they review per section, by decision of
   2026-10-31). **Every review item must carry clock time, cue lines and the exact
   quoted text** — a review item without the quote and the timestamp cannot be
   checked. The same fields go into `<ambiguity time=... quote=...>`, so the PDF
   appendix shows them too.

Do **not** batch-attribute several sections blind and then "check later": the errors
that matter (who said which short sentence) are exactly the ones that a bulk pass
hides.

**Exception, 2026-10-31.** The editor asked for the whole recording in one pass and
deferred all resolutions to the end. Sections 5–11 were therefore attributed
sequentially in a single session, each one built and tiled before the next; the
review they would have had per section is consolidated in `docs/QUESTIONS.md`
("Final review"). The rule still stands for future work: one section, one build,
one review.

---

## 11. Open decisions (blocking later stages)

Resolved on 2026-10-31 (see `docs/QUESTIONS.md` for the exact wording):

* **D1 Punctuation → resolved.** The document is a reading text, not a diplomatic
  transcript: sentences and punctuation follow meaning. Implemented as `<text>/<p>`
  with the raw cue stream kept in `<source>`; `assemble()` in `build_xml.py` does a
  first pass (sentence punctuation at cue boundaries by meaning, duplicate sentences
  dropped, ~55-word paragraphs), and a per-turn `text:` override in the attribution
  YAML handles the cases where the machine pass reads badly.
* **D2 Moderator → resolved.** Поли Златарева (Poli Zlatareva), `verified="true"`.
* **D3 Header image → resolved.** `assets/images/debate-header.png`, credit on the
  cover; rights with БНТ.
* **D4 PDF toolchain → resolved.** HTML/CSS + headless Chrome (see §9).
* **D5 Anchors → resolved.** Yes: section (`#s01`) and turn (`#t042`) ids exist in
  HTML and are preserved as internal links in the PDF.

Still open:

* **D6 Copy-editing.** The readability pass fixes punctuation and sentence breaks,
  but grammar/case errors remain (`българският интерес` → `българския`, dropped
  auxiliary verbs). Do we edit grammar aggressively across the whole text, or only
  where the meaning is at risk? Current practice: per-case corrections with a `why`.
* **D7 PDF outline → resolved.** `scripts/add_outline.py` (pypdf) adds a nested
  outline after Chrome prints: sections, then each turn with its time and speaker.
* **D8 Turn index.** For a 1h51m document, a clickable index of turns by time would
  help navigation. Not built yet.
* **D10 Correction integrity.** Fixed 2026-10-31 after an audit: corrections are keyed
  per cue as a list (a cue can carry several), and the build now **aborts** if any
  correction in the covered range never matched the text. This caught five dead
  entries (wrong cue numbers) and a shadowed duplicate. Expect the same guard for
  `<unclear>` entries if they multiply.
* **D9 Editorial authority.** Confirmed 2026-10-31: where the transcript and the
  editor's listening disagree, the editor wins, and the change is logged as a
  correction with the editor named as source. This is why cue 562 reads
  «Край, свърши.» although the ASR only has «свърши».

---

## 12. Glossary

| Term | Meaning |
| --- | --- |
| реплика | utterance/turn |
| водеща | (female) moderator — the debate's anchor |
| служебен кабинет | caretaker government |
| домова книга | the informal list of candidate caretaker PMs (Constitution, art. 99) |
| балотаж | runoff (second round) |
| ЦИК | Central Election Commission (draw determines speaking order) |
| Коалиция на желаещите | "coalition of the willing" |
| `n` | line number in the raw transcript = cue id |
