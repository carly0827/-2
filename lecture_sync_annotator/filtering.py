from __future__ import annotations

import re
from typing import Iterable

from .models import PageData, PageMatch
from .utils import clean_text


EXERCISE_PATTERNS = [
    r"기출",
    r"연습문제",
    r"문제",
    r"quiz",
    r"퀴즈",
    r"case\s*study",
    r"증례",
    r"문항",
    r"다음.*옳",
    r"다음.*고르",
    r"문제풀이",
    r"self[- ]?test",
    r"review\s*question",
]


def _count_pattern_hits(text: str, patterns: Iterable[str]) -> int:
    count = 0
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            count += 1
    return count


def _looks_like_exercise_page(page_text: str) -> bool:
    text = clean_text(page_text)
    if not text:
        return False

    hits = _count_pattern_hits(text, EXERCISE_PATTERNS)
    numbered = len(re.findall(r"(?:^|\n|\s)(?:\d+\.|[①-⑤]|[ㄱ-ㅎ]\.)", text))
    questions = text.count("?") + text.count("？")

    # Many question markers / numbered choices are strong hints.
    if hits >= 2:
        return True
    if hits >= 1 and (numbered >= 3 or questions >= 2):
        return True
    return False


def apply_skip_rules(
    page: PageData,
    match: PageMatch,
    *,
    min_score_for_content: float = 0.22,
    min_transcript_chars: int = 80,
) -> PageMatch:
    transcript_text = clean_text(" ".join(seg.text for seg in match.matched_segments))
    looks_like_exercise = _looks_like_exercise_page(page.text)

    # Hard skip: practice/exam page with little or no professor explanation.
    if looks_like_exercise and (
        match.score < min_score_for_content or len(transcript_text) < min_transcript_chars
    ):
        match.is_skipped = True
        match.skip_reason = "연습/기출 문제 페이지로 보이고 대응되는 교수님 설명이 거의 없어 건너뜀"
        match.highlight_terms = []
        match.side_notes = []
        match.figure_notes = []
        match.bottom_summary = ""
        return match

    # Soft skip: almost no aligned explanation regardless of page type.
    if match.score < 0.10 and len(transcript_text) < 40:
        match.is_skipped = True
        match.skip_reason = "대응되는 교수님 설명을 충분히 찾지 못해 건너뜀"
        match.highlight_terms = []
        match.side_notes = []
        match.figure_notes = []
        match.bottom_summary = ""
        return match

    return match
