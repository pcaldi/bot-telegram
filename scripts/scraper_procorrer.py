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

        items = soup.select(".js-item-product, .item-product")
        if not items:
            items = soup.select("div[class*=product]")

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
            if t.isupper() and len(t) > 10 and "R$" not in t:
                name = t.strip().title()
                break

        if not name:
            for t in texts:
                if len(t) > 10 and "R$" not in t and t.lower() not in ("comprar", "cor", "tamanho", "ver"):
                    name = t.strip()
                    break

        if not name:
            name_el = item.select_one("h2, h3, h4, span[class*=name], span[class*=title]")
            if name_el:
                name = name_el.get_text(strip=True)

        if not name:
            return None

        price_text = ""
        prices = []
        parcelamento = None
        preco_pix = None

        for i, t in enumerate(texts):
            if "R$" in t:
                try:
                    val = parse_preco(t)
                    if val > 0:
                        prev = texts[i - 1].strip() if i > 0 else ""
                        nxt = texts[i + 1].strip() if i + 1 < len(texts) else ""
                        prev_lower = prev.lower()
                        nxt_lower = nxt.lower()

                        if "pix" in prev_lower or "pix" in nxt_lower:
                            preco_pix = val
                            continue

                        is_installment = (
                            re.match(r'^\d+\s*x$', prev_lower)
                            or re.match(r'^x\s*\d+$', prev_lower)
                            or "juros" in nxt_lower
                            or "parcela" in nxt_lower
                        )
                        if is_installment:
                            parcelamento = f"{prev} {t}".strip()
                            continue

                        prices.append((t, val))
                except Exception:
                    pass

        if not prices:
            return None

        preco_antigo = None
        preco = 0
        for t, val in prices:
            if val == 0:
                continue
            if preco == 0:
                preco = val
            elif val > preco and preco_antigo is None:
                preco_antigo = val
            elif val < preco:
                preco_antigo = preco
                preco = val

        if preco <= 0:
            return None

        link_el = item.select_one("a[href*='/produtos/']") or item.select_one("a[href]")
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
            imagem = (
                img_el.get("src", "")
                or img_el.get("data-src", "")
                or img_el.get("data-lazy-src", "")
                or img_el.get("data-original", "")
            )
            if imagem and imagem.startswith("//"):
                imagem = f"https:{imagem}"
            if not imagem or "placeholder" in imagem or imagem.startswith("data:"):
                srcset = img_el.get("data-srcset", "")
                if srcset:
                    primeira = srcset.split(",")[0].strip().split(" ")[0]
                    if primeira.startswith("//"):
                        primeira = f"https:{primeira}"
                    imagem = primeira

        tamanhos = []
        size_els = item.select("button[data-option], .size-option, .tamanho, [class*=size] button")
        for el in size_els:
            txt = el.get_text(strip=True)
            if txt and len(txt) <= 5:
                tamanhos.append(txt)

        return self.criar_produto(
            nome=name[:100],
            preco=preco,
            url=href,
            preco_antigo=preco_antigo,
            imagem=imagem,
            preco_pix=preco_pix,
            parcelamento=parcelamento,
            tamanhos=tamanhos if tamanhos else None,
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
