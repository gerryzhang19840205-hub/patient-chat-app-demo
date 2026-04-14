import logging

from openai import APIError, OpenAI

from app.config import get_settings
from app.models.llm import LLMTextRequest, LLMTextResponse


DEFAULT_MODEL = "gpt-5"
DEFAULT_PROVIDER = "deepseek"
logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """Raised when LLM client usage or configuration fails."""


class LLMService:
    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        client: OpenAI | None = None,
    ) -> None:
        settings = get_settings()

        self.provider = (provider or settings.llm_provider or DEFAULT_PROVIDER).lower()
        self.api_key = api_key if api_key is not None else self._get_default_api_key(settings)
        self.model = model if model is not None else self._get_default_model(settings)
        self.base_url = base_url if base_url is not None else self._get_default_base_url(settings)
        self.timeout = timeout if timeout is not None else settings.llm_timeout_seconds
        self._client = client

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_text(self, request: LLMTextRequest) -> LLMTextResponse:
        if not self.is_configured():
            raise LLMClientError("LLM API key is not configured.")

        client = self._get_client()
        try:
            if self.provider == "deepseek":
                response = client.chat.completions.create(
                    model=request.model or self.model,
                    messages=self._build_messages(request),
                    max_tokens=request.max_output_tokens,
                    temperature=request.temperature,
                )
            else:
                response = client.responses.create(
                    model=request.model or self.model,
                    instructions=request.system_prompt,
                    input=request.user_input,
                    temperature=request.temperature,
                    max_output_tokens=request.max_output_tokens,
                )
        except APIError as error:
            logger.exception(
                "LLM API error: provider=%s status=%s type=%s code=%s message=%s body=%s",
                self.provider,
                getattr(error, "status_code", None),
                error.__class__.__name__,
                getattr(error, "code", None),
                getattr(error, "message", str(error)),
                getattr(error, "body", None),
            )
            raise
        except Exception:
            logger.exception("Unexpected LLM client error for provider=%s", self.provider)
            raise

        if self.provider == "deepseek":
            text = response.choices[0].message.content or ""
            model_name = response.model
            response_id = getattr(response, "id", None)
        else:
            text = response.output_text
            model_name = response.model
            response_id = getattr(response, "id", None)

        return LLMTextResponse(
            text=text,
            model=model_name,
            response_id=response_id,
        )

    def _get_client(self) -> OpenAI:
        if self._client is None:
            client_kwargs = {"api_key": self.api_key, "timeout": self.timeout}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            self._client = OpenAI(**client_kwargs)
        return self._client

    def _build_messages(self, request: LLMTextRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_input})
        return messages

    def _get_default_api_key(self, settings) -> str | None:
        if self.provider == "deepseek":
            return settings.deepseek_api_key
        return settings.openai_api_key

    def _get_default_model(self, settings) -> str:
        if self.provider == "deepseek":
            return settings.deepseek_model
        return settings.openai_model or DEFAULT_MODEL

    def _get_default_base_url(self, settings) -> str | None:
        if self.provider == "deepseek":
            return settings.deepseek_base_url
        return settings.openai_base_url


llm_service = LLMService()
