from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer, util
from src.ontology import RULE_KEYWORDS, RESEARCH_DOMAINS, METHODS, POPULATIONS, SPONSOR_THEMES

_model: Optional[SentenceTransformer] = None
SIMILARITY_THRESHOLD = 0.30


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def tag(foa: dict) -> dict:
    text = _build_tagging_text(foa)
    rule_tags = _apply_rules(text)
    embedding_tags = _apply_embeddings(text, rule_tags)

    merged = {}
    for category in ("research_domains", "methods", "populations", "sponsor_themes"):
        combined = list(dict.fromkeys(rule_tags.get(category, []) + embedding_tags.get(category, [])))
        merged[category] = combined

    return merged


def _build_tagging_text(foa: dict) -> str:
    parts = [
        foa.get("title") or "",
        foa.get("description") or "",
        foa.get("eligibility") or "",
    ]
    return " ".join(filter(None, parts)).lower()


def _apply_rules(text: str) -> dict:
    result = {category: [] for category in RULE_KEYWORDS}
    for category, label_map in RULE_KEYWORDS.items():
        for label, keywords in label_map.items():
            if any(kw in text for kw in keywords):
                result[category].append(label)
    return result


def _apply_embeddings(text: str, rule_tags: dict) -> dict:
    model = _get_model()
    text_embedding = model.encode(text, convert_to_tensor=True)

    ontology_map = {
        "research_domains": RESEARCH_DOMAINS,
        "methods": METHODS,
        "populations": POPULATIONS,
        "sponsor_themes": SPONSOR_THEMES,
    }

    result = {}
    for category, candidates in ontology_map.items():
        already_tagged = set(rule_tags.get(category, []))
        new_candidates = [c for c in candidates if c not in already_tagged]

        if not new_candidates:
            result[category] = []
            continue

        label_embeddings = model.encode(new_candidates, convert_to_tensor=True)
        scores = util.cos_sim(text_embedding, label_embeddings)[0].cpu().numpy()

        assigned = [
            new_candidates[i]
            for i, score in enumerate(scores)
            if score >= SIMILARITY_THRESHOLD
        ]
        result[category] = assigned

    return result
