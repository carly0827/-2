from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import fitz


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class ImageBlock:
    xref: int
    bbox: fitz.Rect
    width: int
    height: int
    ext: str = "png"


@dataclass
class TextBlock:
    bbox: fitz.Rect
    text: str


@dataclass
class PageData:
    page_index: int
    text: str
    rect: fitz.Rect
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageBlock] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class SideNote:
    anchor: fitz.Rect
    text: str
    kind: str = "text_note"


@dataclass
class FigureNote:
    anchor: fitz.Rect
    text: str
    kind: str = "figure_note"


@dataclass
class PageMatch:
    page_index: int
    score: float
    page_text: str
    matched_segments: List[TranscriptSegment] = field(default_factory=list)
    highlight_terms: List[str] = field(default_factory=list)
    side_notes: List[SideNote] = field(default_factory=list)
    figure_notes: List[FigureNote] = field(default_factory=list)
    bottom_summary: str = ""
    is_skipped: bool = False
    skip_reason: str = ""
    debug: Dict[str, Any] = field(default_factory=dict)

    @property
    def raw_transcript(self) -> str:
        return "\n".join(
            f"[{seg.start:06.1f}-{seg.end:06.1f}] {seg.text}"
            for seg in self.matched_segments
        )
