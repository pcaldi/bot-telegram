import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.browser_utils import get_browser_page


async def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = f"https://www.centauro.com.br/busca?q={termo.replace(' ', '+')}"
    try:
        html = await get_browser_page(url, extra_wait=5000)
    except Exception as e:
        print(f"Erro ao buscar no Centauro: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("a[href*='/p/']")
    if not items:
        items = soup.select("[class*=product] a[href]")

    seen = set()
    for item in items[:15]:
        try:
            href = item.get("href", "")
            if not href or not "/p/" in href:
                continue

            if href in seen:
                continue
            seen.add(href)

            name = item.get_text(strip=True)
            if len(name) < 5:
                continue

            card = item
            preco_el = card.select_one("[class*=price]") or card.select_one("[class*=Price]")
            if not preco_el:
                continue

            preco_texto = preco_el.get_text().strip()
            preco_texto = re.sub(r'[^\d.,]', '', preco_texto).replace(".", "").replace(",", ".")
            if not preco_texto:
                continue
            preco = float(preco_texto)

            if max_preco and preco > max_preco:
                continue

            link = href
            if link.startswith("/"):
                link = f"https://www.centauro.com.br{link}"

            produto = {
                "nome": name[:100],
                "preco": preco,
                "preco_antigo": None,
                "url": link,
                "loja": "Centauro",
                "frete": "Consulta"
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    import asyncio
    produtos = asyncio.run(buscar_produtos("tênis adidas"))
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
