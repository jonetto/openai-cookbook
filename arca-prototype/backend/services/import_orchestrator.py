"""
Import orchestrator — the core of the onboarding import tool.

Coordinates all data sources (AFIP enrichment, ARCA comprobantes, retenciones,
notifications) into a single SSE stream. Runs enrichment in parallel with ARCA
login, then sequential ARCA operations on a shared browser session.

Yields SSE-formatted strings that the FastAPI endpoint streams to the client.
"""
import asyncio
import json
import urllib.parse
import uuid
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Literal

from backend.services.arca_session import ArcaSession
from backend.services.cuit_enrichment import enrich_cuit

# Reuse pure parser functions from comprobantes_api — no browser dependency
from backend.services.comprobantes_api import (
    MCMP_BASE,
    _parse_comprobante_emitido,
    _parse_comprobante_recibido,
)


def _sse(event_type: str, data: dict) -> str:
    """Format a single SSE event string."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event_type}\ndata: {payload}\n\n"


# ── Comprobantes fetching (adapted for shared session) ─────────────────────


async def _fetch_comprobantes_streaming(
    mcmp_page,
    cuit: str,
    fecha_desde: str,
    fecha_hasta: str,
    tipo: Literal["R", "E"],
    id_contribuyente: int = 1,
) -> AsyncGenerator[tuple[str, dict], None]:
    """Fetch comprobantes on an already-authenticated MCMP page.

    Yields (event_type, payload) tuples for each batch and completion.
    Adapted from comprobantes_api._fetch_comprobantes (lines 206-413),
    but accepts an existing Page instead of launching a new browser.
    """
    page_do = "comprobantesRecibidos.do" if tipo == "R" else "comprobantesEmitidos.do"
    parser = _parse_comprobante_recibido if tipo == "R" else _parse_comprobante_emitido
    event_prefix = "comprobantes_recibidos" if tipo == "R" else "comprobantes_emitidos"

    yield (f"{event_prefix}_start", {})
    running_total = 0

    try:
        # Select persona
        await mcmp_page.evaluate(
            """(idx) => {
                document.getElementById('idcontribuyente').value = String(idx);
                document.seleccionaEmpresaForm.submit();
            }""",
            id_contribuyente,
        )
        await asyncio.sleep(5)

        # Navigate to the right comprobantes page
        await mcmp_page.goto(f"{MCMP_BASE}/{page_do}", wait_until="networkidle")
        await asyncio.sleep(3)

        # Extract actual CUIT from page (may differ if representing another entity)
        actual_cuit = await mcmp_page.evaluate(
            """() => {
                const m = document.body.innerText.match(/REPRESENTANDO A:.*?\\[(\\d{2}-\\d{8}-\\d)\\]/);
                if (m) return m[1].replace(/-/g, '');
                return '';
            }"""
        ) or cuit

        fecha_param = f"{fecha_desde} - {fecha_hasta}"

        # Step 1: Generate query
        gen_url = (
            f"{MCMP_BASE}/ajax.do?f=generarConsulta&t={tipo}"
            f"&fechaEmision={urllib.parse.quote(fecha_param)}"
            f"&tiposComprobantes="
            f"&cuitConsultada={actual_cuit}"
        )
        gen_resp_text = await mcmp_page.evaluate(
            "async (url) => { const r = await fetch(url); return await r.text(); }",
            gen_url,
        )
        gen_data = json.loads(gen_resp_text)

        if gen_data.get("estado") != "ok":
            yield (f"{event_prefix}_complete", {"total": 0, "error": f"Query failed: {gen_data}"})
            return

        query_id = gen_data["datos"]["idConsulta"]

        # Step 2: Estimate results
        est_url = f"{MCMP_BASE}/ajax.do?f=estimarResultados&id={query_id}"
        est_resp_text = await mcmp_page.evaluate(
            "async (url) => { const r = await fetch(url); return await r.text(); }",
            est_url,
        )
        est_data = json.loads(est_resp_text)
        server_side = est_data.get("datos", {}).get("serverSide", False)

        # Step 3: Fetch results (streaming batches)

        if not server_side:
            # All data in one call
            list_url = f"{MCMP_BASE}/ajax.do?f=listaResultados&id={query_id}"
            list_resp_text = await mcmp_page.evaluate(
                "async (url) => { const r = await fetch(url); return await r.text(); }",
                list_url,
            )
            list_data = json.loads(list_resp_text)
            raw_rows = list_data.get("datos", {}).get("data", [])
            comprobantes = []
            for raw in raw_rows:
                try:
                    comprobantes.append(parser(raw))
                except Exception:
                    pass
            running_total = len(comprobantes)
            if comprobantes:
                yield (f"{event_prefix}_batch", {
                    "comprobantes": comprobantes,
                    "count": len(comprobantes),
                    "running_total": running_total,
                })
        else:
            # Server-side pagination — stream each page as a batch
            start = 0
            page_size = 500
            max_retries = 3
            while True:
                list_url = (
                    f"{MCMP_BASE}/ajax.do?f=listaResultados&id={query_id}"
                    f"&start={start}&length={page_size}"
                )
                list_resp_text = ""
                for attempt in range(max_retries):
                    list_resp_text = await mcmp_page.evaluate(
                        "async (url) => { const r = await fetch(url); return await r.text(); }",
                        list_url,
                    )
                    if list_resp_text:
                        break
                    await asyncio.sleep(2 * (attempt + 1))

                if not list_resp_text:
                    break

                list_data = json.loads(list_resp_text)
                raw_rows = list_data.get("datos", {}).get("data", [])

                comprobantes = []
                for raw in raw_rows:
                    try:
                        comprobantes.append(parser(raw))
                    except Exception:
                        pass

                running_total += len(comprobantes)
                if comprobantes:
                    yield (f"{event_prefix}_batch", {
                        "comprobantes": comprobantes,
                        "count": len(comprobantes),
                        "running_total": running_total,
                    })

                if len(raw_rows) < page_size:
                    break
                start += page_size
                await asyncio.sleep(1)

        yield (f"{event_prefix}_complete", {"total": running_total})

    except Exception as e:
        yield ("error", {"stage": event_prefix, "message": str(e), "recoverable": True})
        yield (f"{event_prefix}_complete", {"total": running_total, "error": str(e)})


# ── Retenciones fetching (adapted for shared session) ──────────────────────


async def _fetch_retenciones_streaming(
    mret_page,
    cuit: str,
    fecha_desde: str,
    fecha_hasta: str,
    cuit_representado: str = "",
    impuesto: str = "767",
) -> AsyncGenerator[tuple[str, dict], None]:
    """Fetch retenciones on an already-authenticated Mirequa page.

    Yields (event_type, payload) tuples. Adapted from retenciones_api.download_retenciones,
    but accepts an existing Page instead of launching a new browser.
    """
    from backend.services.retenciones_api import IMPUESTO_OPTIONS, PERIODO_FORMAT

    yield ("retenciones_start", {})

    api_calls: list[dict] = []

    async def intercept_response(response):
        url = response.url
        if any(pat in url.lower() for pat in ["/api/", "retenciones", "consulta"]):
            try:
                body = await response.text()
            except Exception:
                body = ""
            api_calls.append({"url": url, "status": response.status, "body": body})

    mret_page.on("response", intercept_response)

    try:
        cuit_clean = "".join(c for c in cuit if c.isdigit())
        cuit_rep_clean = "".join(c for c in cuit_representado if c.isdigit()) if cuit_representado else ""

        # Representado selection inside Mirequa (if needed)
        if cuit_rep_clean and cuit_rep_clean != cuit_clean:
            try:
                cuit_formatted = f"{cuit_rep_clean[:2]}-{cuit_rep_clean[2:10]}-{cuit_rep_clean[10:]}"
                nav_links = mret_page.locator('nav a[href="#"]')
                nav_count = await nav_links.count()
                for i in range(nav_count):
                    link = nav_links.nth(i)
                    text = (await link.inner_text()).strip()
                    if 1 <= len(text) <= 4 and text.isalpha():
                        await link.click()
                        break
                await asyncio.sleep(2)

                sel_rep = mret_page.locator('a:has-text("Seleccionar representado"), button:has-text("Seleccionar representado")')
                await sel_rep.first.wait_for(state="visible", timeout=5000)
                await sel_rep.first.click()
                await asyncio.sleep(4)

                for cuit_text in [cuit_formatted, cuit_rep_clean]:
                    entity_card = mret_page.locator(f'[role="tab"]:has-text("{cuit_text}")')
                    if await entity_card.count() > 0:
                        await entity_card.first.click()
                        await asyncio.sleep(5)
                        break
            except Exception:
                pass  # Non-fatal: continue with active entity

        # Check SIAP export checkbox
        siap_checkbox = mret_page.locator("#exportarAplicativoCheck_input")
        if await siap_checkbox.count() > 0 and not await siap_checkbox.is_checked():
            await siap_checkbox.click()
            await asyncio.sleep(2)

        # Select Impuesto
        impuesto_code = IMPUESTO_OPTIONS.get(impuesto, f"IMP_{impuesto}")
        option_id = f"selectImpuestos-multiselect-option-{impuesto_code}"
        multiselect_input = mret_page.locator("#selectImpuestos")
        await multiselect_input.click()
        await asyncio.sleep(1)
        option_el = mret_page.locator(f"#{option_id}")
        if await option_el.count() > 0:
            await option_el.click()
            await asyncio.sleep(1)
        await mret_page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        title_el = mret_page.locator("h1, h2, .e-tabs-nav-link").first
        if await title_el.count() > 0:
            await title_el.click()
        await asyncio.sleep(1)

        # Select Retención radio
        radio_input = mret_page.locator('input[type="radio"][value="1"]')
        if await radio_input.count() > 0:
            await radio_input.click(force=True)
            await asyncio.sleep(0.5)

        # Fill dates (hasta first to avoid re-render issue)
        for field_id, date_value in [
            ("#datePickerFechasRetencionesHasta__input", fecha_hasta),
            ("#datePickerFechasRetencionesDesde__input", fecha_desde),
        ]:
            field = mret_page.locator(field_id)
            if await field.count() > 0:
                await field.click()
                await asyncio.sleep(0.3)
                await mret_page.keyboard.press("Escape")
                await asyncio.sleep(0.3)
                await field.fill(date_value)
                await asyncio.sleep(0.5)
                await mret_page.keyboard.press("Escape")
                await asyncio.sleep(0.2)

        # Blur date fields
        title_el = mret_page.locator("h1, h2, .e-tabs-nav-link").first
        if await title_el.count() > 0:
            await title_el.click()
        await asyncio.sleep(0.5)

        # Check if dates stuck; fallback to periodoFiscal
        desde_val = await mret_page.locator("#datePickerFechasRetencionesDesde__input").input_value()
        hasta_val = await mret_page.locator("#datePickerFechasRetencionesHasta__input").input_value()
        dates_filled = (1 if desde_val and len(desde_val) >= 8 else 0) + \
                       (1 if hasta_val and len(hasta_val) >= 8 else 0)

        if dates_filled < 2:
            periodo_field = mret_page.locator("#periodoFiscal")
            if await periodo_field.count() > 0:
                parts_d = fecha_desde.split("/")
                year = parts_d[2] if len(parts_d) == 3 else fecha_desde[:4]
                month = parts_d[1] if len(parts_d) == 3 else "01"
                periodo_len = PERIODO_FORMAT.get(impuesto, 6)
                periodo = f"{year}{month}" if periodo_len == 6 else year
                await periodo_field.click()
                await periodo_field.fill(periodo)
                await asyncio.sleep(0.3)

        # Click Consultar
        consultar = mret_page.locator("button:has-text('Consultar')").first
        if await consultar.count() == 0:
            yield ("retenciones_complete", {"total": 0, "error": "No se encontró botón Consultar"})
            return

        await consultar.click()
        await asyncio.sleep(8)

        # Check for intercepted JSON API response
        api_url = None
        first_page_data = None
        for call in api_calls:
            body = call.get("body", "")
            if not body or call.get("status", 0) != 200:
                continue
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict) and "retenciones" in parsed and "page" in parsed:
                    api_url = call["url"]
                    first_page_data = parsed
                    break
            except (json.JSONDecodeError, ValueError):
                continue

        if first_page_data and api_url:
            page_info = first_page_data["page"]
            total_elements = page_info.get("totalElements", 0)
            total_pages = page_info.get("totalPages", 1)
            all_retenciones = list(first_page_data["retenciones"])
            running_total = len(all_retenciones)

            if all_retenciones:
                yield ("retenciones_batch", {
                    "retenciones": all_retenciones,
                    "count": len(all_retenciones),
                    "running_total": running_total,
                })

            import re
            for page_num in range(1, total_pages):
                if "page=" in api_url:
                    paged_url = re.sub(r"page=\d+", f"page={page_num}", api_url)
                elif "?" in api_url:
                    paged_url = f"{api_url}&page={page_num}"
                else:
                    paged_url = f"{api_url}?page={page_num}"
                try:
                    page_text = await mret_page.evaluate(
                        "async (url) => { const r = await fetch(url); return await r.text(); }",
                        paged_url,
                    )
                    page_data = json.loads(page_text)
                    if "retenciones" in page_data:
                        batch = page_data["retenciones"]
                        running_total += len(batch)
                        yield ("retenciones_batch", {
                            "retenciones": batch,
                            "count": len(batch),
                            "running_total": running_total,
                        })
                except Exception:
                    break
                await asyncio.sleep(0.3)

            yield ("retenciones_complete", {"total": running_total})
        else:
            yield ("retenciones_complete", {"total": 0, "message": "No data captured from Mirequa API"})

    except Exception as e:
        yield ("error", {"stage": "retenciones", "message": str(e), "recoverable": True})
        yield ("retenciones_complete", {"total": 0, "error": str(e)})
    finally:
        mret_page.remove_listener("response", intercept_response)


# ── Notifications fetching (adapted for shared session) ────────────────────


async def _fetch_notifications_streaming(
    page,
    cuit: str,
) -> AsyncGenerator[tuple[str, dict], None]:
    """Fetch DFE notifications using an already-authenticated DFE session.

    The page should already be on ve.cloud.afip.gob.ar after open_dfe().
    Yields (event_type, payload) tuples.
    """
    from backend.services.notifications_api import _classify, _epoch_ms_to_iso, MAX_DETAIL_FETCH

    yield ("notifications_start", {})
    cuit_clean = "".join(c for c in cuit if c.isdigit())

    try:
        today = datetime.now()
        since = (today - timedelta(days=365)).strftime("%Y-%m-%d")
        to = today.strftime("%Y-%m-%d")

        list_url = (
            f"https://ve.cloud.afip.gob.ar/api/v1/communications"
            f"?cuit={cuit_clean}"
            f"&fechaPublicacionSince={since}"
            f"&fechaPublicacionTo={to}"
        )

        list_resp = await page.evaluate(
            """async (url) => {
                const r = await fetch(url);
                return { status: r.status, body: await r.text() };
            }""",
            list_url,
        )

        if list_resp["status"] != 200:
            yield ("notifications_complete", {"total": 0, "error": f"API returned {list_resp['status']}"})
            return

        list_data = json.loads(list_resp["body"])
        comunicaciones = list_data.get("comunicaciones", [])
        total = 0

        for i, comm in enumerate(comunicaciones):
            nid = comm["idComunicacion"]
            notif: dict[str, Any] = {
                "id": nid,
                "organismo": comm.get("organismoDesc", ""),
                "fecha_publicacion": _epoch_ms_to_iso(comm.get("fechaPublicacion")),
                "fecha_vencimiento": _epoch_ms_to_iso(comm.get("fechaVencimiento")),
                "sistema": comm.get("sistemaPublicador"),
                "estado": comm.get("estado"),
                "tiene_adjunto": comm.get("tieneAdjunto", False),
                "mensaje_preview": comm.get("mensaje", ""),
                "clasificacion": _classify(comm.get("tipo"), comm.get("prioridad")),
            }

            # Fetch detail for first N notifications
            if i < MAX_DETAIL_FETCH:
                detail_url = (
                    f"https://ve.cloud.afip.gob.ar/api/v1/communications/{nid}"
                    f"?id={nid}&cuit={cuit_clean}"
                )
                try:
                    detail_resp = await page.evaluate(
                        """async (url) => {
                            const r = await fetch(url);
                            return { status: r.status, body: await r.text() };
                        }""",
                        detail_url,
                    )
                    if detail_resp["status"] == 200:
                        detail_data = json.loads(detail_resp["body"])
                        comm_detail = detail_data.get("comunicacion", {})
                        notif["mensaje_completo"] = comm_detail.get("mensaje", "")
                        if comm_detail.get("sistemaPublicadorDesc"):
                            notif["sistema_desc"] = comm_detail["sistemaPublicadorDesc"]
                except Exception:
                    pass

            total += 1
            # Stream each notification individually
            yield ("notification", notif)

        yield ("notifications_complete", {"total": total})

    except Exception as e:
        yield ("error", {"stage": "notifications", "message": str(e), "recoverable": True})
        yield ("notifications_complete", {"total": 0, "error": str(e)})


# ── Main orchestrator ──────────────────────────────────────────────────────


async def run_import(
    cuit: str,
    password: str,
    fecha_desde: str = "",
    fecha_hasta: str = "",
) -> AsyncGenerator[str, None]:
    """Main orchestrator. Yields SSE-formatted strings.

    Runs two parallel tracks:
    - Track A: CUIT enrichment (AFIP + RNS, no browser, ~1-2s)
    - Track B: ARCA browser session (login + sequential scraping, ~60-120s)
    """
    job_id = str(uuid.uuid4())[:8]
    cuit_clean = "".join(c for c in cuit if c.isdigit())

    # Default date range: last 12 months
    if not fecha_hasta:
        fecha_hasta = datetime.now().strftime("%d/%m/%Y")
    if not fecha_desde:
        fecha_desde = (datetime.now() - timedelta(days=365)).strftime("%d/%m/%Y")

    yield _sse("job_started", {"job_id": job_id, "cuit": cuit_clean, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})

    # Track A: Enrichment (runs in parallel with ARCA login)
    enrichment_task = asyncio.create_task(enrich_cuit(cuit_clean))

    # Track B: ARCA session
    session = ArcaSession(cuit_clean, password)
    summary = {
        "comprobantes_recibidos": 0,
        "comprobantes_emitidos": 0,
        "retenciones": 0,
        "notifications": 0,
    }

    # Start ARCA login
    yield _sse("arca_login_start", {})
    login_result = await session.login()
    yield _sse("arca_login_complete", login_result)

    # Check if enrichment is done and yield its results
    if enrichment_task.done():
        afip_result, rns_result = enrichment_task.result()
        yield _sse("enrichment_afip", afip_result)
        yield _sse("enrichment_rns", rns_result)
    else:
        # Enrichment still running — yield when ready
        try:
            afip_result, rns_result = await asyncio.wait_for(enrichment_task, timeout=15)
            yield _sse("enrichment_afip", afip_result)
            yield _sse("enrichment_rns", rns_result)
        except asyncio.TimeoutError:
            yield _sse("enrichment_afip", {"error": True, "message": "Timeout"})
            yield _sse("enrichment_rns", {"found": False, "error": "Timeout"})

    if not login_result.get("success"):
        yield _sse("error", {"stage": "login", "message": login_result.get("message", "Login failed"), "recoverable": False})
        yield _sse("job_completed", {"job_id": job_id, "summary": summary, "success": False})
        await session.close()
        return

    fatal_error = False
    try:
        # Step 1: Comprobantes Recibidos
        mcmp_page = await session.open_mis_comprobantes()
        if mcmp_page:
            async for event_type, payload in _fetch_comprobantes_streaming(
                mcmp_page, cuit_clean, fecha_desde, fecha_hasta, tipo="R"
            ):
                yield _sse(event_type, payload)
                if event_type == "comprobantes_recibidos_complete":
                    summary["comprobantes_recibidos"] = payload.get("total", 0)

            # Step 2: Comprobantes Emitidos (reuse same MCMP page)
            async for event_type, payload in _fetch_comprobantes_streaming(
                mcmp_page, cuit_clean, fecha_desde, fecha_hasta, tipo="E"
            ):
                yield _sse(event_type, payload)
                if event_type == "comprobantes_emitidos_complete":
                    summary["comprobantes_emitidos"] = payload.get("total", 0)
        else:
            yield _sse("error", {"stage": "comprobantes", "message": "No se pudo abrir Mis Comprobantes", "recoverable": True})

        # Step 3: Retenciones
        mret_page = await session.open_mis_retenciones()
        if mret_page:
            async for event_type, payload in _fetch_retenciones_streaming(
                mret_page, cuit_clean, fecha_desde, fecha_hasta
            ):
                yield _sse(event_type, payload)
                if event_type == "retenciones_complete":
                    summary["retenciones"] = payload.get("total", 0)
        else:
            yield _sse("retenciones_start", {})
            yield _sse("retenciones_complete", {"total": 0, "error": "No se pudo abrir Mis Retenciones"})

        # Step 4: DFE Notifications
        dfe_auth = await session.open_dfe()
        if dfe_auth:
            async for event_type, payload in _fetch_notifications_streaming(
                session.portal_page, cuit_clean
            ):
                yield _sse(event_type, payload)
                if event_type == "notifications_complete":
                    summary["notifications"] = payload.get("total", 0)
        else:
            yield _sse("notifications_start", {})
            yield _sse("notifications_complete", {"total": 0, "error": "No se pudo acceder al DFE"})

    except Exception as e:
        yield _sse("error", {"stage": "general", "message": str(e), "recoverable": False})
        fatal_error = True
    finally:
        await session.close()
        yield _sse("job_completed", {"job_id": job_id, "summary": summary, "success": not fatal_error})
