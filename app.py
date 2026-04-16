from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lecture_sync_annotator.pdf_parser import extract_pages
from lecture_sync_annotator.transcript_loader import load_transcript
from lecture_sync_annotator.matcher import match_pages_to_segments
from lecture_sync_annotator.notes import build_side_notes, build_bottom_summary
from lecture_sync_annotator.figure_notes import build_figure_notes
from lecture_sync_annotator.renderer import render_study_pdf
from lecture_sync_annotator.filtering import apply_skip_rules

import os
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Lecture Sync Annotator")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

ALLOWED_PDF = {".pdf"}
ALLOWED_TRANSCRIPT = {".json", ".srt", ".txt"}


def _safe_suffix(name: str) -> str:
    return Path(name).suffix.lower().strip()


# -------------------------------
# 메인 페이지
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------------
# 처리
# -------------------------------
@app.post("/process", response_class=HTMLResponse)
async def process(
    request: Request,
    pdf: UploadFile = File(...),
    transcript: UploadFile = File(...)
):
    pdf_suffix = _safe_suffix(pdf.filename or "")
    transcript_suffix = _safe_suffix(transcript.filename or "")

    if pdf_suffix not in ALLOWED_PDF:
        raise HTTPException(status_code=400, detail="PDF만 가능")
    if transcript_suffix not in ALLOWED_TRANSCRIPT:
        raise HTTPException(status_code=400, detail="전사본 형식 오류")

    run_id = uuid.uuid4().hex[:12]
    run_dir = RUNS_DIR / run_id
    uploads_dir = run_dir / "uploads"
    output_dir = run_dir / "output"

    uploads_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = uploads_dir / f"input{pdf_suffix}"
    transcript_path = uploads_dir / f"transcript{transcript_suffix}"

    with pdf_path.open("wb") as f:
        shutil.copyfileobj(pdf.file, f)

    with transcript_path.open("wb") as f:
        shutil.copyfileobj(transcript.file, f)

    # -------------------------------
    # 핵심 처리
    # -------------------------------
    pages = extract_pages(pdf_path)
    segments = load_transcript(transcript_path)
    matches = match_pages_to_segments(pages, segments)

    page_map = {p.page_index: p for p in pages}

    for m in matches:
        m.is_skipped = apply_skip_rules(page_map[m.page_index], m)

    side_notes = [build_side_notes(page_map[m.page_index], m) for m in matches]
    figure_notes = [build_figure_notes(page_map[m.page_index], m) for m in matches]
    bottom_summary = [build_bottom_summary(m) for m in matches]

    pdf_out, json_out = render_study_pdf(
        source_pdf=pdf_path,
        pages=pages,
        matches=matches,
        outdir=output_dir
    )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "run_id": run_id,
            "pdf_name": pdf.filename,
            "transcript_name": transcript.filename,
        },
    )


# -------------------------------
# 다운로드
# -------------------------------
@app.get("/download/{run_id}")
async def download_pdf(run_id: str):
    pdf_path = RUNS_DIR / run_id / "output" / "annotated_notes.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="파일 없음")
    return FileResponse(pdf_path, filename="annotated_notes.pdf")


@app.get("/download-json/{run_id}")
async def download_json(run_id: str):
    json_path = RUNS_DIR / run_id / "output" / "page_matches.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="파일 없음")
    return FileResponse(json_path, filename="page_matches.json")


# -------------------------------
# health check
# -------------------------------
@app.get("/health")
async def health():
    return {"ok": True}


# -------------------------------
# 실행
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
