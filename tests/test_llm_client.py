from types import SimpleNamespace

import pytest

from app.models.llm import LLMTextRequest
from app.services.llm_client import LLMClientError, LLMService


class FakeResponsesAPI:
    def __init__(self, response: SimpleNamespace) -> None:
        self._response = response
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class FakeOpenAIClient:
    def __init__(self, response: SimpleNamespace) -> None:
        self.responses = FakeResponsesAPI(response)


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


def test_llm_service_requires_api_key() -> None:
    service = LLMService(provider="deepseek", api_key="", client=None)

    with pytest.raises(LLMClientError):
        service.generate_text(LLMTextRequest(user_input="test"))


def test_llm_service_generate_text_uses_deepseek_chat_completions() -> None:
    fake_response = SimpleNamespace(
        id="resp_123",
        model="deepseek-chat",
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
    )
    fake_client = FakeDeepSeekClient(fake_response)
    service = LLMService(provider="deepseek", api_key="test-key", client=fake_client)

    result = service.generate_text(
        LLMTextRequest(
            user_input="Say hello",
            system_prompt="You are concise.",
            max_output_tokens=64,
        )
    )

    assert result.text == "hello"
    assert result.model == "deepseek-chat"
    assert result.response_id == "resp_123"
    assert fake_client.chat.completions.calls == [
        {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are concise."},
                {"role": "user", "content": "Say hello"},
            ],
            "max_tokens": 64,
            "temperature": None,
        }
    ]


def test_llm_service_generate_text_uses_openai_responses_api() -> None:
    fake_response = SimpleNamespace(id="resp_123", model="gpt-5", output_text="hello")
    fake_client = FakeOpenAIClient(fake_response)
    service = LLMService(provider="openai", api_key="test-key", client=fake_client)

    result = service.generate_text(
        LLMTextRequest(
            user_input="Say hello",
            system_prompt="You are concise.",
            temperature=0.2,
            max_output_tokens=64,
        )
    )

    assert result.text == "hello"
    assert result.model == "gpt-5"
    assert result.response_id == "resp_123"
    assert fake_client.responses.calls == [
        {
            "model": "gpt-5",
            "instructions": "You are concise.",
            "input": "Say hello",
            "temperature": 0.2,
            "max_output_tokens": 64,
        }
    ]
