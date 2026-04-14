from app.models.message import (
    MessageAnalyzeRequest,
    MessageAnalyzeResponse,
)
from app.services.action_policy import decide_next_action
from app.services.classifier import classify_message
from app.services.confidence import estimate_confidence
from app.services.constants import LINKS_BY_CLASSIFICATION
from app.services.conversation_store import save_inbound_message, save_outbound_message
from app.services.reason_builder import build_reason
from app.services.reply_builder import build_reply
from app.services.speech_service import speech_service
from app.services.urgency import detect_urgent


def analyze_message(payload: MessageAnalyzeRequest) -> MessageAnalyzeResponse:
    save_inbound_message(payload)

    transcript = payload.transcript.strip()
    normalized = transcript.lower()

    classification_decision = classify_message(normalized)
    classification = classification_decision.classification
    sub_classification = classification_decision.sub_classification
    is_urgent = detect_urgent(normalized)
    confidence = estimate_confidence(
        classification=classification,
        is_urgent=is_urgent,
        source=classification_decision.source,
        llm_confidence=classification_decision.confidence,
    )
    next_action = decide_next_action(
        classification=classification,
        is_urgent=is_urgent,
        confidence=confidence,
    )
    reply = build_reply(
        classification=classification,
        sub_classification=sub_classification,
        next_action=next_action,
        transcript=transcript,
        session_id=payload.session_id,
        message_id=payload.id,
    )
    reason = (
        classification_decision.reason
        if classification_decision.source == "llm" and classification_decision.reason
        else build_reason(
            classification=classification,
            sub_classification=sub_classification,
            next_action=next_action,
            is_urgent=is_urgent,
            source=classification_decision.source,
        )
    )

    response = MessageAnalyzeResponse(
        session_id=payload.session_id,
        id=payload.id,
        transcript=transcript,
        input_mode=payload.input_mode,
        source_audio_filename=payload.source_audio_filename,
        classification=classification,
        sub_classification=sub_classification,
        reply=reply,
        next_action=next_action,
        confidence=confidence,
        reason=reason,
        recommended_links=LINKS_BY_CLASSIFICATION.get(classification, []),
        reply_audio_filename=None,
        reply_audio_url=None,
    )
    reply_audio_path = speech_service.build_reply_audio_path(payload.session_id, payload.id)
    speech_service.synthesize_text_to_mp3(reply, reply_audio_path)
    response.reply_audio_filename = reply_audio_path.name
    response.reply_audio_url = f"/api/messages/audio/{reply_audio_path.name}"
    save_outbound_message(response)
    return response
