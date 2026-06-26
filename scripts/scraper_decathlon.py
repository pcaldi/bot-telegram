"""Scraper para Decathlon Brasil.

Utiliza Playwright com stealth para extrair ofertas.
"""

import sys
import os
import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

# Adiciona o diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco
from scripts.browser_utils import BrowserManager

log = logging.getLogger("bot-ofertas.decathlon")


class DecathlonScraper(BaseScraper):
    """Scraper para Decathlon Brasil."""

    def __init__(self):
        super().__init__(
            nome_loja="Decathlon",
            emoji="🔵",
            dominio="decathlon.com.br"
        )

    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos no Decathlon.

        Args:
            termo: Termo de busca
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        url = f"https://www.decathlon.com.br/busca?q={termo.replace(' ', '+')}"

        mgr = BrowserManager.get()
        page = mgr.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
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

        items = soup.select("div[class*=product-card]")
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
        """Parseia um item de busca do Decathlon.

        Args:
            item: Elemento BeautifulSoup do produto

        Returns:
            Dicionário com dados do produto ou None
        """
        texts = list(item.stripped_strings)
        if len(texts) < 3:
            return None

        name = ""
        for t in texts:
            if t.startswith("R$"):
                continue
            if len(t) > len(name):
                name = t

        if not name:
            name = texts[1] if len(texts) > 1 else texts[0]

        # Busca o preço
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

        # Link do produto
        link_el = item.select_one("a[href*='/p']") or item.select_one("a[href]")
        if not link_el:
            return None
        href = link_el.get("href", "")
        if href.startswith("/"):
            href = f"https://www.decathlon.com.br{href}"

        # Imagem do produto
        imagem = ""
        img_el = item.select_one("img")
        if img_el:
            imagem = img_el.get("src", "") or img_el.get("data-src", "")

        # Preço anterior (se houver desconto)
        preco_antigo = None
        for t in texts[texts.index(price_text) + 1:]:
            if "R$" in t:
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


# Função de conveniência para manter compatibilidade
def buscar_produtos(termo: str, max_preco: float = None, context=None) -> list:
    """Busca produtos no Decathlon (função de conveniência).

    Args:
        termo: Termo de busca
        max_preco: Preço máximo para filtrar
        context: Contexto Playwright (opcional)

    Returns:
        Lista de produtos encontrados
    """
    scraper = DecathlonScraper()
    return scraper.buscar(termo, max_preco)


if __name__ == "__main__":
    # Teste rápido
    produtos = buscar_produtos("tênis corrida")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
