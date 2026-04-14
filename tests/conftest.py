from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def patch_speech_synthesis(monkeypatch):
    from app.services import speech_service as speech_module

    def fake_synthesize_text_to_mp3(text, output_path):
        output_path.write_bytes(b"fake-mp3-data")
        return output_path

    monkeypatch.setattr(speech_module.speech_service, "synthesize_text_to_mp3", fake_synthesize_text_to_mp3)


@pytest.fixture(autouse=True)
def patch_speech_transcription(monkeypatch):
    from app.services import speech_service as speech_module

    async def fake_transcribe_upload_file(upload_file):
        return "我无法登录门户系统。"

    monkeypatch.setattr(speech_module.speech_service, "transcribe_upload_file", fake_transcribe_upload_file)
