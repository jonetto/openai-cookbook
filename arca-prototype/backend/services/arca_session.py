"""
Shared ARCA browser session manager.

Extracts the login logic from arca_scraper.py into a reusable class that keeps
the browser alive across multiple ARCA operations (comprobantes, retenciones,
notifications). This avoids redundant logins (~8-15s each) when running
multiple scraping tasks sequentially.

Usage:
    session = ArcaSession(cuit, password)
    result = await session.login()
    if result["success"]:
        mcmp_page = await session.open_mis_comprobantes()
        # ... use mcmp_page for comprobantes queries ...
        mret_page = await session.open_mis_retenciones()
        # ... use mret_page for retenciones queries ...
        dfe_auth = await session.open_dfe()
        # ... use dfe_auth for notifications API ...
    await session.close()
"""
import asyncio
import os
import urllib.parse
from typing import Any

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
)

ARCA_LOGIN_URL = os.getenv("ARCA_LOGIN_URL", "https://auth.afip.gob.ar/contribuyente/")
HEADLESS = os.getenv("ARCA_HEADLESS", "true").lower() == "true"
TIMEOUT_MS = int(os.getenv("ARCA_TIMEOUT_MS", "45000"))


class ArcaSession:
    """Manages a single Playwright browser session for ARCA operations."""

    def __init__(self, cuit: str, password: str):
        self.cuit = "".join(c for c in cuit if c.isdigit())
        self.password = password
        self._pw: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.portal_page: Page | None = None

    async def login(self) -> dict[str, Any]:
        """Launch browser and login to ARCA. Returns {success, message}.

        On success, self.portal_page is the authenticated portal page.
        The browser stays open for subsequent operations.
        """
        if len(self.cuit) != 11:
            return {"success": False, "message": "CUIT debe tener 11 dígitos"}

        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=HEADLESS)
        self.context = await self.browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            accept_downloads=True,
        )
        self.portal_page = await self.context.new_page()
        self.portal_page.set_default_timeout(TIMEOUT_MS)

        page = self.portal_page
        try:
            await page.goto(ARCA_LOGIN_URL, wait_until="networkidle")
            await asyncio.sleep(2)

            # Step 1: CUIT
            cuit_input = page.locator('input[name="F1:username"]')
            await cuit_input.wait_for(state="visible", timeout=10000)
            await cuit_input.fill(self.cuit)
            await page.locator('input[name="F1:btnSiguiente"]').click()
            await asyncio.sleep(3)

            # Step 2: Password
            password_input = page.locator('input[name="F1:password"]')
            await password_input.wait_for(state="visible", timeout=10000)
            await password_input.fill(self.password)
            await page.locator('input[name="F1:btnIngresar"]').click()
            await asyncio.sleep(8)

            # Check success
            current_url = page.url
            if "login" in current_url.lower() and "portal" not in current_url.lower():
                error_el = page.locator(
                    '.error, .alert-danger, [class*="error"], [role="alert"]'
                ).first
                if await error_el.count() > 0:
                    error_text = await error_el.text_content()
                    return {
                        "success": False,
                        "message": f"Error de login: {error_text or 'Credenciales inválidas'}",
                    }
                return {
                    "success": False,
                    "message": "Login fallido. Verifique CUIT y Clave Fiscal.",
                }

            return {"success": True, "message": "Login exitoso"}

        except PlaywrightTimeout as e:
            return {"success": False, "message": f"Timeout: {e}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def open_mis_comprobantes(self) -> Page | None:
        """Navigate to Mis Comprobantes from the portal search bar.

        Returns the MCMP page (new tab) or None on failure.
        Uses the pattern from comprobantes_api.py lines 264-280.
        """
        page = self.portal_page
        if not page:
            return None

        search_input = page.locator("#buscadorInput")
        await search_input.fill("Mis Comprobantes")
        await asyncio.sleep(2)
        await page.locator(".rbt-menu a, .rbt-menu li").first.click()
        await asyncio.sleep(10)

        all_pages = self.context.pages
        if len(all_pages) < 2:
            return None
        return all_pages[-1]

    async def open_mis_retenciones(self) -> Page | None:
        """Navigate to Mis Retenciones from the portal search bar.

        Returns the Mirequa page (new tab) or None on failure.
        Uses the pattern from retenciones_api.py lines 217-239.
        """
        page = self.portal_page
        if not page:
            return None

        search_input = page.locator("#buscadorInput")
        await search_input.wait_for(state="visible", timeout=15000)
        # Clear previous search and type new one
        await search_input.fill("")
        await asyncio.sleep(0.5)
        await search_input.fill("Mis Retenciones")
        await asyncio.sleep(2)

        menu_item = page.locator(".rbt-menu a, .rbt-menu li").first
        if await menu_item.count() > 0:
            await menu_item.click()
        else:
            await search_input.press("Enter")
        await asyncio.sleep(10)

        all_pages = self.context.pages
        if len(all_pages) < 2:
            return None

        mret = all_pages[-1]
        try:
            await mret.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(3)
        return mret

    async def open_dfe(self) -> dict[str, Any] | None:
        """Navigate to DFE and capture auth token/sign.

        Returns {token, sign} or None on failure.
        Uses the pattern from notifications_api.py lines 61-80.
        """
        page = self.portal_page
        if not page:
            return None

        auth_data: dict[str, Any] = {}

        async def capture_auth(resp):
            if "e-ventanilla/autorizacion" in resp.url:
                try:
                    auth_data["data"] = await resp.json()
                except Exception:
                    pass

        page.on("response", capture_auth)

        try:
            dfe_link = page.get_by_text("Domicilio Fiscal Electrónico", exact=False)
            await dfe_link.first.wait_for(state="visible", timeout=15000)
            await dfe_link.first.click()
            await asyncio.sleep(8)

            if "data" not in auth_data:
                return None

            token = auth_data["data"]["token"]
            sign = auth_data["data"]["sign"]

            # Open DFE app to establish session cookies
            dfe_url = (
                f"https://ve.cloud.afip.gob.ar/login"
                f"?token={urllib.parse.quote(token)}"
                f"&sign={urllib.parse.quote(sign)}"
            )
            await page.goto(dfe_url, wait_until="networkidle")
            await asyncio.sleep(4)

            # Dismiss info modal if present
            try:
                btn = page.get_by_role("button", name="ENTENDIDO")
                await btn.wait_for(state="visible", timeout=5000)
                await btn.click()
                await asyncio.sleep(1)
            except Exception:
                pass

            return {"token": token, "sign": sign}
        finally:
            page.remove_listener("response", capture_auth)

    async def close(self):
        """Close the browser. Call this when all operations are done."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self._pw:
            try:
                await self._pw.stop()
            except Exception:
                pass
            self._pw = None
