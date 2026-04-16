from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def one_line(text: str) -> str:
    return clean_text(text).replace("\n", " ")


def split_sentences(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+|\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, max_chars: int = 280) -> List[str]:
    chunks: List[str] = []
    cur = ""
    for sent in split_sentences(text):
        if not cur:
            cur = sent
            continue
        if len(cur) + 1 + len(sent) <= max_chars:
            cur += " " + sent
        else:
            chunks.append(cur)
            cur = sent
    if cur:
        chunks.append(cur)
    return chunks


def to_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def flatten(list_of_lists: Iterable[Iterable[str]]) -> List[str]:
    out: List[str] = []
    for chunk in list_of_lists:
        out.extend(chunk)
    return out
