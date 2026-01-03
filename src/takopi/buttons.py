"""Button configuration for Telegram inline keyboards."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Button:
    """A single inline button."""
    text: str
    data: str

    def to_inline_button(self) -> dict[str, str]:
        """Convert to Telegram InlineKeyboardButton format."""
        return {"text": self.text, "callback_data": self.data}


@dataclass(frozen=True)
class VoiceButtonsConfig:
    """Configuration for voice message buttons."""
    enabled: bool = False
    options: tuple[Button, ...] = ()
    store_file: str = "inbox.md"  # File to append transcripts when Store is pressed


@dataclass(frozen=True)
class ButtonsConfig:
    """Configuration for all button types."""
    startup: tuple[Button, ...] = ()
    voice: VoiceButtonsConfig = field(default_factory=VoiceButtonsConfig)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ButtonsConfig:
        """Parse button config from TOML dict."""
        if not isinstance(data, dict):
            return ButtonsConfig()

        # Parse startup buttons
        startup_data = data.get("startup", [])
        startup_buttons: list[Button] = []
        if isinstance(startup_data, list):
            for btn in startup_data:
                if isinstance(btn, dict) and "text" in btn and "data" in btn:
                    startup_buttons.append(Button(
                        text=str(btn["text"]),
                        data=str(btn["data"]),
                    ))

        # Parse voice buttons
        voice_data = data.get("voice", {})
        voice_config = VoiceButtonsConfig()
        if isinstance(voice_data, dict):
            enabled = voice_data.get("enabled", False)
            store_file = voice_data.get("store_file", "inbox.md")
            options_data = voice_data.get("options", [])
            voice_options: list[Button] = []
            if isinstance(options_data, list):
                for btn in options_data:
                    if isinstance(btn, dict) and "text" in btn and "data" in btn:
                        voice_options.append(Button(
                            text=str(btn["text"]),
                            data=str(btn["data"]),
                        ))
            voice_config = VoiceButtonsConfig(
                enabled=bool(enabled),
                options=tuple(voice_options),
                store_file=str(store_file),
            )

        return ButtonsConfig(
            startup=tuple(startup_buttons),
            voice=voice_config,
        )


def build_inline_keyboard(buttons: tuple[Button, ...], columns: int = 3) -> dict[str, Any]:
    """Build a Telegram InlineKeyboardMarkup from buttons.

    Args:
        buttons: Tuple of Button objects
        columns: Number of buttons per row (default 2)

    Returns:
        Dict suitable for reply_markup parameter
    """
    if not buttons:
        return {}

    keyboard: list[list[dict[str, str]]] = []
    row: list[dict[str, str]] = []

    for btn in buttons:
        row.append(btn.to_inline_button())
        if len(row) >= columns:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return {"inline_keyboard": keyboard}


def parse_response_buttons(text: str) -> tuple[str, tuple[Button, ...]]:
    """Parse [buttons] block from Claude's response.

    Format:
    ```
    [buttons]
    - ✅ Done | !done
    - ⏰ Snooze | !snooze:1h
    ```

    Args:
        text: Claude's response text

    Returns:
        Tuple of (cleaned_text, buttons)
        cleaned_text has the [buttons] block removed
    """
    # Pattern to match [buttons] block (case-insensitive, handles whitespace)
    pattern = r'\n*\[buttons?\]\s*\n((?:[-•]\s*.+\n?)+)'

    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return text, ()

    buttons_block = match.group(1)
    buttons: list[Button] = []

    # Parse each button line: "- Text | action" or "• Text | action"
    line_pattern = r'[-•]\s*(.+?)\s*\|\s*(\S+)'
    for line_match in re.finditer(line_pattern, buttons_block):
        btn_text = line_match.group(1).strip()
        btn_data = line_match.group(2).strip()
        # Telegram callback_data limit is 64 bytes
        if len(btn_data.encode('utf-8')) <= 64:
            buttons.append(Button(text=btn_text, data=btn_data))

    # Remove the [buttons] block from text
    cleaned_text = text[:match.start()] + text[match.end():]
    cleaned_text = cleaned_text.strip()

    return cleaned_text, tuple(buttons)
