from __future__ import annotations

from typing import List

from .models import PageData, PageMatch, FigureNote, ImageBlock
from .utils import split_sentences


def _guess_figure_note(page: PageData, match: PageMatch, image_index: int) -> str:
    title_hint = split_sentences(page.text)[:3]
    transcript = split_sentences(" ".join(seg.text for seg in match.matched_segments))[:4]

    pieces: List[str] = []
    if title_hint:
        pieces.append("슬라이드 문맥: " + " ".join(title_hint[:2]))
    if transcript:
        pieces.append("교수님 설명 연결: " + " ".join(transcript[:2]))
    if not pieces:
        pieces.append(f"그림 {image_index + 1}: 이 페이지의 핵심 구조를 보여주는 도식일 가능성이 큽니다.")
    return "\n".join(pieces)


def build_figure_notes(page: PageData, match: PageMatch, max_figures: int = 3) -> List[FigureNote]:
    notes: List[FigureNote] = []
    images = sorted(page.images, key=lambda img: (img.bbox.y0, img.bbox.x0))[:max_figures]
    for idx, image in enumerate(images):
        text = _guess_figure_note(page, match, idx)
        notes.append(FigureNote(anchor=image.bbox, text=text, kind="figure_note"))
    return notes
