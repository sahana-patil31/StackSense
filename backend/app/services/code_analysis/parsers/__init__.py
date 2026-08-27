from typing import Dict
from app.services.code_analysis.parsers.base import BaseParser
from app.services.code_analysis.parsers.javascript_parser import JavaScriptParser
from app.services.code_analysis.parsers.python_parser import PythonParser
from app.services.code_analysis.parsers.typescript_parser import TypeScriptParser


_PARSERS: Dict[str, BaseParser] = {}


def get_parser_for_file(file_path: str, language: str) -> BaseParser:
    """Returns the appropriate parser instance for a language/file."""
    ext = file_path.lower().split(".")[-1]
    if language == "python":
        if "python" not in _PARSERS:
            _PARSERS["python"] = PythonParser()
        return _PARSERS["python"]
    elif language == "javascript":
        if "javascript" not in _PARSERS:
            _PARSERS["javascript"] = JavaScriptParser()
        return _PARSERS["javascript"]
    elif language == "typescript":
        key = f"typescript_{ext}"
        if key not in _PARSERS:
            is_tsx = ext == "tsx"
            _PARSERS[key] = TypeScriptParser(is_tsx=is_tsx)
        return _PARSERS[key]
    else:
        raise ValueError(f"Unsupported language for parsing: {language}")
