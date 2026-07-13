"""Scraper para Mercado Livre.

Utiliza Playwright + stealth para buscar produtos no Mercado Livre.
Anti-bot do ML requer stealth browser.
"""

import sys
import os
import logging
import re
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco
from scripts.browser_utils import BrowserManager

log = logging.getLogger("bot-ofertas.mercadolivre")


class MercadoLivreScraper(BaseScraper):
    """Scraper para Mercado Livre."""

    def __init__(self):
        super().__init__(
            nome_loja="Mercado Livre",
            emoji="🟠",
            dominio="mercadolivre.com.br",
        )
        self._bm = BrowserManager()

    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos no Mercado Livre.

        Args:
            termo: Termo de busca
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"

        try:
            page = self._bm.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(8000)

            items = page.query_selector_all("div.poly-card")
            produtos = []

            for item in items[:10]:
                try:
                    produto = self._parse_item(item)
                    if produto:
                        produtos.append(produto)
                except Exception as e:
                    self.log.debug("Erro ao parsear item ML: %s", e)
                    continue

            page.close()
            return self.filtrar_por_preco(produtos, max_preco)

        except Exception as e:
            self.tratar_erro(f"Erro ao buscar '{termo}'", e)
            return []

    def _parse_item(self, item) -> Optional[dict]:
        """Parseia um card de produto do Mercado Livre.

        Args:
            item: Elemento Playwright do card

        Returns:
            Dicionário com dados do produto ou None
        """
        # Nome
        title_el = item.query_selector("a.poly-component__title")
        if not title_el:
            return None
        name = (title_el.inner_text() or "").strip()
        if not name:
            return None

        # Preço atual
        price_el = item.query_selector("span.andes-money-amount__fraction")
        cents_el = item.query_selector("span.andes-money-amount__cents")
        if not price_el:
            return None

        price_text = (price_el.inner_text() or "").strip()
        cents_text = (cents_el.inner_text() or "00").strip() if cents_el else "00"
        preco = parse_preco(f"{price_text},{cents_text}")
        if preco <= 0:
            return None

        # Link
        href = (title_el.get_attribute("href") or "").strip()
        if not href or not href.startswith("http"):
            return None

        # Imagem
        imagem = ""
        img_el = item.query_selector("img.poly-component__picture")
        if img_el:
            imagem = (img_el.get_attribute("src") or "").strip()
            if imagem.startswith("//"):
                imagem = f"https:{imagem}"

        # Parcelamento
        parcelamento = None
        install_el = item.query_selector("span.poly-component__installments")
        if install_el:
            parcel_text = (install_el.inner_text() or "").strip()
            if parcel_text:
                parcelamento = parcel_text

        # Frete grátis
        frete = "Consulta"
        shipping_el = item.query_selector("span.poly-component__shipping")
        if shipping_el:
            shipping_text = (shipping_el.inner_text() or "").strip()
            if shipping_text:
                frete = shipping_text

        # Desconto / preço antigo
        preco_antigo = None
        discount_el = item.query_selector("span.poly-component__discount")
        if discount_el:
            discount_text = str(discount_el.inner_text() or "")
            match = re.search(r'(\d+)%', discount_text)
            if match:
                pct = int(match.group(1))
                preco_antigo = preco / (1 - pct / 100)

        return self.criar_produto(
            nome=name[:100],
            preco=preco,
            url=href,
            preco_antigo=preco_antigo,
            imagem=imagem,
            frete=frete,
            parcelamento=parcelamento,
        )


def buscar_produtos(termo: str, max_preco: float = None) -> list:
    """Busca produtos no Mercado Livre (função de conveniência).

    Args:
        termo: Termo de busca
        max_preco: Preço máximo para filtrar

    Returns:
        Lista de produtos encontrados
    """
    scraper = MercadoLivreScraper()
    return scraper.buscar(termo, max_preco)


if __name__ == "__main__":
    produtos = buscar_produtos("nike air max")
    for p in produtos[:5]:
        print(f"{p['nome'][:60]} - R$ {p['preco']:.2f}")
