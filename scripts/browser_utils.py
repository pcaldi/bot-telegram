import os
import time
import threading
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

log = logging.getLogger("bot-ofertas")

MAX_RETRIES = 3
RETRY_DELAY = 2

_stealth = Stealth(
    navigator_languages_override=("pt-BR", "pt"),
    navigator_platform_override="Win32",
)


class BrowserManager:
    _instances = []
    _instances_lock = threading.Lock()

    def __init__(self):
        self._pw = None
        self._browser = None
        self._context = None
        self._lock = threading.Lock()
        self._started = False

    @classmethod
    def get(cls) -> "BrowserManager":
        """Retorna instância compartilhada (compatibilidade)."""
        with cls._instances_lock:
            if not cls._instances:
                mgr = cls()
                cls._instances.append(mgr)
            return cls._instances[0]

    @classmethod
    def new_instance(cls) -> "BrowserManager":
        """Cria nova instância independente (para paralelismo)."""
        return cls()

    def start(self):
        with self._lock:
            if self._started:
                return
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                locale="pt-BR"
            )
            self._started = True
            log.info("Browser Playwright iniciado (stealth)")

    def new_page(self):
        self.start()
        page = self._context.new_page()
        _stealth.apply_stealth_sync(page)
        return page

    def stop(self):
        with self._lock:
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None
                self._context = None
            if self._pw:
                try:
                    self._pw.stop()
                except Exception:
                    pass
                self._pw = None
            self._started = False
            log.info("Browser Playwright fechado")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def fetch_playwright(url: str, wait_selector: str = None, timeout: int = 20000, extra_wait: int = 3000) -> str:
    last_error = None

    for attempt in range(MAX_RETRIES):
        mgr = BrowserManager.get()
        page = mgr.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=timeout)
                except Exception:
                    pass
            page.wait_for_timeout(extra_wait)
            html = page.content()
            return html
        except Exception as e:
            last_error = e
            log.warning("Tentativa %d/%d falhou para %s: %s", attempt + 1, MAX_RETRIES, url, e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        finally:
            try:
                page.close()
            except Exception:
                pass

    raise last_error
