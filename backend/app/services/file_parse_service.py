from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import AppError
from app.parsers.assembler import WaferAssembler
from app.parsers.base import RawSource
from app.parsers.cp_parser import CpParser
from app.parsers.detector import DetectionFailure, FormatDetector
from app.parsers.pat_parser import PatParser
from app.schemas.parsing import ParseResult


class FileParseService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._detector = FormatDetector([PatParser(), CpParser()])
        self._assembler = WaferAssembler()

    async def parse_uploads(self, files: list[UploadFile]) -> ParseResult:
        if not files:
            raise AppError(
                code="UPLOAD_FILE_REQUIRED",
                message="At least one wafer source file is required.",
                status_code=422,
            )
        if len(files) > self._settings.upload_max_files:
            raise AppError(
                code="UPLOAD_TOO_MANY_FILES",
                message="Too many wafer source files were uploaded.",
                status_code=413,
                details={
                    "maximum": self._settings.upload_max_files,
                    "actual": len(files),
                },
            )

        raw_sources: list[RawSource] = []
        total_size = 0

        for upload in files:
            filename = upload.filename or ""
            if not filename or Path(filename).name != filename:
                raise AppError(
                    code="UPLOAD_FILENAME_INVALID",
                    message="Upload filename must not contain a path.",
                    status_code=422,
                    details={"filename": filename},
                )

            suffix = Path(filename).suffix.lower()
            if suffix not in self._settings.allowed_upload_extensions:
                raise AppError(
                    code="UPLOAD_EXTENSION_NOT_ALLOWED",
                    message=f"File extension {suffix or '<none>'} is not allowed.",
                    status_code=415,
                    details={
                        "filename": filename,
                        "allowed_extensions": sorted(
                            self._settings.allowed_upload_extensions
                        ),
                    },
                )

            content = await upload.read(self._settings.upload_max_file_bytes + 1)
            if len(content) > self._settings.upload_max_file_bytes:
                raise AppError(
                    code="UPLOAD_FILE_TOO_LARGE",
                    message="Uploaded wafer source exceeds the per-file size limit.",
                    status_code=413,
                    details={
                        "filename": filename,
                        "maximum_bytes": self._settings.upload_max_file_bytes,
                    },
                )

            total_size += len(content)
            if total_size > self._settings.upload_max_total_bytes:
                raise AppError(
                    code="UPLOAD_TOTAL_TOO_LARGE",
                    message="Uploaded wafer sources exceed the total size limit.",
                    status_code=413,
                    details={"maximum_bytes": self._settings.upload_max_total_bytes},
                )

            lines = content.splitlines()
            if len(lines) > self._settings.upload_max_lines:
                raise AppError(
                    code="UPLOAD_TOO_MANY_LINES",
                    message="Uploaded wafer source contains too many lines.",
                    status_code=413,
                    details={
                        "filename": filename,
                        "maximum": self._settings.upload_max_lines,
                        "actual": len(lines),
                    },
                )
            longest = max((len(line) for line in lines), default=0)
            if longest > self._settings.upload_max_line_bytes:
                raise AppError(
                    code="UPLOAD_LINE_TOO_LONG",
                    message="Uploaded wafer source contains an excessively long line.",
                    status_code=413,
                    details={
                        "filename": filename,
                        "maximum_bytes": self._settings.upload_max_line_bytes,
                        "actual_bytes": longest,
                    },
                )

            raw_sources.append(RawSource(filename=filename, content=content))

        return self.parse_sources(raw_sources)

    def parse_sources(self, sources: list[RawSource]) -> ParseResult:
        parsed = []
        for source in sources:
            try:
                parser, detection = self._detector.detect(source)
            except DetectionFailure as exc:
                raise AppError(
                    code=exc.code,
                    message=exc.message,
                    status_code=422,
                    details=exc.details,
                ) from exc
            parsed.append(parser.parse(source, detection))

        return self._assembler.assemble(parsed)
