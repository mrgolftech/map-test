from pathlib import Path

from app.core.config import get_settings
from app.parsers.base import RawSource
from app.schemas.parsing import ParseStatus
from app.services.file_parse_service import FileParseService

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "synthetic_demo"
PAT = (FIXTURE_DIR / "SYNTH001.01.PAT").read_text()
CP = (FIXTURE_DIR / "SYNTH001_20260101090000.CP1").read_text()


def issue_codes(result) -> set[str]:
    return {issue.code for issue in result.validation_issues}


def parse_pat(content: str):
    return FileParseService(get_settings()).parse_sources(
        [RawSource("bad.PAT", content.encode())]
    )


def parse_cp(content: str):
    return FileParseService(get_settings()).parse_sources(
        [RawSource("bad.CP1", content.encode())]
    )


def test_pat_row_length_mismatch_is_invalid():
    lines = PAT.splitlines()
    lines[5] = lines[5][:-1]
    result = parse_pat("\n".join(lines) + "\n")

    assert result.status == ParseStatus.INVALID
    assert "PARSER_ROW_LENGTH_MISMATCH" in issue_codes(result)


def test_pat_unknown_bin_character_is_invalid():
    mutated = PAT.replace("K", "?", 1)
    result = parse_pat(mutated)

    assert result.status == ParseStatus.INVALID
    assert "PARSER_UNKNOWN_BIN_CHAR" in issue_codes(result)


def test_cp_bin_count_mismatch_is_invalid():
    mutated = CP.replace(
        "BIN,     18,     60",
        "BIN,     18,     61",
        1,
    )
    result = parse_cp(mutated)

    assert result.status == ParseStatus.INVALID
    assert "ASSEMBLY_BIN_COUNT_MISMATCH" in issue_codes(result)


def test_cp_tested_mismatch_is_invalid():
    mutated = CP.replace("TESTED DIE     : 512", "TESTED DIE     : 511", 1)
    result = parse_cp(mutated)

    assert result.status == ParseStatus.INVALID
    assert "ASSEMBLY_TESTED_MISMATCH" in issue_codes(result)


def test_cp_missing_map_row_is_invalid():
    lines = [line for line in CP.splitlines() if not line.startswith("010  ")]
    result = parse_cp("\n".join(lines) + "\n")

    assert result.status == ParseStatus.INVALID
    assert "CP_MAP_ROW_MISSING" in issue_codes(result)


def test_pat_cp_metadata_mismatch_is_invalid():
    mutated_pat = PAT.replace("SYNTH001\n", "OTHERLOT\n", 1)
    service = FileParseService(get_settings())
    result = service.parse_sources(
        [
            RawSource("bad.PAT", mutated_pat.encode()),
            RawSource("good.CP1", CP.encode()),
        ]
    )

    assert result.status == ParseStatus.INVALID
    assert "ASSEMBLY_METADATA_MISMATCH" in issue_codes(result)


def test_pat_cp_map_mismatch_is_invalid():
    mutated_pat = PAT.replace("111K", "111G", 1)
    service = FileParseService(get_settings())
    result = service.parse_sources(
        [
            RawSource("bad.PAT", mutated_pat.encode()),
            RawSource("good.CP1", CP.encode()),
        ]
    )

    assert result.status == ParseStatus.INVALID
    assert "ASSEMBLY_MAP_MISMATCH" in issue_codes(result)


def test_invalid_pat_encoding_surfaces_parser_error():
    service = FileParseService(get_settings())
    result = service.parse_sources([RawSource("bad.PAT", b"\xff\xfe\xff")])

    assert result.status == ParseStatus.INVALID
    assert "PARSER_ENCODING_ERROR" in issue_codes(result)
