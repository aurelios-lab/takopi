"""Voice transcription using local Whisper."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    """Configuration for Whisper transcription."""
    enabled: bool = True
    model: str = "base"
    language: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WhisperConfig":
        return cls(
            enabled=data.get("enabled", True),
            model=data.get("model", "base"),
            language=data.get("language"),
        )


class TranscriptionError(Exception):
    pass


async def transcribe_audio(
    audio_data: bytes,
    model: str = "base",
    language: str | None = None,
) -> str:
    """
    Transcribe audio using local Whisper CLI.

    Args:
        audio_data: Raw audio bytes (OGG/OGA format from Telegram)
        model: Whisper model size (tiny, base, small, medium, large)
        language: Optional language code (e.g., "en", "fr")

    Returns:
        Transcribed text
    """
    import anyio

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        input_file = tmppath / "voice.ogg"
        output_file = tmppath / "voice.txt"

        # Write audio to temp file
        input_file.write_bytes(audio_data)

        # Build whisper command
        cmd = [
            "whisper",
            str(input_file),
            "--model", model,
            "--output_dir", str(tmppath),
            "--output_format", "txt",
        ]
        if language:
            cmd.extend(["--language", language])

        logger.debug("[transcribe] running: %s", " ".join(cmd))

        # Run whisper in a thread to not block
        def run_whisper() -> subprocess.CompletedProcess:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

        try:
            result = await anyio.to_thread.run_sync(run_whisper)
        except subprocess.TimeoutExpired:
            raise TranscriptionError("Whisper transcription timed out")

        if result.returncode != 0:
            logger.error("[transcribe] whisper failed: %s", result.stderr)
            raise TranscriptionError(f"Whisper failed: {result.stderr}")

        # Read output
        if not output_file.exists():
            # Whisper might name it differently
            txt_files = list(tmppath.glob("*.txt"))
            if txt_files:
                output_file = txt_files[0]
            else:
                raise TranscriptionError("No transcription output found")

        text = output_file.read_text().strip()
        logger.info("[transcribe] result: %s", text[:100] if text else "(empty)")
        return text


def is_whisper_available() -> bool:
    """Check if whisper CLI is available."""
    try:
        result = subprocess.run(
            ["whisper", "--help"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
