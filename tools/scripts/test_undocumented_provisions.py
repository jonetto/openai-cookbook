#!/usr/bin/env python3
"""
Proof that undocumented Colppy API provisions work and return real data.

Calls 5 undocumented provisions (all READ-ONLY operations):
1. CondicionIVA.getCondicionesIVA — IVA tax conditions
2. CondicionIVA.getPorcentajesIVA — IVA percentage rates
3. Location.getCountries — supported countries
4. Location.getRegions — provinces/states for a country
5. TipoOperacionCompra.listar_tipo_de_operaciones_compra — purchase operation types

Uses DEMO empresa (11675) for safety.
"""

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / "arca-prototype" / ".env"
load_dotenv(env_path)

import httpx

COLPPY_API_URL = "https://login.colppy.com/lib/frontera2/service.php"
DEMO_EMPRESA = "11675"
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
        return resp.json()


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
        print(f"✅ Login OK (claveSesion: {clave[:8]}...)")
        return clave
    else:
        print(f"❌ Login failed: {json.dumps(data, indent=2)}")
        sys.exit(1)


def session_block(clave: str) -> dict:
    return {"usuario": os.getenv("COLPPY_USER"), "claveSesion": clave}


async def test_provision(name: str, provision: str, operation: str,
                         clave: str, extra_params: dict = None):
    """Call an operation and print the result summary."""
    params = {"sesion": session_block(clave)}
    if extra_params:
        params.update(extra_params)

    payload = {
        "auth": auth_block(),
        "service": {"provision": provision, "operacion": operation},
        "parameters": params,
    }

    print(f"\n{'='*60}")
    print(f"📡 {name}")
    print(f"   Provision: {provision}")
    print(f"   Operation: {operation}")
    if extra_params:
        print(f"   Params: {json.dumps(extra_params)}")
    print(f"{'='*60}")

    try:
        data = await call_api(payload)
        # Some provisions wrap in "response", others return flat
        response = data.get("response") or data
        success = response.get("success", False)

        if success:
            result_data = response.get("data", [])
            if isinstance(result_data, list):
                print(f"✅ SUCCESS — returned {len(result_data)} records")
                for i, record in enumerate(result_data[:3]):
                    print(f"   [{i}] {json.dumps(record, ensure_ascii=False)}")
                if len(result_data) > 3:
                    print(f"   ... and {len(result_data) - 3} more")
            elif isinstance(result_data, dict):
                print(f"✅ SUCCESS — returned object")
                print(f"   {json.dumps(result_data, ensure_ascii=False)[:200]}")
            else:
                print(f"✅ SUCCESS — {result_data}")

            total = response.get("total")
            if total is not None:
                print(f"   Total: {total}")
        else:
            msg = response.get("message", "unknown error")
            print(f"❌ FAILED — {msg}")

        # Debug: show raw structure
        print(f"   Top-level keys: {list(data.keys())}")
        if data.get("result"):
            print(f"   result: {json.dumps(data['result'], ensure_ascii=False)[:200]}")
        if data.get("response") is None:
            print(f"   response: None")

    except Exception as e:
        print(f"💥 ERROR — {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()


async def main():
    print("🔍 Testing Undocumented Colppy API Provisions")
    print("   All operations are READ-ONLY, using DEMO empresa 11675\n")

    clave = await login()

    # 1. CondicionIVA.getCondicionesIVA — no params needed
    await test_provision(
        "IVA Conditions (getCondicionesIVA)",
        "CondicionIVA", "getCondicionesIVA", clave,
    )

    # 2. CondicionIVA.getPorcentajesIVA — needs country_id
    await test_provision(
        "IVA Percentages for Argentina (getPorcentajesIVA)",
        "CondicionIVA", "getPorcentajesIVA", clave,
        {"country_id": "12"},  # 12 = Argentina
    )

    # 3. Location.getCountries — paginated
    await test_provision(
        "Countries (getCountries)",
        "Location", "getCountries", clave,
        {"start": 0, "limit": 10},
    )

    # 4. Location.getRegions — provinces for Argentina
    await test_provision(
        "Provinces of Argentina (getRegions)",
        "Location", "getRegions", clave,
        {"country_id": "12", "start": 0, "limit": 30},
    )

    # 5. TipoOperacionCompra
    await test_provision(
        "Purchase Operation Types (listar_tipo_de_operaciones_compra)",
        "TipoOperacionCompra", "listar_tipo_de_operaciones_compra", clave,
        {"idEmpresa": DEMO_EMPRESA},
    )

    print(f"\n{'='*60}")
    print("Done! All 5 undocumented provisions tested.")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
