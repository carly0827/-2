from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import fitz

from .models import PageData, PageMatch, SideNote, FigureNote
from .utils import save_json


HIGHLIGHT_COLOR = (0.85, 0.95, 0.65)
NOTE_FILL = (0.93, 0.98, 0.92)
FIGURE_FILL = (0.95, 0.96, 1.0)
RIGHT_FILL = (0.98, 0.98, 0.98)
BOTTOM_FILL = (1.0, 0.98, 0.90)
BORDER = (0.72, 0.76, 0.72)


def _draw_box(page: fitz.Page, rect: fitz.Rect, fill, border=BORDER, width: float = 0.8) -> None:
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=border, fill=fill, width=width)
    shape.commit()


def _insert_text(page: fitz.Page, rect: fitz.Rect, text: str, fontsize: float = 9.0) -> None:
    page.insert_textbox(rect, text, fontsize=fontsize, lineheight=1.18)


def _safe_note_rect(anchor: fitz.Rect, page_rect: fitz.Rect, width: float = 180, height: float = 74) -> fitz.Rect:
    x0 = min(page_rect.x1 - width - 12, anchor.x1 + 6)
    y0 = max(page_rect.y0 + 8, anchor.y0)
    if x0 < page_rect.x0 + 6:
        x0 = page_rect.x0 + 6
    y1 = min(page_rect.y1 - 8, y0 + height)
    return fitz.Rect(x0, y0, x0 + width, y1)


def _highlight_terms(page: fitz.Page, terms: List[str]) -> None:
    for term in terms:
        rects = page.search_for(term, quads=False)
        for rect in rects[:3]:
            try:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.update()
            except Exception:
                # fallback: draw translucent rectangle
                shape = page.new_shape()
                shape.draw_rect(rect)
                shape.finish(color=None, fill=HIGHLIGHT_COLOR, fill_opacity=0.35)
                shape.commit()


def _add_in_slide_notes(page: fitz.Page, notes: List[SideNote], slide_rect: fitz.Rect) -> None:
    for note in notes:
        rect = _safe_note_rect(note.anchor, slide_rect)
        _draw_box(page, rect, fill=NOTE_FILL)
        _insert_text(page, rect + (5, 5, -5, -5), note.text, fontsize=8.2)


def _add_figure_notes(page: fitz.Page, notes: List[FigureNote], slide_rect: fitz.Rect) -> None:
    for note in notes:
        anchor = note.anchor
        width = 200
        height = 96
        x0 = min(slide_rect.x1 - width - 10, anchor.x1 + 8)
        y0 = min(slide_rect.y1 - height - 10, max(slide_rect.y0 + 10, anchor.y0))
        if x0 < slide_rect.x0 + 10:
            x0 = max(slide_rect.x0 + 10, anchor.x0 - width - 8)
        rect = fitz.Rect(x0, y0, x0 + width, y0 + height)
        _draw_box(page, rect, fill=FIGURE_FILL)
        _insert_text(page, rect + (6, 6, -6, -6), note.text, fontsize=8.0)


def render_study_pdf(
    source_pdf: str | Path,
    pages: List[PageData],
    matches: List[PageMatch],
    outdir: str | Path,
    right_panel_ratio: float = 0.34,
    bottom_ratio: float = 0.24,
) -> Tuple[Path, Path]:
    source_pdf = Path(source_pdf)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    src = fitz.open(source_pdf)
    out = fitz.open()

    matches_by_index = {m.page_index: m for m in matches}

    for page_data in pages:
        src_page = src[page_data.page_index]
        src_rect = src_page.rect

        right_w = max(220, src_rect.width * right_panel_ratio)
        bottom_h = max(140, src_rect.height * bottom_ratio)

        new_w = src_rect.width + right_w
        new_h = src_rect.height + bottom_h
        new_page = out.new_page(width=new_w, height=new_h)

        slide_rect = fitz.Rect(0, 0, src_rect.width, src_rect.height)
        right_rect = fitz.Rect(src_rect.width, 0, new_w, src_rect.height)
        bottom_rect = fitz.Rect(0, src_rect.height, new_w, new_h)

        new_page.show_pdf_page(slide_rect, src, page_data.page_index)

        match = matches_by_index[page_data.page_index]
        if match.is_skipped:
            continue
        _highlight_terms(new_page, match.highlight_terms)

        _draw_box(new_page, right_rect, fill=RIGHT_FILL)
        _draw_box(new_page, bottom_rect, fill=BOTTOM_FILL)

        # Right panel title
        title_rect = fitz.Rect(right_rect.x0 + 8, right_rect.y0 + 8, right_rect.x1 - 8, right_rect.y0 + 28)
        _insert_text(new_page, title_rect, f"교수님 설명 원문 | p.{page_data.page_index + 1}", fontsize=11)

        transcript_rect = fitz.Rect(right_rect.x0 + 10, right_rect.y0 + 30, right_rect.x1 - 10, right_rect.y1 - 10)
        transcript_text = match.raw_transcript or "이 페이지에 대응되는 전사 원문을 찾지 못했습니다."
        _insert_text(new_page, transcript_rect, transcript_text, fontsize=8.7)

        # Bottom summary
        summary_title = fitz.Rect(bottom_rect.x0 + 10, bottom_rect.y0 + 6, bottom_rect.x1 - 10, bottom_rect.y0 + 26)
        _insert_text(new_page, summary_title, "페이지 전체 정리", fontsize=11)
        summary_body = fitz.Rect(bottom_rect.x0 + 10, bottom_rect.y0 + 26, bottom_rect.x1 - 10, bottom_rect.y1 - 10)
        _insert_text(new_page, summary_body, match.bottom_summary or "요약 없음", fontsize=8.8)

        _add_in_slide_notes(new_page, match.side_notes, slide_rect)
        _add_figure_notes(new_page, match.figure_notes, slide_rect)

    pdf_path = outdir / "annotated_notes.pdf"
    out.save(pdf_path)
    out.close()
    src.close()

    debug_data = []
    for m in matches:
        debug_data.append({
            "page_index": m.page_index,
            "score": m.score,
            "highlight_terms": m.highlight_terms,
            "raw_transcript": m.raw_transcript,
            "bottom_summary": m.bottom_summary,
            "side_notes": [n.text for n in m.side_notes],
            "figure_notes": [n.text for n in m.figure_notes],
            "is_skipped": m.is_skipped,
            "skip_reason": m.skip_reason,
            "debug": m.debug,
        })

    json_path = outdir / "page_matches.json"
    save_json(json_path, debug_data)
    return pdf_path, json_path
