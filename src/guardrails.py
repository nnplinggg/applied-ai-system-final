"""Input validation and confidence scoring."""
from dataclasses import dataclass

MAX_QUERY_CHARS = 300
MIN_ALPHA_RATIO = 0.5
LOW_CONFIDENCE = 0.55
MIN_SIMILARITY = 0.08  # below this, retrieval found nothing relevant


@dataclass
class Validation:
    ok: bool
    cleaned: str = ""
    reason: str = ""


def validate_query(query) -> Validation:
    if not isinstance(query, str):
        return Validation(False, reason="Input must be text.")
    cleaned = query.strip()
    if not cleaned:
        return Validation(False, reason="Input is empty. Describe the music you want.")
    if len(cleaned) > MAX_QUERY_CHARS:
        return Validation(False, reason=f"Input is too long (max {MAX_QUERY_CHARS} characters).")
    letters = sum(c.isalpha() for c in cleaned)
    if letters / len(cleaned) < MIN_ALPHA_RATIO:
        return Validation(False, reason="Input does not look like a text description.")
    return Validation(True, cleaned)


def compute_confidence(top_ratio: float, margin: float, similarity: float) -> float:
    """Blend match quality (0.5), separation from runner-up (0.2) and retrieval relevance (0.3)."""
    c = 0.5 * top_ratio + 0.2 * min(1.0, margin / 0.15) + 0.3 * min(1.0, similarity / 0.4)
    return round(max(0.0, min(1.0, c)), 2)
