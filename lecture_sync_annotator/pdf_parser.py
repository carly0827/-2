from __future__ import annotations

from pathlib import Path
from typing import List
import fitz

from .models import PageData, TextBlock, ImageBlock
from .utils import clean_text


def extract_pages(pdf_path: str | Path) -> List[PageData]:
    doc = fitz.open(pdf_path)
    pages: List[PageData] = []

    for i, page in enumerate(doc):
        text_blocks: List[TextBlock] = []
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") == 0:
                lines = []
                for line in block.get("lines", []):
                    spans = [span.get("text", "") for span in line.get("spans", [])]
                    joined = "".join(spans).strip()
                    if joined:
                        lines.append(joined)
                if lines:
                    bbox = fitz.Rect(block["bbox"])
                    text_blocks.append(TextBlock(bbox=bbox, text=clean_text("\n".join(lines))))

        full_text = clean_text(page.get_text("text"))

        image_blocks: List[ImageBlock] = []
        for block in page_dict.get("blocks", []):
            if block.get("type") == 1:
                bbox = fitz.Rect(block["bbox"])
                image_blocks.append(
                    ImageBlock(
                        xref=int(block.get("number", 0)),
                        bbox=bbox,
                        width=int(bbox.width),
                        height=int(bbox.height),
                        ext="png",
                    )
                )

        pages.append(
            PageData(
                page_index=i,
                text=full_text,
                rect=page.rect,
                text_blocks=text_blocks,
                images=image_blocks,
            )
        )

    doc.close()
    return pages
