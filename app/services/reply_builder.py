import logging

from app.models.llm import LLMTextRequest
from app.models.message import Classification, NextAction
from app.services.constants import FAQ_ANSWERS_BY_SUBCLASSIFICATION
from app.services.conversation_store import DEFAULT_DB_PATH, build_recent_conversation_context
from app.services.llm_client import LLMClientError, LLMService, llm_service


logger = logging.getLogger(__name__)


def build_reply(
    classification: Classification,
    sub_classification: str,
    next_action: NextAction,
    transcript: str,
    session_id: str | None = None,
    message_id: str | None = None,
    database_path: str | None = None,
    llm_service_override: LLMService | None = None,
) -> str:
    if next_action == NextAction.ESCALATE_URGENT:
        return (
            "你的消息涉及可能需要尽快人工处理的风险情况。"
            "请先暂停自行调整治疗或设备设置，并尽快联系临床支持或人工客服。"
        )
    faq_answer = FAQ_ANSWERS_BY_SUBCLASSIFICATION.get(sub_classification)
    if faq_answer:
        return faq_answer

    llm_fallback = llm_service_override or llm_service
    llm_answer = build_reply_by_llm(
        classification=classification,
        sub_classification=sub_classification,
        transcript=transcript,
        session_id=session_id,
        message_id=message_id,
        database_path=database_path,
        llm_service_instance=llm_fallback,
    )
    if llm_answer is not None:
        return llm_answer

    return build_default_reply(classification=classification, transcript=transcript)


def build_reply_by_llm(
    classification: Classification,
    sub_classification: str,
    transcript: str,
    session_id: str | None,
    message_id: str | None,
    database_path: str | None,
    llm_service_instance: LLMService,
) -> str | None:
    if not llm_service_instance.is_configured():
        return None

    recent_context = ""
    if session_id:
        recent_context = build_recent_conversation_context(
            session_id=session_id,
            database_path=database_path or DEFAULT_DB_PATH,
            exclude_message_id=message_id,
        )

    user_input_lines = [
        f"classification={classification.value}",
        f"sub_classification={sub_classification}",
    ]
    if recent_context:
        user_input_lines.extend(
            [
                "",
                recent_context,
                "",
                "当前消息：",
                transcript,
            ]
        )
    else:
        user_input_lines.append(f"patient_message={transcript}")

    request = LLMTextRequest(
        system_prompt=(
            "You are a patient support assistant. "
            "Write a short, safe, helpful answer in Simplified Chinese. "
            "Do not provide definitive medical advice. "
            "If the issue is clinical or safety-related, be conservative and recommend professional follow-up."
        ),
        user_input="\n".join(user_input_lines),
        max_output_tokens=120,
    )
    logger.info("LLM reply input: %s", request.model_dump())

    try:
        response = llm_service_instance.generate_text(request)
    except LLMClientError:
        return None
    except Exception:
        return None

    logger.info("LLM reply output: %s", response.model_dump())
    answer = response.text.strip()
    return answer or None


def build_default_reply(classification: Classification, transcript: str) -> str:
    if classification == Classification.DEVICE_ISSUE:
        return "这看起来是设备使用或故障问题。建议先检查电量和连接状态，如仍无法恢复，我们会转给设备支持团队跟进。"
    if classification == Classification.CLINICAL_QUESTION:
        return "这条消息更适合由临床团队确认。为避免给出不准确的医疗建议，我们会建议由专业人员进一步跟进。"
    if classification == Classification.SHIPPING_ISSUE:
        return "这看起来与耗材或物流进度有关。你可以先查看订单状态，如仍异常，我们会转给物流支持。"
    if classification == Classification.ACCOUNT_ISSUE:
        return "这看起来是门户登录或账号访问问题。你可以先尝试重置密码，必要时由门户支持团队协助处理。"
    if classification == Classification.INSURANCE_ISSUE:
        return "这条消息与保险信息更新有关。通常需要人工确认最新资料，我们会建议交给保险支持团队继续处理。"
    if classification == Classification.BILLING_ISSUE:
        return "这看起来与账单或付款有关。我们会建议由账单团队进一步核对具体信息。"
    return f"我们已收到你的消息：{transcript}。当前会先提供基础帮助，如仍未解决，可再转人工支持。"
