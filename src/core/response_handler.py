import re

CODE_BLOCK_PATTERN = re.compile(r"```(?:\w+)?\n?.*?```", re.DOTALL)
CODE_SPEECH_PLACEHOLDER = "See the code on screen."


def strip_code_for_speech(text: str) -> str:
    speech_text = CODE_BLOCK_PATTERN.sub(CODE_SPEECH_PLACEHOLDER, text)
    speech_text = re.sub(r"\n{3,}", "\n\n", speech_text)
    return speech_text.strip()


def prepare_response(user_input: str, text: str) -> tuple[str, str]:
    """Split an assistant response into (speech_text, display_text).

    display_text is the original response, unchanged, so the user can still
    read any code. speech_text has fenced code blocks replaced with a short
    placeholder so Jarvis doesn't read code aloud.
    """
    # Special case: user just said the wake word with no real command, and
    # the model came back with little to say. Skip the code stripping since
    # it's a fixed short reply.
    if user_input.strip().lower() in {"jarvis", "jarvis.", "jarvis?"} and (not text or len(text) < 5):
        return "Sir.", "Sir."
    return strip_code_for_speech(text), text
