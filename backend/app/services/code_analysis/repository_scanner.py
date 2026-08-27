import os
from dataclasses import dataclass
from typing import List, Set

from app.services.code_analysis.language_detector import detect_language


DEFAULT_IGNORED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    ".env",
    "build",
    "dist",
    "coverage",
    ".pytest_cache",
    ".idea",
    ".vscode",
    ".next",
    "out",
    "vendor",
}

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB threshold to avoid memory issues with bundle files


@dataclass
class DiscoveredFile:
    relative_path: str
    absolute_path: str
    language: str
    size: int


class RepositoryScanner:
    def __init__(self, ignored_dirs: Set[str] = None, max_file_size: int = MAX_FILE_SIZE_BYTES):
        self.ignored_dirs = ignored_dirs if ignored_dirs is not None else DEFAULT_IGNORED_DIRS
        self.max_file_size = max_file_size

    def scan(self, repo_dir: str) -> List[DiscoveredFile]:
        """Recursively scans repository directory and yields supported source files."""
        discovered: List[DiscoveredFile] = []
        if not os.path.exists(repo_dir) or not os.path.isdir(repo_dir):
            return discovered

        norm_repo_dir = os.path.abspath(repo_dir)

        for root, dirs, files in os.walk(norm_repo_dir, topdown=True):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith(".")]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, norm_repo_dir).replace("\\", "/")

                language = detect_language(rel_path)
                if not language:
                    continue

                try:
                    stat = os.stat(abs_path)
                    size = stat.st_size
                except OSError:
                    continue

                if size > self.max_file_size:
                    continue

                # Skip binary check
                if self._is_binary_file(abs_path):
                    continue

                discovered.append(
                    DiscoveredFile(
                        relative_path=rel_path,
                        absolute_path=abs_path,
                        language=language,
                        size=size,
                    )
                )

        return discovered

    def _is_binary_file(self, file_path: str) -> bool:
        """Simple heuristic to detect binary files."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except Exception:
            return True
