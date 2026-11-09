"""Speech-to-text for voice questions in the Assistant tab."""

from __future__ import annotations

from openai import OpenAI, OpenAIError

import config


def voice_enabled() -> bool:
    """True when an OpenAI key is configured."""
    return bool(config.OPENAI_API_KEY)


def get_transcriber() -> OpenAI:
    """Return an OpenAI client for transcription. Fails fast if the key is missing."""
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is empty in .env")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def transcribe(client: OpenAI, audio: bytes, filename: str = "question.wav") -> str:
    """Turn recorded speech into text. Raises RuntimeError with a readable message on failure."""
    try:
        result = client.audio.transcriptions.create(
            model=config.TRANSCRIBE_MODEL, file=(filename, audio)
        )
    except OpenAIError as err:
        raise RuntimeError(f"Couldn't transcribe the recording: {err}") from err
    return result.text.strip()
