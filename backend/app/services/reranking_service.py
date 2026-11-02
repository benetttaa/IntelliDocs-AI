from __future__ import annotations

import re
from typing import Any

try:
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover - optional at runtime
    CrossEncoder = None


class RerankingService:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.cross_encoder = None
        self._lazy_model = None

    def _load_model(self):
        if CrossEncoder is None:
            return None
        if self._lazy_model is None:
            self._lazy_model = CrossEncoder(self.model_name)
        return self._lazy_model

    def _lexical_score(self, query: str, candidate: str) -> float:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        candidate_tokens = set(re.findall(r"\w+", candidate.lower()))
        if not query_tokens:
            return 0.0
        overlap = len(query_tokens & candidate_tokens)
        return overlap / len(query_tokens)

    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not candidates:
            return []

        cross_encoder = self._load_model()
        if cross_encoder is not None:
            pairs = [(query, item["text"]) for item in candidates]
            try:
                scores = cross_encoder.predict(pairs)
                reranked = []
                for item, score in zip(candidates, scores):
                    item_copy = dict(item)
                    item_copy["score"] = float(score)
                    reranked.append(item_copy)
                return sorted(reranked, key=lambda x: x["score"], reverse=True)
            except Exception:
                pass

        reranked = []
        for item in candidates:
            lexical_score = self._lexical_score(query, item["text"])
            item_copy = dict(item)
            item_copy["score"] = float(item.get("score", 0.0)) + lexical_score
            reranked.append(item_copy)

        return sorted(reranked, key=lambda x: x["score"], reverse=True)
