from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedEntity:
    name: str
    entity_type: str  # FILE, MODULE, CLASS, FUNCTION, METHOD
    start_line: int
    end_line: int
    parent_scope: Optional[str] = None  # e.g., 'class:PaymentService' or 'function:outer'
    qualified_name: Optional[str] = None


@dataclass
class ParsedImport:
    module: str  # e.g., 'auth' or './auth'
    imported_items: List[str] = field(default_factory=list)  # e.g., ['validate_token']
    is_relative: bool = False
    start_line: int = 1


@dataclass
class ParsedCall:
    callee: str  # e.g., 'validate_token' or 'database.save' or 'service.charge'
    caller_scope: Optional[str] = None  # e.g., 'function:process_payment'
    start_line: int = 1


@dataclass
class ParseResult:
    file_path: str
    language: str
    status: str  # 'success' or 'error'
    errors: List[str] = field(default_factory=list)
    entities: List[ParsedEntity] = field(default_factory=list)
    imports: List[ParsedImport] = field(default_factory=list)
    calls: List[ParsedCall] = field(default_factory=list)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str, source_code: bytes) -> ParseResult:
        """Parses file source code and returns ParseResult with entities, imports, and calls."""
        pass
