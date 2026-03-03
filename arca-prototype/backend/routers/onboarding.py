"""
Onboarding import SSE endpoint.

POST /api/onboarding/import — accepts CUIT + Clave Fiscal, returns an SSE
stream with progressive import events (enrichment, comprobantes, retenciones,
notifications).
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services.import_orchestrator import run_import

router = APIRouter()


class ImportRequest(BaseModel):
    cuit: str
    password: str
    fecha_desde: str = ""
    fecha_hasta: str = ""


@router.post("/import")
async def start_import(req: ImportRequest):
    """Start an ARCA onboarding import. Returns an SSE event stream."""
    return StreamingResponse(
        run_import(req.cuit, req.password, req.fecha_desde, req.fecha_hasta),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
