import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORIAS
from scripts.browser_utils import get_browser_page


async def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = f"https://www.netshoes.com.br/busca/{termo.replace(' ', '-')}"
    try:
        html = await get_browser_page(url, wait_selector="a.f-ads-product")
    except Exception as e:
        print(f"Erro ao buscar no Netshoes: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("a.f-ads-product")
    for item in items[:10]:
        try:
            nome_el = item.select_one("p.f-ads-name") or item.select_one("h3") or item.select_one("[class*=name]")
            preco_el = item.select_one("p.f-ads-sale-price")

            if not nome_el or not preco_el:
                continue

            preco_texto = preco_el.get_text().strip()
            preco_texto = re.sub(r'[^\d.,]', '', preco_texto).replace(".", "").replace(",", ".")
            preco = float(preco_texto)

            if max_preco and preco > max_preco:
                continue

            preco_antigo = None
            preco_old_el = item.select_one("p.f-ads-old-price")
            if preco_old_el:
                orig_text = preco_old_el.get_text().strip()
                orig_text = re.sub(r'[^\d.,]', '', orig_text).replace(".", "").replace(",", ".")
                try:
                    preco_antigo = float(orig_text)
                except ValueError:
                    preco_antigo = None

            link = item.get("href", "")
            if link.startswith("/"):
                link = f"https://www.netshoes.com.br{link}"

            produto = {
                "nome": nome_el.get_text(strip=True),
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link,
                "loja": "Netshoes",
                "frete": "Consulta"
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


async def buscar_todas_categorias() -> list:
    todos_produtos = []
    for cat_key, cat_info in CATEGORIAS.items():
        for termo in cat_info["palavras_chave"]:
            produtos = await buscar_produtos(termo, cat_info.get("max_preco"))
            todos_produtos.extend(produtos)
    return todos_produtos


if __name__ == "__main__":
    import asyncio
    produtos = asyncio.run(buscar_produtos("tênis puma"))
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
