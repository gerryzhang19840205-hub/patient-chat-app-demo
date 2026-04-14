from dataclasses import dataclass
import json
import logging

from app.models.llm import LLMTextRequest
from app.models.message import Classification
from app.services.constants import (
    CLASSIFICATION_RULES,
    GENERAL_SUB_CLASSIFICATION,
    VALID_SUBCLASSIFICATIONS,
    ClassificationRule,
)
from app.services.llm_client import LLMClientError, LLMService, llm_service


@dataclass(frozen=True)
class ClassificationDecision:
    classification: Classification
    sub_classification: str
    source: str
    confidence: float | None = None
    reason: str | None = None


VALID_CLASSIFICATIONS = {classification.value: classification for classification in Classification}
logger = logging.getLogger(__name__)


def classify_message(
    normalized: str,
    llm_service: LLMService | None = None,
) -> ClassificationDecision:
    matched_rules = get_rule_matches(normalized)
    if len(matched_rules) == 1:
        matched_rule = matched_rules[0]
        return ClassificationDecision(
            classification=matched_rule.classification,
            sub_classification=matched_rule.sub_classification,
            source="rule",
            confidence=1.0,
            reason=(
                f"规则唯一命中 {matched_rule.classification.value}/{matched_rule.sub_classification}，"
                "因此直接采用规则结果。"
            ),
        )

    fallback_service = llm_service or llm_service_singleton()
    llm_decision = classify_by_llm(normalized, fallback_service)
    if llm_decision is not None:
        return ClassificationDecision(
            classification=llm_decision.classification,
            sub_classification=llm_decision.sub_classification,
            source="llm",
            confidence=llm_decision.confidence,
            reason=llm_decision.reason,
        )

    return ClassificationDecision(
        classification=Classification.GENERAL_QUESTION,
        sub_classification=GENERAL_SUB_CLASSIFICATION,
        source="fallback",
        confidence=0.55,
        reason="规则和 LLM 都未明确命中，回退为通用咨询。",
    )


def classify_by_rules(normalized: str) -> Classification:
    matched_classifications = get_rule_matches(normalized)
    if len(matched_classifications) == 1:
        return matched_classifications[0].classification
    return Classification.GENERAL_QUESTION


def get_rule_matches(normalized: str) -> list[ClassificationRule]:
    matched_rules: list[ClassificationRule] = []
    for rule in CLASSIFICATION_RULES:
        if any(phrase in normalized for phrase in rule.phrases):
            matched_rules.append(rule)
    return matched_rules


def llm_service_singleton() -> LLMService:
    return llm_service


def classify_by_llm(normalized: str, llm_service: LLMService) -> ClassificationDecision | None:
    if not llm_service.is_configured():
        return None

    prompt = (
        "You are a medical support triage classifier. "
        "Choose exactly one main classification and one sub classification for the patient's message. "
        "Valid main classifications are: "
        "device_issue, clinical_question, billing_issue, shipping_issue, "
        "account_issue, insurance_issue, general_question. "
        "Valid sub classifications by main classification are: "
        "account_issue=[portal_login_issue,password_reset,password_change,account_locked]; "
        "shipping_issue=[supply_delivery_eta,order_tracking,shipment_not_dispatched]; "
        "billing_issue=[billing_error,bill_payment,charge_question,invoice_request]; "
        "insurance_issue=[insurance_update,insurance_claim,insurance_document_upload,insurance_review_status]; "
        "clinical_question=[stimulation_discomfort,skin_redness,treatment_restart,prescription_status]; "
        "device_issue=[device_wont_power_on,device_charging,device_not_working]; "
        "general_question=[general_inquiry]. "
        "Return strict JSON with keys classification, sub_classification, confidence, and reason. "
        "confidence must be a number between 0 and 1. Do not add extra text."
    )
    request = LLMTextRequest(
        system_prompt=prompt,
        user_input=normalized,
        max_output_tokens=80,
    )

    logger.info("LLM classification input: %s", request.model_dump())

    try:
        response = llm_service.generate_text(request)
    except LLMClientError:
        return None
    except Exception:
        return None

    logger.info("LLM classification output: %s", response.model_dump())
    return parse_llm_classification_response(response.text)


def parse_llm_classification_response(raw_text: str) -> ClassificationDecision | None:
    cleaned = raw_text.strip().strip("`")
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    classification_value = str(payload.get("classification", "")).strip().lower()
    sub_classification = str(payload.get("sub_classification", "")).strip()
    classification = VALID_CLASSIFICATIONS.get(classification_value)
    if classification is None:
        return None
    if sub_classification not in VALID_SUBCLASSIFICATIONS.get(classification, set()):
        return None

    raw_confidence = payload.get("confidence")
    confidence: float | None = None
    if raw_confidence is not None:
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            return None
        if not 0.0 <= confidence <= 1.0:
            return None

    raw_reason = payload.get("reason")
    reason = str(raw_reason).strip() if raw_reason is not None else None
    if reason == "":
        reason = None

    return ClassificationDecision(
        classification=classification,
        sub_classification=sub_classification,
        source="llm",
        confidence=confidence,
        reason=reason,
    )
