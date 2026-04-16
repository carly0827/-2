from __future__ import annotations

from typing import List

from .models import PageData, PageMatch, SideNote
from .utils import chunk_text, split_sentences


def build_side_notes(page: PageData, match: PageMatch, max_notes: int = 6) -> List[SideNote]:
    notes: List[SideNote] = []
    if not page.text_blocks:
        return notes

    transcript_chunks = chunk_text(" ".join(seg.text for seg in match.matched_segments), max_chars=90)
    if not transcript_chunks:
        return notes

    candidate_blocks = sorted(page.text_blocks, key=lambda b: (b.bbox.y0, b.bbox.x0))
    note_count = min(max_notes, len(candidate_blocks), len(transcript_chunks))

    for idx in range(note_count):
        block = candidate_blocks[idx]
        note_text = transcript_chunks[idx]
        notes.append(SideNote(anchor=block.bbox, text=note_text, kind="text_note"))
    return notes


def build_bottom_summary(match: PageMatch, max_sentences: int = 6) -> str:
    raw = " ".join(seg.text for seg in match.matched_segments)
    sents = split_sentences(raw)
    if not sents:
        return "이 페이지와 연결된 설명을 확실히 찾지 못했습니다."
    return " ".join(sents[:max_sentences])
