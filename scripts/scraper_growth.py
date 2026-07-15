"""Scraper para Growth Suplementos.

Utiliza Playwright com stealth para extrair preços via JSON-LD.
"""

import sys
import os
import logging
from typing import Optional

# Adiciona o diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco
from scripts.browser_utils import BrowserManager

log = logging.getLogger("bot-ofertas.growth")


class GrowthScraper(BaseScraper):
    """Scraper para Growth Suplementos."""

    def __init__(self):
        super().__init__(
            nome_loja="Growth",
            emoji="💪",
            dominio="gsuplementos.com.br"
        )
        self.base_url = "https://www.gsuplementos.com.br"
        self.known_products = {
            "whey protein concentrado 1kg": "/whey-protein-concentrado-1kg-growth-supplements-p985936",
            "creatina monohidratada 250g": "/creatina-monohidratada-250gr-growth-supplements-p985931",
            "kit whey creatina": "/kit-whey-protein-concentrado-1kg-e-creatina-monohidratada-250g-growth-supplements",
        }

    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos na Growth.

        Args:
            termo: Termo de busca
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        mgr = BrowserManager.get()
        page = mgr.new_page()
        ctx = page.context

        try:
            return self._scrape([termo], ctx, max_preco)
        finally:
            try:
                page.close()
            except Exception:
                pass

    def _scrape(self, product_names: list, context, max_preco: Optional[float]) -> list:
        """Realiza o scraping de uma lista de produtos.

        Args:
            product_names: Lista de nomes de produtos para buscar
            context: Contexto do Playwright
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        products = []
        page = context.new_page()

        try:
            for name in product_names:
                try:
                    if name.lower() in self.known_products:
                        product_path = self.known_products[name.lower()]
                        product_url = f"{self.base_url}{product_path}"
                        product = self._scrape_product_page(page, product_url)
                        if product:
                            products.append(product)
                    else:
                        results = self._search_products(page, name)
                        for url in results[:3]:
                            product = self._scrape_product_page(page, url)
                            if product:
                                products.append(product)
                except Exception as e:
                    self.tratar_erro(f"Erro na busca '{name}'", e)
        finally:
            try:
                page.close()
            except Exception:
                pass

        return self.filtrar_por_preco(products, max_preco)

    def _search_products(self, page, query: str) -> list:
        """Busca produtos por termo de pesquisa.

        Args:
            page: Página Playwright
            query: Termo de busca

        Returns:
            Lista de URLs dos produtos encontrados
        """
        urls = []
        search_url = f"{self.base_url}/busca?q={query}"
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        links = page.query_selector_all("a[href]")
        for link in links:
            try:
                href = link.get_attribute("href")
                text = link.inner_text().strip()

                if not href or not text or "R$" not in text:
                    continue
                if href.startswith("/busca") or href.startswith("/categoria"):
                    continue
                if len(href) < 10 or href.count("-") < 2:
                    continue
                if not href.startswith("/"):
                    continue

                full_url = f"{self.base_url}{href}"
                if full_url not in urls:
                    urls.append(full_url)
            except Exception:
                continue

        return urls

    def _scrape_product_page(self, page, url: str) -> Optional[dict]:
        """Extrai dados de uma página de produto via JSON-LD.

        Args:
            page: Página Playwright
            url: URL do produto

        Returns:
            Dicionário com dados do produto ou None
        """
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            json_ld = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'Product') return data;
                        if (Array.isArray(data)) {
                            for (const item of data) {
                                if (item['@type'] === 'Product') return item;
                            }
                        }
                    } catch(e) {}
                }
                return null;
            }""")

            if not json_ld:
                return None

            offers = json_ld.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]

            price = parse_preco(str(offers.get("price", 0)))
            if price <= 0:
                return None

            image = json_ld.get("image", "")
            if isinstance(image, list) and image:
                image = image[0]

            name = json_ld.get("name", "")

            return self.criar_produto(
                nome=name,
                preco=price,
                url=url,
                imagem=image,
            )

        except Exception as e:
            self.tratar_erro(f"Erro ao scrape produto {url}", e)
            return None


# Função de conveniência para manter compatibilidade
def buscar_produtos(termo: str, preco_maximo: float = None, page=None, context=None) -> list:
    """Busca produtos na Growth (função de conveniência).

    Args:
        termo: Termo de busca
        preco_maximo: Preço máximo para filtrar
        page: Página Playwright (opcional)
        context: Contexto Playwright (opcional)

    Returns:
        Lista de produtos encontrados
    """
    scraper = GrowthScraper()

    if context is not None:
        return scraper._scrape([termo], context, preco_maximo)
    elif page is not None:
        return scraper._scrape([termo], page.context, preco_maximo)
    else:
        return scraper.buscar(termo, preco_maximo)
