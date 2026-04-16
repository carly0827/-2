from __future__ import annotations

import argparse
from pathlib import Path

from .pdf_parser import extract_pages
from .transcript_loader import load_transcript
from .matcher import match_pages_to_segments
from .notes import build_side_notes, build_bottom_summary
from .figure_notes import build_figure_notes
from .renderer import render_study_pdf
from .filtering import apply_skip_rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="강의록 PDF + 전사본 -> 공부용 주석 PDF")
    parser.add_argument("--pdf", required=True, help="입력 PDF 경로")
    parser.add_argument("--transcript", required=True, help="전사본 경로(json/srt/txt)")
    parser.add_argument("--outdir", required=True, help="출력 폴더")
    parser.add_argument(
        "--model-name",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="sentence-transformers 모델 이름",
    )
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--min-score", type=float, default=0.14)
    parser.add_argument("--skip-exercise-pages", action="store_true", default=True, help="설명이 거의 없는 연습/기출 문제 페이지를 결과 PDF에서 제외")
    parser.add_argument("--keep-exercise-pages", action="store_true", help="연습/기출 문제 페이지도 유지")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    pdf_path = Path(args.pdf)
    transcript_path = Path(args.transcript)
    outdir = Path(args.outdir)

    pages = extract_pages(pdf_path)
    segments = load_transcript(transcript_path)

    matches = match_pages_to_segments(
        pages=pages,
        segments=segments,
        model_name=args.model_name,
        top_k=args.top_k,
        min_score=args.min_score,
    )

    page_map = {p.page_index: p for p in pages}
    skip_exercise_pages = not args.keep_exercise_pages
    for match in matches:
        page = page_map[match.page_index]
        if skip_exercise_pages:
            apply_skip_rules(page, match)
        if match.is_skipped:
            continue
        match.side_notes = build_side_notes(page, match)
        match.figure_notes = build_figure_notes(page, match)
        match.bottom_summary = build_bottom_summary(match)

    pdf_out, json_out = render_study_pdf(
        source_pdf=pdf_path,
        pages=pages,
        matches=matches,
        outdir=outdir,
    )

    print(f"Saved PDF : {pdf_out}")
    print(f"Saved JSON: {json_out}")


if __name__ == "__main__":
    main()
