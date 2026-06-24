import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORIAS
from scripts.browser_utils import get_browser_page


async def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = f"https://www.decathlon.com.br/busca?q={termo.replace(' ', '+')}"
    try:
        html = await get_browser_page(url, extra_wait=5000)
    except Exception as e:
        print(f"Erro ao buscar no Decathlon: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("[class*=product]")
    for item in items[:15]:
        try:
            nome_el = item.select_one("h3") or item.select_one("[class*=title]") or item.select_one("p")
            link_el = item if item.name == "a" else item.select_one("a[href]")

            if not nome_el or not link_el:
                continue

            name_text = nome_el.get_text(strip=True)
            if len(name_text) < 5:
                continue

            href = link_el.get("href", "")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.decathlon.com.br{href}"

            # Look for price in the item
            price_text = ""
            for text_node in item.stripped_strings:
                if "R$" in text_node:
                    price_text = text_node
                    break

            if not price_text:
                continue

            preco_texto = re.sub(r'[^\d.,]', '', price_text).replace(".", "").replace(",", ".")
            if not preco_texto:
                continue
            preco = float(preco_texto)

            if max_preco and preco > max_preco:
                continue

            produto = {
                "nome": name_text[:100],
                "preco": preco,
                "preco_antigo": None,
                "url": href,
                "loja": "Decathlon",
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
    produtos = asyncio.run(buscar_produtos("tênis corrida"))
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
