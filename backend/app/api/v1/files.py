from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.core.config import get_settings
from app.schemas.parsing import ParseResult
from app.services.file_parse_service import FileParseService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/parse", response_model=ParseResult)
async def parse_files(
    files: Annotated[list[UploadFile], File(description="PAT / CP wafer source files")],
) -> ParseResult:
    service = FileParseService(get_settings())
    return await service.parse_uploads(files)
