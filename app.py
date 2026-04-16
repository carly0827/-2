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
from
