from pydantic import ConfigDict
from enum import Enum

from pydantic import BaseModel, Field


class Classification(str, Enum):
    DEVICE_ISSUE = "device_issue"
    CLINICAL_QUESTION = "clinical_question"
    BILLING_ISSUE = "billing_issue"
    SHIPPING_ISSUE = "shipping_issue"
    ACCOUNT_ISSUE = "account_issue"
    INSURANCE_ISSUE = "insurance_issue"
    GENERAL_QUESTION = "general_question"


class NextAction(str, Enum):
    AUTO_REPLY = "auto_reply"
    ROUTE_TO_DEVICE_SUPPORT = "route_to_device_support"
    ROUTE_TO_CLINICAL_TEAM = "route_to_clinical_team"
    ROUTE_TO_BILLING_TEAM = "route_to_billing_team"
    ROUTE_TO_SHIPPING_TEAM = "route_to_shipping_team"
    ROUTE_TO_PORTAL_SUPPORT = "route_to_portal_support"
    ROUTE_TO_INSURANCE_TEAM = "route_to_insurance_team"
    ESCALATE_URGENT = "escalate_urgent"


class RecommendedLink(BaseModel):
    label: str
    url: str


class MessageAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId", serialization_alias="sessionId", description="Conversation session identifier")
    id: str = Field(..., description="Message or transcript identifier")
    transcript: str = Field(..., min_length=1, description="Patient message transcript")
    input_mode: str = Field(default="text", alias="inputMode", serialization_alias="inputMode")
    source_audio_filename: str | None = Field(default=None, alias="sourceAudioFilename", serialization_alias="sourceAudioFilename")


class MessageAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId", serialization_alias="sessionId")
    id: str
    transcript: str
    input_mode: str = Field(default="text", alias="inputMode", serialization_alias="inputMode")
    source_audio_filename: str | None = Field(default=None, alias="sourceAudioFilename", serialization_alias="sourceAudioFilename")
    classification: Classification
    sub_classification: str
    reply: str
    next_action: NextAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    recommended_links: list[RecommendedLink] = Field(default_factory=list)
    reply_audio_filename: str | None = Field(default=None, alias="replyAudioFilename", serialization_alias="replyAudioFilename")
    reply_audio_url: str | None = Field(default=None, alias="replyAudioUrl", serialization_alias="replyAudioUrl")


class ConversationEvent(BaseModel):
    session_id: str = Field(..., alias="sessionId", serialization_alias="sessionId")
    message_id: str = Field(..., alias="messageId", serialization_alias="messageId")
    direction: str
    payload: dict
    created_at: str = Field(..., alias="createdAt", serialization_alias="createdAt")


class SessionMessagesResponse(BaseModel):
    session_id: str = Field(..., alias="sessionId", serialization_alias="sessionId")
    events: list[ConversationEvent]
