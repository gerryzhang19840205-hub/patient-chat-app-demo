# Fasikl Patient Message Assistant

FastAPI implementation for the Fasikl interview assignment (Option C).

## What Is Implemented

- `POST /api/messages/analyze` for message analysis
- Text input and `mp3` audio input support on the analyze endpoint
- Main classification + sub classification
- `next_action` decision output
- FAQ-first reply generation by `sub_classification`
- LLM fallback for classification and reply (DeepSeek default, OpenAI optional)
- Conversation persistence for all inbound/outbound payloads
- `GET /api/messages/sessions/{session_id}` for session history query
- `GET /api/messages/audio/{filename}` for generated reply audio download

## Tech Stack

- Python 3.11
- FastAPI + Pydantic
- SQLite (local file)
- Pytest
- OpenAI-compatible SDK for DeepSeek/OpenAI provider switching
- `faster-whisper` for speech-to-text
- `gTTS` for text-to-speech

## Project Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Config is loaded from `.env` via [`app/config.py`](/Users/zhanghao/PycharmProjects/fasikl-option-c/app/config.py).

### DeepSeek (default)

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### OpenAI (optional)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5
OPENAI_BASE_URL=
```

### Database

```env
DATABASE_PATH=app/data/app.db
```

All inbound/outbound conversation events are persisted to SQLite.

### Speech

```env
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
TTS_LANGUAGE=zh-CN
AUDIO_OUTPUT_DIR=app/data/audio
```

Audio input is transcribed with `faster-whisper`, and the reply is synthesized back to an `mp3` file.

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health`
- `POST /api/messages/analyze`
- `GET /api/messages/sessions/{session_id}`
- `GET /api/messages/audio/{filename}`
- Swagger: `http://127.0.0.1:8000/docs`

## API Examples

### Analyze Message

JSON text input:

```bash
curl -X POST http://127.0.0.1:8000/api/messages/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "S001",
    "id": "C001",
    "transcript": "我的设备昨天开始无法开机，我每天早上都要使用。"
  }'
```

Multipart audio input:

```bash
curl -X POST http://127.0.0.1:8000/api/messages/analyze \
  -F "sessionId=S002" \
  -F "id=C002" \
  -F "audioFile=@sample.mp3"
```

Example response (shape):

```json
{
  "sessionId": "S001",
  "id": "C001",
  "transcript": "我的设备昨天开始无法开机，我每天早上都要使用。",
  "inputMode": "text",
  "classification": "device_issue",
  "sub_classification": "device_wont_power_on",
  "reply": "...",
  "next_action": "auto_reply",
  "confidence": 1.0,
  "reason": "...",
  "recommended_links": [],
  "replyAudioFilename": "S001_C001.mp3",
  "replyAudioUrl": "/api/messages/audio/S001_C001.mp3"
}
```

### Query Session History

```bash
curl http://127.0.0.1:8000/api/messages/sessions/S001
```

## Test

```bash
source .venv/bin/activate
pytest
```

Current automated coverage includes:

- classification (rule + LLM fallback)
- action policy
- FAQ/LLM reply fallback
- conversation persistence
- session query API
