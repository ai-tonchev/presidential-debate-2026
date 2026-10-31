# Method, confidence and limits

## What the source gives us

Whisper large-v3 output with timestamps and no speaker labels. The recording is
1:51:18 long and is cut into 1830 cues, median cue length a few seconds. The
transcription is good on continuous speech and poor exactly where debates are
hard: short interjections, crosstalk, and numbers/names.

## What is machine-made and what is ours

| Layer | Produced by | Trust |
| --- | --- | --- |
| Words, timestamps | Whisper large-v3 (author of the gist) | medium: occasional errors, two gaps |
| Speaker attribution | deepseek-flash (DeepSeek Harness), reading the text | stated per turn |
| Topic sections | deepseek-flash, editorial decision | stated in `sections.yml` |
| ASR corrections | deepseek-flash, each one logged | listed in `corrections.yml` |
| Ambiguity resolutions | the editor, by ear, on top of the model's alternatives | listed in `corrections.yml` |

The machine chain never heard the audio. Only the editor's spot-checks did: the
flagged ambiguities and a handful of corrections were verified by ear, but the
recording as a whole was not transcribed or audited again. That is the single
biggest limitation and the reason the disclaimers exist.

## How a turn boundary is decided

1. **Explicit hand-off** — the moderator names the next speaker. Strongest signal:
   «Андрей Гюров.», «Реплика Илияна Йотова.», «Бърз отговор, Андрей Гюров.».
2. **Addressee shift** — the content tells you who is being addressed:
   «вашата теза, господин Гюров» (speaker: Yotova), «госпожо Йотова» (speaker:
   Gyurov). A speaker who refers to both candidates in the third person is the
   moderator.
3. **Procedural language** — «Имате още 30 секунди», «Следваме регламента»,
   «Моля ви» ⇒ moderator.
4. **Discourse pairing** — an answer follows a question; a rebuttal follows an
   accusation; «Отговорете, моля» re-opens the floor.

Where two signals conflict, the content wins over the name (people address each
other constantly, so a name is not a hand-off).

## Confidence rubric

| Level | Meaning | Consequence |
| --- | --- | --- |
| `high` | hand-off, or unambiguous addressee shift, or the turn is long enough that only one speaker could have said it | none |
| `medium` | inferred from topic continuity, from a sequence of short cues, or from an exchange that only makes sense one way | worth a second look during review |
| `low` | the fragment could plausibly belong to two speakers | must have an `<ambiguity>` entry with all readings |

Reviewers should read `low` and `medium` turns first; `high` turns are cheap to
spot-check.

## The text layer (decided 2026-10-31)

The document is a **reading text**, not a diplomatic transcript. Words are kept,
but punctuation and sentence boundaries follow meaning:

* `build_xml.py:assemble()` joins the ASR cues of a turn, inserts sentence
  punctuation where a new sentence clearly starts, drops sentences the recogniser
  emitted twice, and groups sentences into paragraphs of roughly 55 words.
* The literal cue stream is kept next to it in `<source>`, so any reader can diff
  "what Whisper gave" against "what we printed".
* Where the automatic pass produces a bad reading, the attribution YAML for that
  turn carries a `text:` override with the edited paragraphs. That is the escape
  hatch — it is data, not code.

## Deliberate modelling choices

* **One utterance = one turn.** A turn is not a paragraph and not a fixed time
  window; it ends when another voice takes over.
* **Asides stay inside.** A two-second «30 секунди.» does not deserve to split the
  candidate's answer in the data model; it is nested where it happened.
* **Mid-cue splits use character offsets.** Cue 88 contains two speakers; the XML
  records `to="16"` / `from="17"` so the exact boundary is reproducible.
* **Unclear stays unclear.** Garbled words are listed in `<unclear>` and marked in
  the rendering; they are not guessed from context.
* **Gaps stay gaps.** Two stretches of audio are missing from the source; they are
  recorded as `<gap>` and the document says so.

## The recording, not the transcript, is the authority

Whisper drops words, flattens names and misses short interjections. Where the
editor, listening to the broadcast, confirms speech that the ASR lost, the text is
restored and the change is logged like any other correction, with the editor named
as the source (`why`). Examples: «Край, свърши.» at cue 562 (ASR had only
«свърши»), and the six-line crosstalk at 0:31:07, where the raw cue-to-speaker
pairing was wrong and was corrected by ear.

What remains forbidden is plausible invention *without* a listening source — that
is what `<unclear>`, `<gap>` and `<ambiguity>` are for.

## What we did *not* do

* The machine pass did not listen to the broadcast, and the editor listened only
  to the flagged spots, so tone, laughter and off-screen voices remain unverified.
* We did not run speaker diarization (the source has none, and pyannote-style
  diarization would need the audio anyway).
* We did not "repair" the transcript beyond the logged corrections.
* We did not resolve political claims; the document records what was said, not
  whether it is true. Statements by candidates about each other are transcribed,
  not fact-checked.

## Known weaknesses

1. **Short turns are the risk zone.** A one-word «Да.» can belong to anyone.
   We mark these `medium`/`low` and note the reasoning.
2. **The opening 32 seconds may be an off-screen announcer**, not the moderator
   (`amb-a05`). Since the brief says exactly three speakers, we assign it to the
   moderator and keep the doubt on record.
3. **Punctuation is inconsistent** in the ASR (see D1 in AGENTS.md). The XML keeps
   what Whisper produced; a punctuation pass is a separate editorial decision.
4. **Timestamps are cue starts**, so a turn's `end` is the start of its last cue,
   not the moment the speaker stopped.

## Review checklist (for a human)

- [ ] Does every `low` turn make sense as an exchange with its neighbours?
- [ ] Are the `overlap` / `interrupts` pointers on the right side of the exchange?
- [ ] Do the asides sit in the right sentence of the host turn?
- [ ] Are corrections faithful (no meaning changed)?
- [ ] Did any gap get silently filled?
