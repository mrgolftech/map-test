from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["system"])


@router.get("/version")
def version() -> dict[str, object]:
    return {
        "data": {
            "version": __version__,
        },
        "meta": {},
    }
