"""
Async CUIT enrichment wrapper.

Wraps the synchronous AFIPCUITLookupService and RNSDatasetLookup into async
generators that yield SSE-ready event dicts as each data source completes.

Both lookups run in parallel via asyncio.gather. AFIP typically completes
in ~1-2s; RNS takes ~12s on first load (CSV parsing), ~100ms after cache warm.
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add tools/scripts to sys.path so we can import the lookup modules
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[3] / "tools" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


async def _lookup_afip(cuit: str) -> dict[str, Any]:
    """Run AFIP CUIT lookup in a thread. Returns enrichment_afip event payload."""
    try:
        from afip_cuit_lookup import AFIPCUITLookupService

        service = AFIPCUITLookupService()
        info = await asyncio.to_thread(service.lookup_cuit, cuit)

        if info and not info.error:
            return {
                "razon_social": info.razon_social,
                "condicion_impositiva": info.condicion_impositiva,
                "estado": info.estado,
                "direccion": info.direccion,
                "localidad": info.localidad,
                "provincia": info.provincia,
                "actividades": [
                    {"descripcion": a.descripcion, "id": a.id, "periodo": a.periodo}
                    for a in info.actividades
                ],
            }
        return {"error": True, "message": info.errores[0] if info and info.errores else "CUIT no encontrado"}
    except Exception as e:
        return {"error": True, "message": str(e)}


async def _lookup_rns(cuit: str) -> dict[str, Any]:
    """Run RNS dataset lookup in a thread. Returns enrichment_rns event payload."""
    try:
        from rns_dataset_lookup import RNSDatasetLookup

        rns = RNSDatasetLookup()
        result = await asyncio.to_thread(rns.lookup_cuit, cuit)

        if result and result.found:
            return {
                "found": True,
                "razon_social": result.razon_social,
                "creation_date": result.creation_date,
                "tipo_societario": result.tipo_societario,
                "provincia": result.provincia,
                "actividad_descripcion": result.actividad_descripcion,
            }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


async def enrich_cuit(cuit: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run AFIP and RNS enrichment in parallel.

    Returns:
        (afip_result, rns_result) — both are dicts ready to be SSE event payloads.
    """
    afip_result, rns_result = await asyncio.gather(
        _lookup_afip(cuit),
        _lookup_rns(cuit),
    )
    return afip_result, rns_result
