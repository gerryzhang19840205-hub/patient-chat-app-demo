import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.conversation_store import fetch_session_events, init_db


client = TestClient(app)


def setup_function() -> None:
    settings = get_settings()
    db_path = Path(settings.database_path)
    if db_path.exists():
        db_path.unlink()
    init_db(settings.database_path)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_device_issue() -> None:
    response = client.post(
        "/api/messages/analyze",
        json={"sessionId": "S001", "id": "C001", "transcript": "我的设备昨天开始无法开机，我每天早上都要使用。"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S001"
    assert body["classification"] == "device_issue"
    assert body["sub_classification"] == "device_wont_power_on"
    assert body["next_action"] == "auto_reply"
    assert body["confidence"] == 1.0
    assert body["recommended_links"]
    events = fetch_session_events("S001")
    assert len(events) == 2
    assert events[0]["direction"] == "inbound"
    assert events[1]["direction"] == "outbound"
    assert json.loads(events[0]["payload_json"])["sessionId"] == "S001"
    assert json.loads(events[1]["payload_json"])["sessionId"] == "S001"


def test_analyze_account_issue() -> None:
    response = client.post(
        "/api/messages/analyze",
        json={"sessionId": "S002", "id": "C004", "transcript": "我无法登录门户系统。"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S002"
    assert body["classification"] == "account_issue"
    assert body["sub_classification"] == "portal_login_issue"
    assert body["next_action"] == "auto_reply"
    assert body["confidence"] == 1.0


def test_analyze_audio_upload() -> None:
    response = client.post(
        "/api/messages/analyze",
        data={"sessionId": "S006", "id": "C200"},
        files={"audioFile": ("sample.mp3", BytesIO(b"fake-audio-bytes"), "audio/mpeg")},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S006"
    assert body["inputMode"] == "audio"
    assert body["sourceAudioFilename"] == "sample.mp3"
    assert body["transcript"] == "我无法登录门户系统。"
    assert body["replyAudioFilename"] == "S006_C200.mp3"
    assert body["replyAudioUrl"] == "/api/messages/audio/S006_C200.mp3"
    audio_response = client.get(body["replyAudioUrl"])
    assert audio_response.status_code == 200
    assert audio_response.headers["content-type"] == "audio/mpeg"
    assert audio_response.content == b"fake-mp3-data"


def test_analyze_urgent_clinical_message() -> None:
    response = client.post(
        "/api/messages/analyze",
        json={"sessionId": "S003", "id": "C007", "transcript": "使用设备后皮肤发红。"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S003"
    assert body["classification"] == "clinical_question"
    assert body["sub_classification"] == "skin_redness"
    assert body["next_action"] == "route_to_clinical_team"
    assert body["confidence"] == 1.0


def test_analyze_general_fallback() -> None:
    response = client.post(
        "/api/messages/analyze",
        json={"sessionId": "S004", "id": "C999", "transcript": "请问这个服务周末有人回复吗？"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S004"
    assert body["classification"] == "general_question"
    assert body["sub_classification"] == "general_inquiry"
    assert body["next_action"] == "auto_reply"


def test_get_session_messages() -> None:
    client.post(
        "/api/messages/analyze",
        json={"sessionId": "S005", "id": "C100", "transcript": "我无法登录门户系统。"},
    )

    response = client.get("/api/messages/sessions/S005")
    body = response.json()

    assert response.status_code == 200
    assert body["sessionId"] == "S005"
    assert len(body["events"]) == 2
    assert body["events"][0]["direction"] == "inbound"
    assert body["events"][1]["direction"] == "outbound"
    assert body["events"][0]["payload"]["sessionId"] == "S005"
    assert body["events"][1]["payload"]["classification"] == "account_issue"
