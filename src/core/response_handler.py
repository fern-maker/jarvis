import re

CODE_BLOCK_PATTERN = re.compile(r"```(?:\w+)?\n?.*?```", re.DOTALL)
CODE_SPEECH_PLACEHOLDER = "See the code on screen."


def strip_code_for_speech(text: str) -> str:
    speech_text = CODE_BLOCK_PATTERN.sub(CODE_SPEECH_PLACEHOLDER, text)
    speech_text = re.sub(r"\n{3,}", "\n\n", speech_text)
    return speech_text.strip()


def prepare_response(text: str) -> tuple[str, str]:
    """Split an assistant response into (speech_text, display_text).

    display_text is the original response, unchanged, so the user can still
    read any code. speech_text has fenced code blocks replaced with a short
    placeholder so Jarvis doesn't read code aloud.
    """
    return strip_code_for_speech(text), text
