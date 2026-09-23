from dataclasses import dataclass

from app.parsers.base import BaseParser, DetectionResult, RawSource


@dataclass(frozen=True, slots=True)
class DetectionFailure(Exception):
    code: str
    message: str
    details: dict[str, object]


class FormatDetector:
    def __init__(
        self,
        parsers: list[BaseParser],
        *,
        minimum_score: float = 0.60,
        ambiguity_delta: float = 0.15,
    ) -> None:
        self._parsers = parsers
        self._minimum_score = minimum_score
        self._ambiguity_delta = ambiguity_delta

    def detect(self, source: RawSource) -> tuple[BaseParser, DetectionResult]:
        ranked = sorted(
            ((parser, parser.detect(source)) for parser in self._parsers),
            key=lambda item: item[1].score,
            reverse=True,
        )

        if not ranked or ranked[0][1].score < self._minimum_score:
            raise DetectionFailure(
                code="FORMAT_UNSUPPORTED",
                message=f"Unable to identify format for {source.filename}.",
                details={
                    "filename": source.filename,
                    "candidates": [
                        {
                            "parser_id": result.parser_id,
                            "score": result.score,
                            "evidence": list(result.evidence),
                        }
                        for _, result in ranked
                    ],
                },
            )

        if len(ranked) > 1:
            first = ranked[0][1]
            second = ranked[1][1]
            if (
                second.score >= self._minimum_score
                and first.score - second.score < self._ambiguity_delta
            ):
                raise DetectionFailure(
                    code="FORMAT_AMBIGUOUS",
                    message=f"Multiple parsers match {source.filename}.",
                    details={
                        "filename": source.filename,
                        "candidates": [
                            {
                                "parser_id": result.parser_id,
                                "score": result.score,
                                "evidence": list(result.evidence),
                            }
                            for _, result in ranked[:2]
                        ],
                    },
                )

        return ranked[0]
