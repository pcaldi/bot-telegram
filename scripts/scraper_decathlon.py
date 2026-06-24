import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    items = soup.select("div[class*=product-card]")
    for item in items[:10]:
        try:
            texts = list(item.stripped_strings)
            if len(texts) < 3:
                continue

            name = texts[1] if len(texts) > 1 else texts[0]

            price_text = ""
            for t in texts:
                if "R$" in t:
                    price_text = t
                    break

            if not price_text:
                continue

            preco_texto = re.sub(r'[^\d.,]', '', price_text).replace(".", "").replace(",", ".")
            if not preco_texto:
                continue
            preco = float(preco_texto)

            if max_preco and preco > max_preco:
                continue

            link_el = item.select_one("a[href*='/p']") or item.select_one("a[href]")
            if not link_el:
                continue
            href = link_el.get("href", "")
            if href.startswith("/"):
                href = f"https://www.decathlon.com.br{href}"

            imagem = ""
            img_el = item.select_one("img")
            if img_el:
                imagem = img_el.get("src", "") or img_el.get("data-src", "")

            preco_antigo = None
            for t in texts[texts.index(price_text) + 1:]:
                if "R$" in t:
                    try:
                        old_text = re.sub(r'[^\d.,]', '', t).replace(".", "").replace(",", ".")
                        preco_antigo = float(old_text)
                    except ValueError:
                        preco_antigo = None
                    break

            produto = {
                "nome": name[:100],
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": href,
                "loja": "Decathlon",
                "frete": "Consulta",
                "imagem": imagem
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    import asyncio
    produtos = asyncio.run(buscar_produtos("tênis corrida"))
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
