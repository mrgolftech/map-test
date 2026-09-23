from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256

from app.schemas.parsing import (
    SourceDescriptor,
    SourceFormat,
    SourceParseResult,
    SourceRole,
)


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


def build_descriptor(source: RawSource, detection: DetectionResult) -> SourceDescriptor:
    return SourceDescriptor(
        filename=source.filename,
        size=source.size,
        sha256=source.sha256,
        detected_format=detection.detected_format,
        parser_id=detection.parser_id,
        role=detection.role,
        detection_evidence=list(detection.evidence),
    )
