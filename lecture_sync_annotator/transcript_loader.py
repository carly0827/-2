from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from .models import TranscriptSegment
from .utils import clean_text


def _load_json(path: Path) -> List[TranscriptSegment]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items: List[TranscriptSegment] = []
    for row in raw:
        items.append(
            TranscriptSegment(
                start=float(row.get("start", 0.0)),
                end=float(row.get("end", 0.0)),
                text=clean_text(str(row.get("text", ""))),
            )
        )
    return [x for x in items if x.text]


def _parse_srt_timestamp(value: str) -> float:
    m = re.match(r"(\d+):(\d+):(\d+),(\d+)", value.strip())
    if not m:
        return 0.0
    hh, mm, ss, ms = map(int, m.groups())
    return hh * 3600 + mm * 60 + ss + ms / 1000.0


def _load_srt(path: Path) -> List[TranscriptSegment]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text.strip())
    items: List[TranscriptSegment] = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        ts_line = lines[1] if "-->" in lines[1] else lines[0]
        if "-->" not in ts_line:
            continue
        start_s, end_s = [x.strip() for x in ts_line.split("-->")]
        body = " ".join(lines[2:] if "-->" in lines[1] else lines[1:])
        items.append(
            TranscriptSegment(
                start=_parse_srt_timestamp(start_s),
                end=_parse_srt_timestamp(end_s),
                text=clean_text(body),
            )
        )
    return [x for x in items if x.text]


def _load_txt(path: Path) -> List[TranscriptSegment]:
    lines = [clean_text(x) for x in path.read_text(encoding="utf-8").splitlines()]
    lines = [x for x in lines if x]
    items: List[TranscriptSegment] = []
    cur = 0.0
    for line in lines:
        dur = max(4.0, min(18.0, len(line) / 7.0))
        items.append(TranscriptSegment(start=cur, end=cur + dur, text=line))
        cur += dur
    return items


def load_transcript(path: str | Path) -> List[TranscriptSegment]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path)
    if suffix == ".srt":
        return _load_srt(path)
    return _load_txt(path)
