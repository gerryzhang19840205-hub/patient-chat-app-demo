import json
from pathlib import Path

from app.services.conversation_store import fetch_session_events, init_db
from app.models.message import MessageAnalyzeRequest, MessageAnalyzeResponse, Classification, NextAction
from app.services.conversation_store import save_inbound_message, save_outbound_message


TEST_DB_PATH = "app/data/test_conversation_store.db"


def setup_function() -> None:
    db_path = Path(TEST_DB_PATH)
    if db_path.exists():
        db_path.unlink()
    init_db(TEST_DB_PATH)


def test_conversation_store_persists_inbound_and_outbound_events() -> None:
    inbound = MessageAnalyzeRequest(sessionId="S100", id="M100", transcript="我无法登录门户系统。")
    outbound = MessageAnalyzeResponse(
        sessionId="S100",
        id="M100",
        transcript="我无法登录门户系统。",
        inputMode="text",
        classification=Classification.ACCOUNT_ISSUE,
        sub_classification="portal_login_issue",
        reply="请先尝试重置密码。",
        next_action=NextAction.AUTO_REPLY,
        confidence=1.0,
        reason="根据关键词规则识别。",
        recommended_links=[],
    )

    save_inbound_message(inbound, TEST_DB_PATH)
    save_outbound_message(outbound, TEST_DB_PATH)

    events = fetch_session_events("S100", TEST_DB_PATH)

    assert len(events) == 2
    assert events[0]["direction"] == "inbound"
    assert events[1]["direction"] == "outbound"
    assert json.loads(events[0]["payload_json"])["sessionId"] == "S100"
    assert json.loads(events[1]["payload_json"])["classification"] == "account_issue"
