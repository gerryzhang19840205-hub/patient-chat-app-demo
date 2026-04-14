import logging
from functools import lru_cache
from pathlib import Path

from fastapi import UploadFile
from faster_whisper import WhisperModel
from gtts import gTTS

from app.config import get_settings


logger = logging.getLogger(__name__)


class SpeechServiceError(RuntimeError):
    """Raised when speech transcription or synthesis fails."""


class SpeechService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_size = settings.whisper_model_size
        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type
        self.tts_language = settings.tts_language
        self.audio_output_dir = Path(settings.audio_output_dir)
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)

    def transcribe_audio_file(self, audio_path: Path) -> str:
        try:
            model = self._get_model()
            segments, _info = model.transcribe(str(audio_path))
        except Exception as exc:
            raise SpeechServiceError("Failed to transcribe audio file.") from exc

        transcript = "".join(segment.text for segment in segments).strip()
        if not transcript:
            raise SpeechServiceError("No speech detected in audio file.")
        return transcript

    async def transcribe_upload_file(self, upload_file: UploadFile) -> str:
        suffix = Path(upload_file.filename or "audio.mp3").suffix or ".mp3"
        temp_path = self.audio_output_dir / f"_tmp_{Path(upload_file.filename or 'audio').stem}{suffix}"
        try:
            content = await upload_file.read()
            temp_path.write_bytes(content)
            return self.transcribe_audio_file(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def synthesize_text_to_mp3(self, text: str, output_path: Path) -> Path:
        try:
            tts = gTTS(text=text, lang=self.tts_language)
            tts.save(str(output_path))
        except Exception as exc:
            logger.exception(
                "Failed to synthesize speech: lang=%s output_path=%s text_length=%s",
                self.tts_language,
                output_path,
                len(text),
            )
            raise SpeechServiceError("Failed to synthesize speech.") from exc
        return output_path

    def build_reply_audio_path(self, session_id: str, message_id: str) -> Path:
        return self.audio_output_dir / f"{session_id}_{message_id}.mp3"

    @lru_cache
    def _get_model(self) -> WhisperModel:
        return WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )


speech_service = SpeechService()
