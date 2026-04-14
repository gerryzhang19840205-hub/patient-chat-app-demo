import json
import sqlite3
from pathlib import Path

from app.models.message import (
    ConversationEvent,
    MessageAnalyzeRequest,
    MessageAnalyzeResponse,
    SessionMessagesResponse,
)


DEFAULT_DB_PATH = "app/data/app.db"


def init_db(database_path: str = DEFAULT_DB_PATH) -> None:
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                direction TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_inbound_message(
    payload: MessageAnalyzeRequest,
    database_path: str = DEFAULT_DB_PATH,
) -> None:
    _insert_event(
        session_id=payload.session_id,
        message_id=payload.id,
        direction="inbound",
        payload_json=json.dumps(payload.model_dump(by_alias=True), ensure_ascii=False),
        database_path=database_path,
    )


def save_outbound_message(
    payload: MessageAnalyzeResponse,
    database_path: str = DEFAULT_DB_PATH,
) -> None:
    _insert_event(
        session_id=payload.session_id,
        message_id=payload.id,
        direction="outbound",
        payload_json=json.dumps(payload.model_dump(by_alias=True), ensure_ascii=False),
        database_path=database_path,
    )


def fetch_session_events(
    session_id: str,
    database_path: str = DEFAULT_DB_PATH,
) -> list[dict[str, str]]:
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            SELECT session_id, message_id, direction, payload_json, created_at
            FROM conversation_events
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "session_id": row[0],
            "message_id": row[1],
            "direction": row[2],
            "payload_json": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def build_session_messages_response(
    session_id: str,
    database_path: str = DEFAULT_DB_PATH,
) -> SessionMessagesResponse:
    raw_events = fetch_session_events(session_id, database_path)
    events = [
        ConversationEvent(
            sessionId=event["session_id"],
            messageId=event["message_id"],
            direction=event["direction"],
            payload=json.loads(event["payload_json"]),
            createdAt=event["created_at"],
        )
        for event in raw_events
    ]
    return SessionMessagesResponse(sessionId=session_id, events=events)


def build_recent_conversation_context(
    session_id: str,
    database_path: str = DEFAULT_DB_PATH,
    max_rounds: int = 5,
    exclude_message_id: str | None = None,
) -> str:
    rounds = fetch_recent_session_rounds(
        session_id=session_id,
        database_path=database_path,
        exclude_message_id=exclude_message_id,
    )
    selected_rounds = rounds[-max_rounds:]
    if not selected_rounds:
        return ""

    lines: list[str] = ["最近对话："]
    for index, round_item in enumerate(selected_rounds, start=1):
        lines.append(f"轮次 {index}:")
        user_payload = round_item.get("user")
        assistant_payload = round_item.get("assistant")
        if isinstance(user_payload, dict):
            user_text = str(user_payload.get("transcript", "")).strip()
            if user_text:
                lines.append(f"用户: {user_text}")
        if isinstance(assistant_payload, dict):
            assistant_text = str(assistant_payload.get("reply", "")).strip()
            if assistant_text:
                lines.append(f"助手: {assistant_text}")

    return "\n".join(lines)


def fetch_recent_session_rounds(
    session_id: str,
    database_path: str = DEFAULT_DB_PATH,
    exclude_message_id: str | None = None,
) -> list[dict[str, object]]:
    raw_events = fetch_session_events(session_id, database_path)
    rounds: list[dict[str, object]] = []

    for event in raw_events:
        if exclude_message_id is not None and event["message_id"] == exclude_message_id:
            continue

        payload = json.loads(event["payload_json"])
        if event["direction"] == "inbound":
            rounds.append(
                {
                    "message_id": event["message_id"],
                    "user": payload,
                    "assistant": None,
                    "created_at": event["created_at"],
                }
            )
            continue

        if rounds and rounds[-1]["message_id"] == event["message_id"]:
            rounds[-1]["assistant"] = payload
        else:
            rounds.append(
                {
                    "message_id": event["message_id"],
                    "user": None,
                    "assistant": payload,
                    "created_at": event["created_at"],
                }
            )

    return rounds


def _insert_event(
    session_id: str,
    message_id: str,
    direction: str,
    payload_json: str,
    database_path: str,
) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO conversation_events (session_id, message_id, direction, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, message_id, direction, payload_json),
        )
        connection.commit()
