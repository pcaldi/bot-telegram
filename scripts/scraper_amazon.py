"""Scraper para Amazon Brasil.

Utiliza cloudscraper para contornar proteções básicas e extrair ofertas.
"""

import sys
import os
import logging
from typing import Optional

import cloudscraper
from bs4 import BeautifulSoup

# Adiciona o diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco

log = logging.getLogger("bot-ofertas.amazon")


class AmazonScraper(BaseScraper):
    """Scraper para Amazon Brasil."""

    def __init__(self):
        super().__init__(
            nome_loja="Amazon",
            emoji="🟡",
            dominio="amazon.com.br"
        )
        self.scraper = cloudscraper.create_scraper()

    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos na Amazon.

        Args:
            termo: Termo de busca
            max_preco: Preço máximo para filtrar

        Returns:
            Lista de produtos encontrados
        """
        url = f"https://www.amazon.com.br/s?k={termo.replace(' ', '+')}"

        try:
            resp = self.scraper.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            self.tratar_erro(f"Erro ao buscar '{termo}'", e)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        produtos = []

        items = soup.select("div[data-component-type='s-search-result']")
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
        """Parseia um item de busca da Amazon.

        Args:
            item: Elemento BeautifulSoup do produto

        Returns:
            Dicionário com dados do produto ou None
        """
        nome_el = item.select_one("h2")
        link_el = nome_el.find_parent("a") if nome_el else None
        img_el = item.select_one("img.s-image")

        if not nome_el or not link_el:
            return None

        nome = nome_el.get_text(strip=True)
        if not nome:
            return None

        link = link_el.get("href", "")
        if not link:
            return None
        if link.startswith("/"):
            link = f"https://www.amazon.com.br{link}"

        # Parse do preço atual
        preco_el = item.select_one("span.a-price-whole")
        preco_frac_el = item.select_one("span.a-price-fraction")

        if not preco_el:
            return None

        preco_texto = f"{preco_el.get_text().strip()}{preco_frac_el.get_text().strip() if preco_frac_el else '00'}"
        preco = parse_preco(preco_texto)

        if preco <= 0:
            return None

        # Parse do preço anterior (se houver desconto)
        preco_antigo = None
        preco_orig_el = item.select_one("span.a-price.a-text-price")
        if preco_orig_el:
            orig_text = preco_orig_el.get_text()
            if orig_text:
                try:
                    preco_antigo_texto = orig_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    preco_antigo = float(preco_antigo_texto)
                    if preco_antigo <= preco:
                        preco_antigo = None
                except ValueError:
                    preco_antigo = None

        # Imagem do produto
        imagem = img_el.get("src", "") if img_el else ""

        return self.criar_produto(
            nome=nome,
            preco=preco,
            url=link.split("/ref=")[0],
            preco_antigo=preco_antigo,
            imagem=imagem,
        )


# Função de conveniência para manter compatibilidade
def buscar_produtos(termo: str, max_preco: float = None) -> list:
    """Busca produtos na Amazon (função de conveniência).

    Args:
        termo: Termo de busca
        max_preco: Preço máximo para filtrar

    Returns:
        Lista de produtos encontrados
    """
    scraper = AmazonScraper()
    return scraper.buscar(termo, max_preco)


if __name__ == "__main__":
    # Teste rápido
    produtos = buscar_produtos("fone bluetooth")
    for p in produtos[:5]:
        print(f"{p['nome'][:50]} - R$ {p['preco']:.2f}")
        print(f"  img: {p.get('imagem', '')[:60]}")
