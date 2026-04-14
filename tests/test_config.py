from app.config import Settings


def test_settings_read_explicit_values() -> None:
    settings = Settings(
        LLM_PROVIDER="deepseek",
        DEEPSEEK_API_KEY="test-key",
        DEEPSEEK_MODEL="deepseek-chat",
        DEEPSEEK_BASE_URL="https://api.deepseek.com",
        OPENAI_API_KEY="openai-test-key",
        OPENAI_MODEL="gpt-5-mini",
        LLM_TIMEOUT_SECONDS=12.5,
    )

    assert settings.llm_provider == "deepseek"
    assert settings.deepseek_api_key == "test-key"
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.openai_api_key == "openai-test-key"
    assert settings.openai_model == "gpt-5-mini"
    assert settings.llm_timeout_seconds == 12.5
