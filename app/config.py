from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    app_name: str = Field(default="Fasikl Patient Message Assistant")
    app_version: str = Field(default="0.1.0")
    database_path: str = Field(default="app/data/app.db", alias="DATABASE_PATH")
    audio_output_dir: str = Field(default="app/data/audio", alias="AUDIO_OUTPUT_DIR")
    whisper_model_size: str = Field(default="base", alias="WHISPER_MODEL_SIZE")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    whisper_compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    tts_language: str = Field(default="zh-CN", alias="TTS_LANGUAGE")
    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-5", alias="OPENAI_MODEL")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
