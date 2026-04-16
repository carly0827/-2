from __future__ import annotations

import re
from collections import Counter
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .models import PageData, PageMatch, TranscriptSegment
from .utils import clean_text, split_sentences


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-]{2,}|[가-힣]{2,}")


def _tokenize(text: str) -> List[str]:
    return [x.lower() for x in TOKEN_RE.findall(clean_text(text))]


def _lexical_overlap(page_text: str, seg_text: str) -> float:
    p = Counter(_tokenize(page_text))
    s = Counter(_tokenize(seg_text))
    if not p or not s:
        return 0.0
    inter = sum((p & s).values())
    denom = max(1, min(sum(p.values()), sum(s.values())))
    return inter / denom


def _keyword_candidates(page_text: str, transcript_text: str, limit: int = 12) -> List[str]:
    page_tokens = set(_tokenize(page_text))
    seen = set()
    out: List[str] = []
    for token in _tokenize(transcript_text):
        if token in seen:
            continue
        seen.add(token)
        if token in page_tokens:
            out.append(token)
        if len(out) >= limit:
            break
    return out


def match_pages_to_segments(
    pages: List[PageData],
    segments: List[TranscriptSegment],
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    top_k: int = 6,
    min_score: float = 0.14,
) -> List[PageMatch]:
    model = SentenceTransformer(model_name)
    page_texts = [p.text or f"page {p.page_index + 1}" for p in pages]
    seg_texts = [s.text for s in segments]

    page_emb = model.encode(page_texts, normalize_embeddings=True, show_progress_bar=False)
    seg_emb = model.encode(seg_texts, normalize_embeddings=True, show_progress_bar=False)

    sem_sim = cosine_similarity(page_emb, seg_emb)

    matches: List[PageMatch] = []
    prev_best = 0

    for i, page in enumerate(pages):
        combined_scores = []
        for j, seg in enumerate(segments):
            lexical = _lexical_overlap(page.text, seg.text)
            continuity = max(0.0, 1.0 - abs(j - prev_best) / 10.0) * 0.08
            score = 0.72 * float(sem_sim[i][j]) + 0.20 * lexical + continuity
            combined_scores.append(score)

        ranked = np.argsort(combined_scores)[::-1][:top_k]
        chosen = [segments[idx] for idx in ranked if combined_scores[idx] >= min_score]
        chosen = sorted(chosen, key=lambda x: x.start)

        best_idx = int(ranked[0]) if len(ranked) else prev_best
        prev_best = best_idx
        raw_text = " ".join(s.text for s in chosen)
        highlight_terms = _keyword_candidates(page.text, raw_text)

        matches.append(
            PageMatch(
                page_index=page.page_index,
                score=float(combined_scores[best_idx]) if len(ranked) else 0.0,
                page_text=page.text,
                matched_segments=chosen,
                highlight_terms=highlight_terms,
                debug={
                    "best_segment_index": best_idx,
                    "top_indices": [int(x) for x in ranked],
                    "top_scores": [float(combined_scores[int(x)]) for x in ranked],
                },
            )
        )
    return matches
