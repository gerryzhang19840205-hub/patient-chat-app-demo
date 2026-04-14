from pydantic import BaseModel, Field


class LLMTextRequest(BaseModel):
    user_input: str = Field(..., min_length=1, description="Primary user input for the model")
    system_prompt: str | None = Field(default=None, description="Optional high-level instructions")
    model: str | None = Field(default=None, description="Optional per-request model override")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, gt=0)


class LLMTextResponse(BaseModel):
    text: str
    model: str
    response_id: str | None = None
