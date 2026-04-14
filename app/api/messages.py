from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.datastructures import FormData

from app.config import get_settings
from app.models.message import MessageAnalyzeRequest, MessageAnalyzeResponse, SessionMessagesResponse
from app.services.conversation_store import build_session_messages_response
from app.services.message_analyzer import analyze_message
from app.services.speech_service import speech_service


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/analyze", response_model=MessageAnalyzeResponse)
async def analyze_patient_message(request: Request) -> MessageAnalyzeResponse:
    payload = await _parse_analyze_request(request)
    return analyze_message(payload)


@router.get("/sessions/{session_id}", response_model=SessionMessagesResponse)
def get_session_messages(session_id: str) -> SessionMessagesResponse:
    return build_session_messages_response(session_id)


@router.get("/audio/{filename}")
def download_reply_audio(filename: str):
    settings = get_settings()
    safe_name = Path(filename).name
    audio_path = Path(settings.audio_output_dir) / safe_name
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=safe_name)


async def _parse_analyze_request(request: Request) -> MessageAnalyzeRequest:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        return await _build_request_from_form(form)

    body = await request.json()
    return MessageAnalyzeRequest(**body)


async def _build_request_from_form(form: FormData) -> MessageAnalyzeRequest:
    session_id = form.get("sessionId")
    message_id = form.get("id")
    transcript = form.get("transcript")
    audio_file = form.get("audioFile")

    if audio_file is not None and hasattr(audio_file, "read") and hasattr(audio_file, "filename"):
        transcript_text = await speech_service.transcribe_upload_file(audio_file)
        return MessageAnalyzeRequest(
            session_id=session_id,
            id=message_id,
            transcript=transcript_text,
            input_mode="audio",
            source_audio_filename=audio_file.filename,
        )

    if transcript is None:
        raise HTTPException(status_code=422, detail="Either transcript or audioFile is required.")

    return MessageAnalyzeRequest(
        session_id=session_id,
        id=message_id,
        transcript=transcript,
        input_mode="text",
    )
