"""Parser for the raw Whisper transcript of the Yotova–Gyurov debate (BNT, 2026-10-29).

The raw file is one cue per line:

    [0:00:20] Здравейте! Започва дебатът, който всички очакват, ...

Cue identifiers used throughout this project are the **1-based line numbers of the
raw file** (``n``). They are stable as long as the raw file is byte-identical, which
is enforced by the SHA-256 recorded in ``data/source/SOURCE.md`` and checked by
``scripts/check_source.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = REPO_ROOT / "data" / "source" / "transcript-raw.txt"

CUE_RE = re.compile(r"^\[(\d+):(\d{2}):(\d{2})\]\s?(.*)$")


@dataclass(frozen=True)
class Cue:
    n: int          # 1-based line number in the raw file (== stable cue id)
    sec: int        # offset from start of the recording
    tc: str         # "H:MM:SS" exactly as printed in the source
    text: str       # verbatim ASR text, whitespace-trimmed

    def as_dict(self) -> dict:
        return asdict(self)


def load_cues(path: Path | str = RAW_PATH) -> tuple[list[str], dict[int, Cue]]:
    """Return (header_lines, {n: Cue})."""
    header: list[str] = []
    cues: dict[int, Cue] = {}
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.rstrip("\r\n")
            m = CUE_RE.match(line)
            if m:
                h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
                cues[lineno] = Cue(
                    n=lineno,
                    sec=h * 3600 + mi * 60 + s,
                    tc=f"{h}:{mi:02d}:{s:02d}",
                    text=" ".join(m.group(4).split()),
                )
            else:
                header.append(line)
    return header, cues


def fmt_tc(sec: int) -> str:
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


if __name__ == "__main__":
    header, cues = load_cues()
    print(f"header lines: {len(header)}")
    print(f"cues: {len(cues)}  first={cues[min(cues)].tc}  last={cues[max(cues)].tc}")
    dur = cues[max(cues)].sec - cues[min(cues)].sec
    print(f"span: {fmt_tc(dur)} ({dur}s)")
    words = sum(len(c.text.split()) for c in cues.values())
    print(f"words: {words}  chars: {sum(len(c.text) for c in cues.values())}")
