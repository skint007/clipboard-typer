import pyperclip


class ClipboardError(Exception):
    """Raised when clipboard cannot be read."""


def read_clipboard() -> str:
    """Read text from system clipboard. Raises ClipboardError on failure."""
    try:
        text = pyperclip.paste()
    except Exception as e:
        raise ClipboardError(f"Cannot access clipboard: {e}") from e
    if not text:
        raise ClipboardError("Clipboard is empty")
    return text
