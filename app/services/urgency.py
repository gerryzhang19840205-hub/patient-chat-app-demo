from app.services.constants import URGENT_KEYWORDS


def detect_urgent(normalized: str) -> bool:
    return any(keyword in normalized for keyword in URGENT_KEYWORDS)
