from playwright.sync_api import sync_playwright
import asyncio


def _fetch_sync(url: str, wait_selector: str = None, timeout: int = 20000, extra_wait: int = 3000) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=timeout)
            except Exception:
                pass
        page.wait_for_timeout(extra_wait)
        html = page.content()
        browser.close()
    return html


async def get_browser_page(url: str, wait_selector: str = None, timeout: int = 20000, extra_wait: int = 3000):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _fetch_sync, url, wait_selector, timeout, extra_wait
    )
