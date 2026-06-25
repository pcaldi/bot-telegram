"""Scraper para Procorrer.

Utiliza Playwright com stealth para extrair ofertas de tênis de corrida.
"""

import sys
import os
import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco
from scripts.browser_utils import BrowserManager

log = logging.getLogger("bot-ofertas.procorrer")


class ProcorrerScraper(BaseScraper):
    """Scraper para Procorrer (tênis de corrida)."""

    def __init__(self):
        super().__init__(
            nome_loja="Procorrer",
            emoji="👟",
            dominio="procorrer.com.br"
        )
        self.base_url = "https://www.procorrer.com.br"

    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos na Procorrer.

        Args:
            termo: Termo de busca
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        url = f"{self.base_url}/busca?q={termo.replace(' ', '+')}"

        mgr = BrowserManager.get()
        page = mgr.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(8000)
            html = page.content()
        except Exception as e:
            self.tratar_erro(f"Erro ao buscar '{termo}'", e)
            return []
        finally:
            try:
                page.close()
            except Exception:
                pass

        soup = BeautifulSoup(html, "lxml")
        produtos = []

        items = soup.select("div.product-card, div[class*=product], li.product-item")
        if not items:
            items = soup.select("a[href*='/product'], a[href*='/produto']")

        for item in items[:10]:
            try:
                produto = self._parse_item(item)
                if produto:
                    produtos.append(produto)
            except Exception as e:
                self.log.debug("Erro ao parsear item: %s", e)
                continue

        return self.filtrar_por_preco(produtos, max_preco)

    def _parse_item(self, item) -> Optional[dict]:
        """Parseia um item de busca da Procorrer.

        Args:
            item: Elemento BeautifulSoup do produto

        Returns:
            Dicionário com dados do produto ou None
        """
        texts = list(item.stripped_strings)
        if not texts:
            return None

        name = ""
        for t in texts:
            if len(t) > 10 and "R$" not in t:
                name = t.strip()
                break

        if not name:
            name_el = item.select_one("h2, h3, h4, span[class*=name], span[class*=title]")
            if name_el:
                name = name_el.get_text(strip=True)

        if not name:
            return None

        price_text = ""
        for t in texts:
            if "R$" in t:
                price_text = t
                break

        if not price_text:
            return None

        preco = parse_preco(price_text)
        if preco <= 0:
            return None

        link_el = item.select_one("a[href]") if item.name != "a" else item
        if not link_el:
            return None
        href = link_el.get("href", "")
        if not href:
            return None
        if href.startswith("/"):
            href = f"{self.base_url}{href}"

        imagem = ""
        img_el = item.select_one("img")
        if img_el:
            imagem = img_el.get("src", "") or img_el.get("data-src", "")

        preco_antigo = None
        for t in texts:
            if "R$" in t and t != price_text:
                try:
                    old_text = re.sub(r'[^\d.,]', '', t).replace(".", "").replace(",", ".")
                    preco_antigo = float(old_text)
                    if preco_antigo <= preco:
                        preco_antigo = None
                except ValueError:
                    preco_antigo = None
                break

        return self.criar_produto(
            nome=name[:100],
            preco=preco,
            url=href,
            preco_antigo=preco_antigo,
            imagem=imagem,
        )


def buscar_produtos(termo: str, max_preco: float = None) -> list:
    """Busca produtos na Procorrer (função de conveniência).

    Args:
        termo: Termo de busca
        max_preco: Preço máximo para filtrar

    Returns:
        Lista de produtos encontrados
    """
    scraper = ProcorrerScraper()
    return scraper.buscar(termo, max_preco)


if __name__ == "__main__":
    produtos = buscar_produtos("tênis corrida")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
