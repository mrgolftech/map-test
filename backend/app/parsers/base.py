from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256

from app.schemas.parsing import SourceFormat, SourceParseResult, SourceRole


@dataclass(frozen=True, slots=True)
class RawSource:
    filename: str
    content: bytes

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def sha256(self) -> str:
        return sha256(self.content).hexdigest()


@dataclass(frozen=True, slots=True)
class DetectionResult:
    parser_id: str
    detected_format: SourceFormat
    role: SourceRole
    score: float
    evidence: tuple[str, ...]


class BaseParser(ABC):
    parser_id: str
    detected_format: SourceFormat
    role: SourceRole

    @abstractmethod
    def detect(self, source: RawSource) -> DetectionResult:
        raise NotImplementedError

    @abstractmethod
    def parse(self, source: RawSource, detection: DetectionResult) -> SourceParseResult:
        raise NotImplementedError


def decode_text(source: RawSource) -> str:
    return source.content.decode("utf-8-sig")
