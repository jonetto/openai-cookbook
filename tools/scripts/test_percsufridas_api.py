#!/usr/bin/env python3
"""
Test: Can the Colppy API accept `percsufridas` array in alta_facturacompra?

Steps:
1. Login to get claveSesion
2. List existing purchase invoices to find one with percepcionIIBB > 0
3. Read that invoice with leer_facturacompra
4. List percsufridas for that invoice (Proveedor.listar_percsufridas)
5. List available IIBB jurisdictions (Proveedor.listar_jurisdiccionesPerc)

This is a READ-ONLY test — no invoices are created or modified.
"""

import asyncio
import hashlib
import json
import os
import sys

# Load env from arca-prototype
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / "arca-prototype" / ".env"
load_dotenv(env_path)

import httpx

COLPPY_API_URL = "https://login.colppy.com/lib/frontera2/service.php"
TIMEOUT = 30.0


def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def auth_block() -> dict:
    return {
        "usuario": os.getenv("COLPPY_AUTH_USER"),
        "password": md5(os.getenv("COLPPY_AUTH_PASSWORD")),
    }


async def call_api(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(COLPPY_API_URL, json=payload)
        resp.raise_for_status()
        text = resp.text.strip()
        if not text:
            return {"result": {"estado": -1, "mensaje": "Empty response"}, "response": {"success": False}}
        try:
            data = resp.json()
        except Exception:
            print(f"[WARN] Non-JSON response: {text[:200]}")
            return {"result": {"estado": -1, "mensaje": "Non-JSON response"}, "response": {"success": False}}
        if data is None:
            return {"result": {"estado": -1, "mensaje": "Null JSON"}, "response": {"success": False}}
        return data


async def login() -> str:
    payload = {
        "auth": auth_block(),
        "service": {"provision": "Usuario", "operacion": "iniciar_sesion"},
        "parameters": {
            "usuario": os.getenv("COLPPY_USER"),
            "password": md5(os.getenv("COLPPY_PASSWORD")),
        },
    }
    data = await call_api(payload)
    if (data.get("response") or {}).get("success"):
        clave = data["response"]["data"]["claveSesion"]
        print(f"[OK] Login successful, claveSesion: {clave[:8]}...")
        return clave
    else:
        print(f"[FAIL] Login failed: {data}")
        sys.exit(1)


async def list_facturas_compra(clave: str, id_empresa: str, limit: int = 20) -> list:
    """List recent purchase invoices."""
    payload = {
        "auth": auth_block(),
        "service": {"provision": "FacturaCompra", "operacion": "listar_facturasCompra"},
        "parameters": {
            "sesion": {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave},
            "idEmpresa": id_empresa,
            "start": 0,
            "limit": limit,
            "filter": [],
            "order": {"field": ["idFactura"], "order": "desc"},
        },
    }
    data = await call_api(payload)
    if (data.get("response") or {}).get("success"):
        items = data["response"]["data"]
        if isinstance(items, list):
            print(f"[OK] Listed {len(items)} purchase invoices")
            return items
    print(f"[FAIL] List failed: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    return []


async def leer_factura_compra(clave: str, id_empresa: str, id_factura: str) -> dict:
    """Read a single purchase invoice."""
    payload = {
        "auth": auth_block(),
        "service": {"provision": "FacturaCompra", "operacion": "leer_facturacompra"},
        "parameters": {
            "sesion": {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave},
            "idEmpresa": id_empresa,
            "idFactura": id_factura,
        },
    }
    data = await call_api(payload)
    resp = data.get("response") or {}
    if resp.get("success"):
        return resp.get("data", {})
    print(f"[FAIL] Read failed: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    return {}


async def listar_percsufridas(clave: str, id_empresa: str, id_factura: str) -> list:
    """List percepciones sufridas for a specific invoice."""
    payload = {
        "auth": auth_block(),
        "service": {"provision": "Proveedor", "operacion": "listar_percsufridas"},
        "parameters": {
            "sesion": {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave},
            "idEmpresa": id_empresa,
            "idFactura": id_factura,
        },
    }
    data = await call_api(payload)
    resp = data.get("response") or {}
    if resp.get("success"):
        return resp.get("data", [])
    print(f"[INFO] listar_percsufridas response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    return []


async def listar_jurisdicciones(clave: str, id_empresa: str) -> list:
    """List available IIBB jurisdictions for the company."""
    payload = {
        "auth": auth_block(),
        "service": {"provision": "Proveedor", "operacion": "listar_jurisdiccionesPerc"},
        "parameters": {
            "sesion": {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave},
            "idEmpresa": id_empresa,
        },
    }
    data = await call_api(payload)
    resp = data.get("response") or {}
    if resp.get("success"):
        return resp.get("data", [])
    print(f"[INFO] listar_jurisdiccionesPerc response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    return []


async def main():
    id_empresa = os.getenv("COLPPY_ID_EMPRESA")
    print(f"=== Colppy percsufridas API Test ===")
    print(f"Empresa: {id_empresa}")
    print()

    # Step 1: Login
    clave = await login()
    print()

    # Step 2: List available jurisdictions
    print("--- Step 2: Available IIBB Jurisdictions ---")
    jurisdicciones = await listar_jurisdicciones(clave, id_empresa)
    if jurisdicciones:
        print(f"[OK] {len(jurisdicciones)} jurisdictions available:")
        for j in jurisdicciones[:10]:
            print(f"  - {json.dumps(j, ensure_ascii=False)}")
    else:
        print("[INFO] No jurisdictions configured for this company")
    print()

    # Step 3: List recent purchase invoices, find one with percepcionIIBB > 0
    print("--- Step 3: Find invoice with IIBB perceptions ---")
    facturas = await list_facturas_compra(clave, id_empresa, limit=50)

    factura_with_iibb = None
    print(f"  Scanning {len(facturas)} invoices for IIBB perceptions...")
    for i, f in enumerate(facturas):
        perc = float(f.get("percepcionIIBB", 0) or 0)
        if i < 5:  # Show first 5 for context
            print(f"  [{i}] id={f.get('idFactura')} nro={f.get('nroFactura1')}-{f.get('nroFactura2')} percIIBB={f.get('percepcionIIBB')} total={f.get('totalFactura')} fecha={f.get('fechaFactura')}")
        if perc > 0 and factura_with_iibb is None:
            factura_with_iibb = f

    if factura_with_iibb:
        print(f"\n[OK] Found invoice with percepcionIIBB > 0:")
        print(f"  idFactura: {factura_with_iibb.get('idFactura')}")
        print(f"  nroFactura: {factura_with_iibb.get('nroFactura1')}-{factura_with_iibb.get('nroFactura2')}")
        print(f"  percepcionIIBB: {factura_with_iibb.get('percepcionIIBB')}")
        print(f"  totalFactura: {factura_with_iibb.get('totalFactura')}")
        print(f"  fechaFactura: {factura_with_iibb.get('fechaFactura')}")
    else:
        print("\n[INFO] No invoices with percepcionIIBB > 0 found in last 50")
        if facturas:
            factura_with_iibb = facturas[0]
            print(f"[INFO] Using first invoice: idFactura={factura_with_iibb.get('idFactura')}")
    print()

    if not factura_with_iibb:
        print("[SKIP] No invoices found, cannot test further")
        return

    # Step 4: Read the full invoice
    id_factura = factura_with_iibb.get("idFactura")
    print(f"--- Step 4: Read invoice {id_factura} ---")
    factura_detail = await leer_factura_compra(clave, id_empresa, str(id_factura))
    if factura_detail:
        info = factura_detail.get("infofactura", {})
        print(f"[OK] Invoice details:")
        print(f"  percepcionIIBB: {info.get('percepcionIIBB')}")
        print(f"  percepcionIIBB1: {info.get('percepcionIIBB1', 'N/A')}")
        print(f"  percepcionIIBB2: {info.get('percepcionIIBB2', 'N/A')}")
        print(f"  percepcionIVA: {info.get('percepcionIVA')}")
        print(f"  IIBBLocal: {info.get('IIBBLocal')}")
        print(f"  IIBBOtro: {info.get('IIBBOtro')}")
    print()

    # Step 5: List percsufridas for this invoice
    print(f"--- Step 5: List percsufridas for invoice {id_factura} ---")
    percs = await listar_percsufridas(clave, id_empresa, str(id_factura))
    if percs:
        if isinstance(percs, list):
            print(f"[OK] {len(percs)} percepciones sufridas found:")
            for p in percs:
                print(f"  - {json.dumps(p, ensure_ascii=False)}")
        else:
            print(f"[OK] Response: {json.dumps(percs, indent=2, ensure_ascii=False)[:500]}")
    else:
        print("[INFO] No percsufridas records for this invoice")
    print()

    # Step 6: List all empresas to find one with IIBB perceptions
    print("--- Step 6: List empresas ---")
    emp_payload = {
        "auth": auth_block(),
        "service": {"provision": "Empresa", "operacion": "listar_empresa"},
        "parameters": {
            "sesion": {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave},
            "start": 0,
            "limit": 50,
            "filter": [],
            "order": {"field": ["IdEmpresa"], "order": "asc"},
        },
    }
    emp_data = await call_api(emp_payload)
    emp_resp = emp_data.get("response") or {}
    if emp_resp.get("success"):
        empresas = emp_resp.get("data", [])
        if isinstance(empresas, list):
            print(f"[OK] {len(empresas)} empresas found:")
            for e in empresas[:15]:
                print(f"  id={e.get('IdEmpresa')} nombre={e.get('razonSocial', e.get('nombreFantasia', '?'))[:40]} condIVA={e.get('idCondicionIva')}")
        else:
            print(f"[INFO] Single empresa: {json.dumps(empresas, ensure_ascii=False)[:200]}")
    else:
        print(f"[FAIL] listar_empresa: {json.dumps(emp_data, indent=2, ensure_ascii=False)[:300]}")
    print()

    # Step 7: Try scanning a few empresas for invoices with percepcionIIBB > 0
    print("--- Step 7: Scan empresas for IIBB perceptions ---")
    if emp_resp.get("success") and isinstance(emp_resp.get("data"), list):
        for emp in emp_resp["data"][:10]:
            eid = str(emp.get("IdEmpresa"))
            try:
                fcts = await list_facturas_compra(clave, eid, limit=20)
                with_iibb = [f for f in fcts if float(f.get("percepcionIIBB", 0) or 0) > 0]
                if with_iibb:
                    print(f"  [FOUND] Empresa {eid}: {len(with_iibb)} invoices with percepcionIIBB > 0")
                    for f in with_iibb[:3]:
                        print(f"    idFactura={f.get('idFactura')} percIIBB={f.get('percepcionIIBB')} total={f.get('totalFactura')}")
                    break
            except Exception as ex:
                print(f"  Empresa {eid}: error - {ex}")
    print()

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
