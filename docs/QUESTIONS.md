# Open questions and review items

This file is the conversation between the editor (human) and the agent. Add a
question here when a decision is needed; record the answer under *Decisions taken*.
Never resolve an open question silently in the data.

---

## Decisions taken

| # | Question | Decision (2026-10-31) |
| --- | --- | --- |
| D0.1 | Candidate name: the brief said "Yordanka Yotova" | **Илияна Йотова / Iliana Yotova** — matches the gist header, the transcript and ballot № 25 |
| D0.2 | How to represent simultaneous speech | **Brief interjections nested as `<aside>`; floor grabs as a separate `<turn overlap interrupts>`** |
| D0.3 | How to treat ASR errors | **Correct in the XML, keep originals in `<appendix>/<corrections>`; never correct what is merely unclear** |
| D0.4 | Working pace | **Section by section, user reviews after each section** |
| D1 | Punctuation / sentence boundaries | **Reading text, not diplomatic transcript: punctuation and sentences follow meaning.** Raw cue stream preserved in `<source>`; per-turn `text:` overrides where the machine pass reads badly |
| D2 | Moderator's name | **Поли Златарева (Poli Zlatareva)** — supplied by the editor, `verified="true"` |
| D3 | Header image | **flagman.bg still, `assets/images/debate-header.png`**, credited on the cover, rights with БНТ |
| D4 | PDF toolchain | **HTML + CSS, printed with headless Chrome** (WeasyPrint blocked by libpango/libfontconfig conflict on this machine) |
| D5 | Anchors in the PDF | **Yes** — `#s01`/`#t042` anchors survive as internal links; section navigation from the ToC works |

---

## Audit round — 2026-10-31

An independent read-only audit of the rendered text (language, syntax,
terminology, attribution logic) produced 52 findings. Applied in this round:

* **Correction integrity** — corrections are now a per-cue list, and the build
  aborts on any entry that never matches. Five dead entries fixed (wrong cue
  numbers: 153→152, 161→160, 453→454, 499→497, 518→521), a shadowed duplicate at
  555 unshelved, and the appendix no longer advertises fixes that did not happen.
* **Terminology** — Стуб, Асен Василев, ООН, Нормандска-4, Скопие, Дертлиев,
  «Прогресивна България», Коалицията на желаещите, Република България.
* **Sentence boundaries** — three cues that had been split mid-sentence merged
  (252–253, 360–361, 368–369); duplicated sentence removed.
* **Root-cause bug** — the abbreviation guard matched the final «с.» inside
  «въпрос.», which silently disabled sentence splitting for any word ending in ‑с.
* **Unclear markers** — now rendered inline as `[неясно]`, and four entries
  re-pointed to the cue that actually contains the garbled words.
* **Attribution** — `t035` marked as an overlap/interruption (Yotova cutting into
  the moderator's invitation to Gyurov).

One finding is **not** resolved and needs a listening check:

> **0:33:02 · cues 551–553** — «Това, което виждаме, са близо 400 милиона долара,
> които ние дължим и които ще докарат до фалит Булгаргаз. Сега не правителството
> българското спря доставките на газ, а Газпром…»
>
> Currently `t069`, assigned to **Yotova** with `confidence="low"`. The audit argues
> it is **Gyurov** (it continues his «ние не виждаме никаква полезност», and it
> attacks the very Botas deal Yotova had just defended). A third reading: 551–552
> Gyurov, 553 Yotova. See `amb-a09`.

## Open

### Q1 — Punctuation — RESOLVED (see D1)

The document is a reading text. Sentences and punctuation follow meaning; the
literal ASR stream is kept for audit in `<source>`. Remaining work is grammar
copy-editing (D6), not punctuation.

Whisper often ends a cue without punctuation, and because cues are joined inside a
turn the result reads badly:

> **Водеща (Златарева)** · `0:31:09`
> Само секунда Ще имате право на реплика Както аз ви чакам, така ще чакате и вие

Options:

1. **Editorial punctuation pass with a change log** (recommended): an editor adds
   sentence punctuation and capitalisation, every change recorded like an ASR fix.
   Cost: manual work over 1830 cues; risk: editorial interpretation of intonation.
2. **Render as-is**: fully faithful, reads like an unedited stream.
3. **Re-segment sentences** in the XML (`<s>` elements), which also fixes
   paragraphing for the PDF but is the largest change to the data model.

### Q2 — Moderator's full name — RESOLVED (Поли Златарева)



Only «Златарева» is recoverable (Yotova addresses her: «Добър вечер, госпожо
Златарева»). The XML has `verified="false"`. If you can supply the full name from
the BNT credits, it goes into `data/debate.yml` and the table in AGENTS.md §3.

### Q3 — Header images — RESOLVED

`assets/images/debate-header.png` (1300×975, split-screen still of both candidates,
published by flagman.bg from the BNT broadcast). Cover credit: «Кадър: БНТ,
излъчване на 29.10.2026 г. Изображението е публикувано от flagman.bg…». Rights
remain with БНТ — do not reuse the image outside this document without permission.

### Q4 — PDF toolchain — RESOLVED

HTML + CSS (`assets/styles/debate.css`), body in **Source Serif 4**, headings in
**Ysabeau** — both with Bulgarian Cyrillic localised forms. Rendered by headless
Chrome (`make pdf`). WeasyPrint is documented as broken here (conda fontconfig
1.12 vs system pango); see AGENTS.md §9.

### Q7 — PDF navigation — RESOLVED

The PDF now has a nested outline (pypdf post-processing): sections + every turn
with its timestamp. Internal anchors work as links. The ToC still lists start
times rather than page numbers (Chrome does not support `target-counter`).

### Q5 — Publication form — RESOLVED

Both are possible from the same HTML: it opens in a browser and prints to PDF.
Turn ids are stable (`#t042`), so a web edition with per-turn permalinks is a
rendering choice, not a data change. PDF internal links already work.

---

## Section 3 review — resolved (2026-10-31)

The editor reviewed all eight items against the recording. Outcome, with the
timestamp and the text as it now stands:

| # | Време | Текст | Решение |
| --- | --- | --- | --- |
| 1 | 0:20:33 · ред 312 | «своето участие. Госпожо, и от това? Освен това,» | «Госпожо, и от това?» е кратка вметка на **Златарева** към Йотова (потвърдено при финалния преглед на 2026-10-31); Йотова продължава с «Освен това…». Моделирано като `<aside>` в `t035`. `amb-a02` — затворен. |
| 2 | 0:21:44–0:21:59 · редове 347–354 | «Ще се съглася само за тази необходимост.» / «Една реплика и не повече моля.» | Водещата се опитва да спре Йотова още в първото изречение, но едва се чува; ред 350 е уточнението ѝ «една реплика». Отбелязано като `overlap` с `confidence="low"`. |
| 3 | 0:27:07 · редове 459–470 | «Нека само да поясня, тук не става въпрос за война на изтощение…» | **Гюров просто поема думата** — не е прекъсване. Махнати `overlap` и `interrupts`. |
| 4 | 0:31:07–0:31:18 · редове 525–531 | «Моля за репликата» / «Само секунда» / «Ще имате право на реплика» / «Както аз ви чакам…» / «Само да не ми хапвате от секундите» / «Не, няма.» | **Гюров · Йотова · Златарева · Йотова (528–530) · Златарева.** Добавена бележка, че двамата говорят един върху друг и част от думите не се разбират. |
| 5 | 0:31:50–0:31:51 · редове 540–541 | «Добре, да, така е.» / «Боташ искаше…» | **Златарева** (540) и **Йотова** (541) — две отделни реплики. `amb-a07` — затворен. |
| 6 | 0:32:06 · ред 546 | «Това е абсолютна манипулация.» | **Гюров** — потвърдено. `amb-a08` — затворен. |
| 7 | 0:34:17 · ред 562 | «свърши.» | Това е **намеса на водещата: «Край, свърши.»**; думата «край» не е разпозната. Възстановена като корекция; Гюров довършва «Ние имаме шанс да го направим.» след нея. |
| 8 | 0:22:21–0:22:25 · редове 366–368 | «запласти? Точно за това е следващият ми въпрос.» | **Водещата** повтаря и продължава да задава въпроса. `amb-a04` — затворен. |

Consequence: sections 1–3 now have 70 turns (t001–t070); the old `t054`–`t068`
were renumbered to `t054`–`t070`, and `interrupts` references were updated.

---

## Apparatus cleanup — 2026-10-31 (with section 4)

Four `<unclear>` entries were removed because the same words are already resolved by
a correction, and the two markers contradicted each other in the rendered text:

* cue 562 — rendered «Край, свърши. [неясно].» although the editor had confirmed
  «Край, свърши.»; the correction stays, the unclear marker goes.
* cue 555 — «че той било» is corrected to «че то е било».
* cue 128 — «спрямо с Копи» is corrected to «спрямо Скопие».
* cue 318 — «нощани» is corrected to «нонсенси».

Unclear spots: 17 → 13. Corrections unchanged (102). The build does not yet guard
against this class of contradiction — see `HANDOFF.md`, trap 10.

---

## Section 4 review — open (attributed 2026-10-31)

Section 4 (cues 563–680, 0:34:19–0:40:21) has 18 turns, `t071`–`t088`. The
attribution is complete and tiles the section, but six points need the editor's
ears before the section can be called reviewed. Each row carries the clock time,
the cue lines and the text as it now stands.

| # | Време | Редове | Текст | Решение |
| --- | --- | --- | --- | --- |
| 1 | 0:39:11–0:40:21 | 645–680 | «Българската индустрия се развива твърде добре…» / «В момента българската индустрия е под напрежение…» | **Йотова защитава развитието (645–654), Гюров отговаря, че е под напрежение (656–680).** Потвърдено. `amb-a11` — затворен. |
| 2 | 0:35:38–0:35:57 | 602–608 | «Само още едно допълнение. … многонационална бригада тук.» / «А що се отнася до това за Варшавския договор?…» | **Йотова говори от 602 нататък, включително за Варшавския договор.** `t074` = 588–601, `t075` = 602–608, и двете `high`. `amb-a10` — затворен. |
| 3 | 0:37:25 | 623 | «Може ли един въпрос?» | **Йотова пита** — остава начало на `t080`. Потвърдено. |
| 4 | 0:36:26–0:36:29 | 613–614 | «Само, че тук имам право наистина на една задължителна реплика.» / «Имате секунди, имате секунди въобще и възможност.» | **Вметката за секундите е на Златарева** — `<aside>` в `t078`, както е моделирано. Потвърдено. |
| 5 | 0:38:44–0:39:01 | 637–642 | «Това, което осветиха тези държавници…» | Думата е **«осуетиха»**, не «осветиха». Коригирано в 635 и 637 („които осуетиха изпращането“, „Това, което осуетиха тези държавници“). |
| 6 | 0:35:57 | 608 | «Много отдавна, помните, господин Гюров?» | **Остава както е в транскрипта** („помните“, не „помните ли“). |

Пет от шестте точки са потвърдени, една (№5) е поправена по слух; нищо в
атрибуцията на s04 не се промени освен разделянето `t074`/`t075`.

Отбелязано за преглед, но **не** двусмислено: 0:34:52–0:34:58 (581–582) —
изричното предаване «Госпожа Йотова.»; 0:35:09 (588) — редът държи две реплики
(«Андрей Гюров.» / «Разбира се.»), разделени с `start_at`; 0:36:53 (619) —
Гюров отговаря на обвинението на Йотова.

---

## Final review — the nine open ambiguities (whole recording, 2026-10-31)

The whole transcript is now attributed (288 turns, 11 sections). What is left is
review, not coverage: nine attribution doubts need the editor's ears. They are also
in the PDF appendix („Двусмислени места“) with the readings considered, and in
`build/debate.xml` as `<ambiguity status="open">`.

| # | Време | Редове | Id | Решение (2026-10-31) |
| --- | --- | --- | --- | --- |
| 1 | 1:23:51–1:24:51 | 1363–1385 | `amb-a15` | **Йотова** задава въпроса за «възродителния процес» (1376–1385); Гюров отговаря в 1386–1391 и после 1397–1410. `t180` е Йотова, `t181` — Гюров. Въпросите на Гюров остават два: медии (1319) и помилвания (1426). |
| 2 | 0:39:11–0:40:21 | 645–680 | `amb-a11` | Виж s04, точка 1: Йотова → развитие, Гюров → под напрежение. |
| 3 | 1:07:31–1:08:04 | 1035–1052 | `amb-a14` | **Йотова** обяснява възражението на Конституционния съд. `t140` остава един turn. |
| 4 | 0:45:45–0:46:30 | 755–761 | `amb-a12` | **Йотова атакува** (755–756); Гюров отговаря (757–758); Йотова продължава (759–761). |
| 5 | 1:10:15–1:10:30 | 1110–1115 | `amb-a13` | Тук са **само Йотова и водещата**: 1110–1111, 1113, 1115 — Йотова; 1112, 1114 — Златарева. `t151` вече е Йотова. |
| 6 | 0:35:38–0:35:57 | 602–608 | `amb-a10` | Виж s04, точка 2: Йотова от 602. |
| 7 | 0:33:02 | 551–553 | `amb-a09` | **Остава отворен**: редакторът не открива пасажа на това време в записа. `t069` остава `confidence="low"`. |
| 8 | 0:16:02 | 225 | `amb-a01` | **Йотова**, после Гюров продължава от 228 с «Това, което исках да кажа също е…». `t026` вече е с `high` на вметката. |
| 9 | 0:00:20–0:00:52 | 4–8 | `amb-a05` | **Водещата.** Говорителите остават три. |

Осем от деветте са затворени. Единствено `amb-a09` остава отворен — пасажът
не се открива на 0:33:02 в записа, вероятно заради разминаване на времената в
преписа; `t069` остава с `confidence="low"` до проверка.

Как се затваря един въпрос: `status: resolved` + `resolution` в
`data/corrections.yml`, после `make all`. Ако четенето се обърне, се променя и
`confidence` на съответния turn (или се разделя turn, както е описано в
`resolution` на `amb-a15`). Нищо не се решава „по подразбиране“.

Дребните бележки от прегледа на s04 (0:37:25 · ред 623 «Може ли един въпрос?»;
0:36:29 · ред 614 — вметката на водещата; 0:38:44–0:39:01 · редове 637–642
«осветиха»/«осъдиха»; 0:35:57 · ред 608 «помните»/«помните ли») остават
записани в таблицата по-горе и в бележките към `t080`, `t078`, `t084` и `t075`.
