from pathlib import Path
from types import SimpleNamespace

from app.models.message import Classification, NextAction
from app.models.message import MessageAnalyzeRequest, MessageAnalyzeResponse
from app.services.conversation_store import init_db, save_inbound_message, save_outbound_message
from app.services.llm_client import LLMService
from app.services.reply_builder import build_reply


class FakeChatCompletionsAPI:
    def __init__(self, response: SimpleNamespace) -> None:
        self._response = response
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class FakeDeepSeekClient:
    def __init__(self, response: SimpleNamespace) -> None:
        self.chat = SimpleNamespace(completions=FakeChatCompletionsAPI(response))


TEST_DB_PATH = "app/data/test_reply_builder_context.db"


def setup_function() -> None:
    db_path = Path(TEST_DB_PATH)
    if db_path.exists():
        db_path.unlink()
    init_db(TEST_DB_PATH)


def test_build_reply_prefers_faq_answer() -> None:
    reply = build_reply(
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="portal_login_issue",
        next_action=NextAction.ROUTE_TO_PORTAL_SUPPORT,
        transcript="我无法登录门户系统。",
    )

    assert "无法登录门户系统" in reply


def test_build_reply_uses_llm_when_faq_answer_missing() -> None:
    fake_response = SimpleNamespace(
        id="resp_reply_1",
        model="deepseek-chat",
        choices=[SimpleNamespace(message=SimpleNamespace(content="这是 LLM 生成的回复。"))],
    )
    fake_client = FakeDeepSeekClient(fake_response)
    llm_service = LLMService(provider="deepseek", api_key="test-key", client=fake_client)

    reply = build_reply(
        classification=Classification.GENERAL_QUESTION,
        sub_classification="non_existing_sub_classification",
        next_action=NextAction.AUTO_REPLY,
        transcript="这个服务周末有人回复吗？",
        llm_service_override=llm_service,
    )

    assert reply == "这是 LLM 生成的回复。"


def test_build_reply_includes_recent_conversation_context() -> None:
    save_inbound_message(
        MessageAnalyzeRequest(sessionId="S300", id="M001", transcript="上一轮用户问题一。"),
        TEST_DB_PATH,
    )
    save_outbound_message(
        MessageAnalyzeResponse(
            sessionId="S300",
            id="M001",
            transcript="上一轮用户问题一。",
            inputMode="text",
            classification=Classification.ACCOUNT_ISSUE,
            sub_classification="portal_login_issue",
            reply="上一轮助手回复一。",
            next_action=NextAction.AUTO_REPLY,
            confidence=1.0,
            reason="测试。",
            recommended_links=[],
        ),
        TEST_DB_PATH,
    )
    save_inbound_message(
        MessageAnalyzeRequest(sessionId="S300", id="M002", transcript="上一轮用户问题二。"),
        TEST_DB_PATH,
    )
    save_outbound_message(
        MessageAnalyzeResponse(
            sessionId="S300",
            id="M002",
            transcript="上一轮用户问题二。",
            inputMode="text",
            classification=Classification.ACCOUNT_ISSUE,
            sub_classification="portal_login_issue",
            reply="上一轮助手回复二。",
            next_action=NextAction.AUTO_REPLY,
            confidence=1.0,
            reason="测试。",
            recommended_links=[],
        ),
        TEST_DB_PATH,
    )

    fake_response = SimpleNamespace(
        id="resp_reply_2",
        model="deepseek-chat",
        choices=[SimpleNamespace(message=SimpleNamespace(content="带上下文的回复。"))],
    )
    fake_client = FakeDeepSeekClient(fake_response)
    llm_service = LLMService(provider="deepseek", api_key="test-key", client=fake_client)

    reply = build_reply(
        classification=Classification.GENERAL_QUESTION,
        sub_classification="non_existing_sub_classification",
        next_action=NextAction.AUTO_REPLY,
        transcript="当前这轮新问题。",
        session_id="S300",
        message_id="M003",
        database_path=TEST_DB_PATH,
        llm_service_override=llm_service,
    )

    assert reply == "带上下文的回复。"
    prompt = fake_client.chat.completions.calls[0]["messages"][-1]["content"]
    assert "最近对话：" in prompt
    assert "上一轮用户问题一。" in prompt
    assert "上一轮助手回复一。" in prompt
    assert "上一轮用户问题二。" in prompt
    assert "上一轮助手回复二。" in prompt
    assert "当前消息：" in prompt
    assert "当前这轮新问题。" in prompt
