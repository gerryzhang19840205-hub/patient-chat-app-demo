from types import SimpleNamespace

from app.models.message import Classification
from app.services.classifier import classify_message
from app.services.llm_client import LLMService


class FakeResponsesAPI:
    def __init__(self, response: SimpleNamespace) -> None:
        self._response = response

    def create(self, **kwargs):
        return self._response


class FakeOpenAIClient:
    def __init__(self, response: SimpleNamespace) -> None:
        self.responses = FakeResponsesAPI(response)


class FakeChatCompletionsAPI:
    def __init__(self, response: SimpleNamespace) -> None:
        self._response = response

    def create(self, **kwargs):
        return self._response


class FakeDeepSeekClient:
    def __init__(self, response: SimpleNamespace) -> None:
        self.chat = SimpleNamespace(completions=FakeChatCompletionsAPI(response))


def test_classify_message_uses_rules_first() -> None:
    decision = classify_message("我无法登录门户系统。")

    assert decision.classification == Classification.ACCOUNT_ISSUE
    assert decision.sub_classification == "portal_login_issue"
    assert decision.source == "rule"


def test_classify_message_uses_llm_fallback_when_rules_miss() -> None:
    fake_response = SimpleNamespace(
        id="resp_456",
        model="deepseek-chat",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"classification":"shipping_issue","sub_classification":"order_tracking","confidence":0.82,"reason":"用户明确询问包裹状态。"}'
                )
            )
        ],
    )
    fake_client = FakeDeepSeekClient(fake_response)
    llm_service = LLMService(provider="deepseek", api_key="test-key", client=fake_client)

    decision = classify_message("我的包裹怎么一直没有更新状态", llm_service=llm_service)

    assert decision.classification == Classification.SHIPPING_ISSUE
    assert decision.sub_classification == "order_tracking"
    assert decision.source == "llm"
    assert decision.confidence == 0.82
    assert decision.reason == "用户明确询问包裹状态。"


def test_classify_message_returns_general_when_llm_is_unavailable() -> None:
    llm_service = LLMService(api_key=None, client=None)

    decision = classify_message("这句话没有明显关键词", llm_service=llm_service)

    assert decision.classification == Classification.GENERAL_QUESTION
    assert decision.sub_classification == "general_inquiry"
    assert decision.source == "fallback"


def test_classify_message_uses_llm_when_multiple_rule_categories_match() -> None:
    fake_response = SimpleNamespace(
        id="resp_789",
        model="deepseek-chat",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"classification":"account_issue","sub_classification":"portal_login_issue","confidence":0.91,"reason":"消息同时提到登录与账单，登录问题更突出。"}'
                )
            )
        ],
    )
    fake_client = FakeDeepSeekClient(fake_response)
    llm_service = LLMService(provider="deepseek", api_key="test-key", client=fake_client)

    decision = classify_message("我无法登录门户系统，而且账单也有问题。", llm_service=llm_service)

    assert decision.classification == Classification.ACCOUNT_ISSUE
    assert decision.sub_classification == "portal_login_issue"
    assert decision.source == "llm"
    assert decision.confidence == 0.91
    assert decision.reason == "消息同时提到登录与账单，登录问题更突出。"
