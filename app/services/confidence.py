from app.models.message import Classification
from app.services.constants import CLASSIFICATION_RULES


def estimate_confidence(
    classification: Classification,
    is_urgent: bool,
    source: str,
    llm_confidence: float | None = None,
) -> float:
    if source == "rule":
        return 1.0
    if source == "llm" and llm_confidence is not None:
        return llm_confidence
    if classification == Classification.GENERAL_QUESTION:
        return 0.55
    if is_urgent:
        return 0.95
    return 0.78
