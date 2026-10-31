"""Verify that the raw transcript is byte-identical to the source we attributed.

Run this before trusting any cue numbers: if the raw file changes, every
`n` reference in data/attribution/*.yml points at the wrong line.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "source" / "transcript-raw.txt"
SOURCE_MD = REPO / "data" / "source" / "SOURCE.md"


def main() -> int:
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    if not SOURCE_MD.exists():
        print(f"missing {SOURCE_MD}; run scripts/record_source.py")
        return 1
    recorded = None
    for line in SOURCE_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("sha256:"):
            recorded = line.split(":", 1)[1].strip()
    if recorded != digest:
        print(f"MISMATCH\n  recorded: {recorded}\n  actual:   {digest}")
        return 1
    print(f"ok: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
