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
from config import ML_AFFILIATE_TAG

log = logging.getLogger("bot-ofertas.mercadolivre")

# Categorias de ofertas ML com seus IDs
ML_CATEGORIAS_OFERTAS = {
    "tenis": "MLB1051",
    "celulares": "MLB1055",
    "notebooks": "MLB1652",
    "monitores": "MLB1431",
    "fones": "MLB1000",
    "tv": "MLB1002",
    "smartwatches": "MLB1430",
    "ferramentas": "MLB5725",
    "games": "MLB1144",
    "esportes": "MLB1246",
}


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
        """Busca produtos no Mercado Livre (por busca).

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
            page.wait_for_timeout(5000)

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

    def buscar_ofertas(self, categoria: str = None, max_preco: Optional[float] = None) -> list:
        """Busca produtos na página de ofertas do ML.

        Args:
            categoria: Categoria para filtrar (ex: "tenis", "celulares")
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        url = "https://www.mercadolivre.com.br/ofertas"
        if categoria and categoria in ML_CATEGORIAS_OFERTAS:
            cat_id = ML_CATEGORIAS_OFERTAS[categoria]
            url = f"https://www.mercadolivre.com.br/ofertas#category={cat_id}"

        try:
            page = self._bm.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)

            items = page.query_selector_all("div.poly-card")
            produtos = []

            for item in items[:15]:
                try:
                    produto = self._parse_item(item)
                    if produto:
                        produtos.append(produto)
                except Exception as e:
                    self.log.debug("Erro ao parsear item ML ofertas: %s", e)
                    continue

            page.close()
            return self.filtrar_por_preco(produtos, max_preco)

        except Exception as e:
            self.tratar_erro(f"Erro ao buscar ofertas ML", e)
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

        # Preço atual - na página de ofertas usa poly-price__amount, na busca usa andes-money-amount__fraction
        price_el = item.query_selector("span.poly-price__amount span.andes-money-amount__fraction")
        if not price_el:
            price_el = item.query_selector("span.andes-money-amount__fraction")
        cents_el = item.query_selector("span.andes-money-amount__cents--superscript-24")
        if not cents_el:
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

        # Adiciona tag de afiliado ML
        if ML_AFFILIATE_TAG:
            separator = "&" if "?" in href else "?"
            href = f"{href}{separator}tag={ML_AFFILIATE_TAG}"

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

        # Desconto / preço antigo - elemento <s> com andes-money-amount--previous
        preco_antigo = None
        old_price_el = item.query_selector("s.andes-money-amount--previous")
        if old_price_el:
            old_fraction = old_price_el.query_selector("span.andes-money-amount__fraction")
            old_cents = old_price_el.query_selector("span.andes-money-amount__cents")
            if old_fraction:
                old_text = (old_fraction.inner_text() or "").strip()
                old_cents_text = (old_cents.inner_text() or "00").strip() if old_cents else "00"
                preco_antigo = parse_preco(f"{old_text},{old_cents_text}")

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


def buscar_ofertas(categoria: str = None, max_preco: float = None) -> list:
    """Busca ofertas na página de ofertas do ML (função de conveniência).

    Args:
        categoria: Categoria para filtrar (ex: "tenis", "celulares")
        max_preco: Preço máximo para filtrar

    Returns:
        Lista de produtos encontrados
    """
    scraper = MercadoLivreScraper()
    return scraper.buscar_ofertas(categoria, max_preco)


if __name__ == "__main__":
    print("=== Buscando ofertas gerais ===")
    ofertas = buscar_ofertas()
    for p in ofertas[:5]:
        print(f"{p['nome'][:60]} - R$ {p['preco']:.2f}")

    print("\n=== Buscando ofertas de tênis ===")
    ofertas_tenis = buscar_ofertas("tenis")
    for p in ofertas_tenis[:5]:
        print(f"{p['nome'][:60]} - R$ {p['preco']:.2f}")
