"""
Async CUIT enrichment wrapper.

Wraps the synchronous RNSDatasetLookup into an async call that yields
SSE-ready event dicts. RNS takes ~12s on first load (CSV parsing),
~100ms after cache warm.
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add tools/scripts to sys.path so we can import the lookup modules
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[3] / "tools" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


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


async def enrich_cuit(cuit: str) -> dict[str, Any]:
    """Run RNS enrichment.

    Returns:
        rns_result — dict ready to be SSE event payload.
    """
    return await _lookup_rns(cuit)
