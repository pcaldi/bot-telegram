from playwright.async_api import async_playwright


async def get_browser_page(url: str, wait_selector: str = None, timeout: int = 20000, extra_wait: int = 3000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            except Exception:
                pass
        await page.wait_for_timeout(extra_wait)
        html = await page.content()
        await browser.close()
    return html
