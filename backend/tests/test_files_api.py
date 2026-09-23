from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "synthetic_demo"


def test_parse_files_api_returns_valid_dataset(client):
    pat = (FIXTURE_DIR / "SYNTH001.01.PAT").read_bytes()
    cp = (FIXTURE_DIR / "SYNTH001_20260101090000.CP1").read_bytes()

    response = client.post(
        "/api/v1/files/parse",
        files=[
            ("files", ("SYNTH001.01.PAT", pat, "application/octet-stream")),
            (
                "files",
                (
                    "SYNTH001_20260101090000.CP1",
                    cp,
                    "application/octet-stream",
                ),
            ),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "VALID"
    assert payload["dataset"]["summary"] == {
        "tested_die": 512,
        "pass_die": 358,
        "fail_die": 154,
        "yield": 0.69921875,
    }
    assert len(payload["sources"]) == 2


def test_parse_files_api_rejects_empty_file(client):
    response = client.post(
        "/api/v1/files/parse",
        files=[("files", ("empty.PAT", b"", "application/octet-stream"))],
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UPLOAD_EMPTY_FILE"


def test_parse_files_api_rejects_disallowed_extension(client):
    response = client.post(
        "/api/v1/files/parse",
        files=[("files", ("wafer.exe", b"synthetic", "application/octet-stream"))],
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UPLOAD_EXTENSION_NOT_ALLOWED"
