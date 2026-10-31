# Source of the transcript

## What we downloaded

| | |
| --- | --- |
| Gist author | **BorisThoris** (GitHub) — the person who made the transcript |
| URL | https://gist.github.com/BorisThoris/f29a74bbf0acba4ad583a74ab71404c9 |
| Raw URL | https://gist.githubusercontent.com/BorisThoris/f29a74bbf0acba4ad583a74ab71404c9/raw/8591e80d17a41dde52a77ed692f1623bb5999523/debat-yotova-gyurov-bnt-2026-10-29.txt |
| Gist revision | `8591e80d17a41dde52a77ed692f1623bb5999523` |
| Gist created | 2026-10-29 23:32 (per GitHub page) |
| Retrieved | 2026-10-31 |
| Local copy | `data/source/transcript-raw.txt` (byte-identical, CRLF/LF mix preserved) |
| Lines | 1833 (3 header lines + 1830 cues) |
| Size | 189 253 bytes, UTF-8 |
| sha256 | `83b8f6c64c282bad9d07a92e2924cd44725a16e118852fe0cb6d6935050b6c78` |

Verify with:

```bash
python3 scripts/check_source.py
```

## What the source claims about itself

The gist's own header says:

> Дебат между Илияна Йотова и Андрей Гюров (БНТ), 29.10.2026
> Автоматичен препис (Whisper large-v3) без отбелязване кой говори; възможни са грешки в отделни думи. Времената са от началото на записа.

Three consequences that shape the whole project:

1. **No speaker labels exist in the source.** Every speaker attribution in `build/debate.xml`
   is our inference; it is not in the data we started from.
2. **The timestamps are the only reliable segmentation.** They are offsets from the start of
   the recording, not broadcast clock time.
3. **The ASR text contains errors** (e.g. «егитални», «Малчанието», «Черноморе», «има стъра»).
   We correct the obvious ones and log every change; we never silently "improve" the wording.

## Cue numbering (important)

`n` in `data/attribution/*.yml` and in `<seg n="…">` is the **line number in the raw file**,
not an index of cues. Line 1–3 are header lines, so the first cue is `n=4` and the last is
`n=1833`. Keeping the raw file byte-identical is therefore a hard requirement: any edit shifts
every reference. `scripts/check_source.py` guards this.

## Credit

The transcript was produced and published by **BorisThoris**. Credit him by name
whenever this material is reused — the README, the XML `<credit>` elements and the
rendered header all do. If you cite the debate, cite three layers: the broadcast
(БНТ, 29.10.2026), the transcript (BorisThoris) and this derived editing.

## Licensing / reuse

No licence is stated on the gist. The underlying material is a broadcast of БНТ and the speech
of the participants. Treat the transcript as an unofficial working copy: do not redistribute the
raw file as an authoritative record, and quote with attribution to the broadcast (БНТ, 29.10.2026),
not to this repository.

## Known gaps in the source recording

The transcript jumps over two stretches — the audio behind them is simply missing:

| From | To | What is missing |
| --- | --- | --- |
| 1:31:27 | 1:31:57 | the middle of Gyurov's answer about the medical commission |
| 1:37:43 | 1:38:18 | the end of the moderator's transition and the start of a question |

Both are recorded as `<gap>` in the XML and must never be filled in from imagination.

## Checksum record (machine-readable)

sha256: 83b8f6c64c282bad9d07a92e2924cd44725a16e118852fe0cb6d6935050b6c78
