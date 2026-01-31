#!/usr/bin/env python3
"""Update grades_summary.json from repos-management/grades_summary.toml.

Schema (per course/year/variant grade entry):
  grade = {
    "raw": <original string>,
    "items": [ {"name": <str>, "percent": <str>} ... ],
    "note": <str | null>
  }

Rationale:
- Always preserves the original text in `raw`.
- Provides a structured list in `items` when parseable.
- Captures any leftover/annotation text in `note`.
"""

from __future__ import annotations

import json
import re
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

SOURCE_URL = (
    "https://raw.githubusercontent.com/HITSZ-OpenAuto/repos-management/main/grades_summary.toml"
)
OUT_PATH = Path(__file__).resolve().parents[1] / "src/hoa_majors/data/grades_summary.json"

PERCENT_RE = re.compile(r"(\d+%)")


def parse_grade(raw: str) -> dict[str, Any]:
    """Parse a grade string into a structured object.

    We aim for best-effort parsing while keeping raw text intact.
    """

    raw_norm = raw.replace("＋", "+")

    # Split on '+' only when it likely separates components.
    # - "... 30%+ ..." (plus right after a percent)
    # - "... + ..." (plus surrounded by whitespace)
    # This avoids splitting merged names like "作业+实验 50%".
    split_re = r"(?<=%)\s*\+\s*|\s+\+\s+"
    parts = [p.strip() for p in re.split(split_re, raw_norm) if p.strip()]

    items: list[dict[str, str]] = []
    notes: list[str] = []

    for part in parts or [raw_norm.strip()]:
        m = PERCENT_RE.search(part)
        if not m:
            # Not parseable as a (name, percent) pair.
            notes.append(part)
            continue

        percent = m.group(1)
        name = part[: m.start()].strip()
        tail = part[m.end() :].strip()

        # If the "name" is empty, treat as note to avoid producing nonsense keys.
        if not name:
            notes.append(part)
            continue

        items.append({"name": name, "percent": percent})
        if tail:
            notes.append(tail)

    note = " ".join(n for n in notes if n).strip() or None
    return {"raw": raw, "items": items, "note": note}


def transform(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k == "grade" and isinstance(v, str):
                obj[k] = parse_grade(v)
            else:
                transform(v)
    elif isinstance(obj, list):
        for v in obj:
            transform(v)


def main() -> None:
    raw_bytes = urllib.request.urlopen(SOURCE_URL).read()
    data = tomllib.loads(raw_bytes.decode("utf-8"))

    transform(data)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
