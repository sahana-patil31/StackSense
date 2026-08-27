import os
from typing import Optional


EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def detect_language(file_path: str) -> Optional[str]:
    """Detects normalized programming language from file extension.
    
    Returns 'python', 'javascript', 'typescript', or None if unsupported.
    """
    _, ext = os.path.splitext(file_path.lower())
    return EXTENSION_TO_LANGUAGE.get(ext)


def is_supported_file(file_path: str) -> bool:
    """Checks if file extension corresponds to a supported language."""
    return detect_language(file_path) is not None
