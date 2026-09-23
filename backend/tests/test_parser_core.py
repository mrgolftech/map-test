import json
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.parsers.base import DetectionResult, RawSource
from app.parsers.cp_parser import CpParser
from app.parsers.detector import DetectionFailure, FormatDetector
from app.parsers.pat_parser import PatParser
from app.schemas.parsing import ParseStatus, SourceFormat, SourceRole
from app.services.file_parse_service import FileParseService

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "synthetic_demo"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


def test_golden_pat_cp_assemble_matches_expected_facts():
    expected = json.loads((FIXTURE_DIR / "expected.json").read_text())
    service = FileParseService(get_settings())

    result = service.parse_sources(
        [
            RawSource("SYNTH001.01.PAT", fixture_bytes("SYNTH001.01.PAT")),
            RawSource(
                "SYNTH001_20260101090000.CP1",
                fixture_bytes("SYNTH001_20260101090000.CP1"),
            ),
        ]
    )

    assert result.status == ParseStatus.VALID
    assert result.validation_issues == []
    assert result.dataset is not None

    dataset = result.dataset
    for key, value in expected["metadata"].items():
        assert getattr(dataset.metadata, key) == value

    assert dataset.summary.tested_die == expected["summary"]["tested_die"]
    assert dataset.summary.pass_die == expected["summary"]["pass_die"]
    assert dataset.summary.fail_die == expected["summary"]["fail_die"]
    assert dataset.summary.yield_ == pytest.approx(expected["summary"]["yield"])

    actual_bins = {str(item.bin): item.count for item in dataset.bins}
    assert actual_bins == expected["bins"]
    assert len(dataset.dies) == expected["summary"]["tested_die"]


def test_detector_recognizes_pat_by_content_when_extension_is_txt():
    detector = FormatDetector([PatParser(), CpParser()])
    parser, result = detector.detect(
        RawSource("renamed.txt", fixture_bytes("SYNTH001.01.PAT"))
    )

    assert isinstance(parser, PatParser)
    assert result.detected_format == SourceFormat.PAT
    assert "fixed-width single-character map" in result.evidence


def test_detector_recognizes_cp_by_content_when_extension_is_txt():
    detector = FormatDetector([PatParser(), CpParser()])
    parser, result = detector.detect(
        RawSource(
            "renamed.txt",
            fixture_bytes("SYNTH001_20260101090000.CP1"),
        )
    )

    assert isinstance(parser, CpParser)
    assert result.detected_format == SourceFormat.CP1
    assert "BOF/SOFT BIN/SOFT BIN MAP/EOF sections" in result.evidence


class StubParser:
    def __init__(self, parser_id: str, score: float) -> None:
        self.parser_id = parser_id
        self.score = score

    def detect(self, source: RawSource) -> DetectionResult:
        return DetectionResult(
            parser_id=self.parser_id,
            detected_format=SourceFormat.UNKNOWN,
            role=SourceRole.UNKNOWN,
            score=self.score,
            evidence=(self.parser_id,),
        )


def test_detector_rejects_ambiguous_content():
    detector = FormatDetector(
        [StubParser("one", 0.80), StubParser("two", 0.72)],
        ambiguity_delta=0.15,
    )

    with pytest.raises(DetectionFailure) as exc_info:
        detector.detect(RawSource("ambiguous.txt", b"synthetic"))

    assert exc_info.value.code == "FORMAT_AMBIGUOUS"


def test_golden_pat_only_is_valid_and_preserves_counts():
    service = FileParseService(get_settings())
    result = service.parse_sources(
        [RawSource("SYNTH001.01.PAT", fixture_bytes("SYNTH001.01.PAT"))]
    )

    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    assert result.dataset.metadata.rows == 24
    assert result.dataset.metadata.columns == 32
    assert result.dataset.summary.tested_die == 512
    assert result.dataset.summary.pass_die == 358
    assert result.dataset.summary.fail_die == 154


def test_golden_cp_only_is_valid_and_preserves_counts():
    service = FileParseService(get_settings())
    result = service.parse_sources(
        [
            RawSource(
                "SYNTH001_20260101090000.CP1",
                fixture_bytes("SYNTH001_20260101090000.CP1"),
            )
        ]
    )

    assert result.status == ParseStatus.VALID
    assert result.dataset is not None
    assert result.dataset.metadata.product_id == "DEMO_PRODUCT"
    assert result.dataset.summary.tested_die == 512
    assert result.dataset.summary.pass_die == 358
    assert result.dataset.summary.fail_die == 154


@pytest.mark.parametrize("filename", ["not-a-map.PAT", "not-a-map.CP1"])
def test_detector_does_not_trust_extension_without_content(filename: str):
    detector = FormatDetector([PatParser(), CpParser()])

    with pytest.raises(DetectionFailure) as exc_info:
        detector.detect(RawSource(filename, b"plain text that is not a wafer map\n"))

    assert exc_info.value.code == "FORMAT_UNSUPPORTED"
