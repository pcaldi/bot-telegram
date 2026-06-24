import cloudscraper
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORIAS

scraper = cloudscraper.create_scraper()


def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = f"https://www.amazon.com.br/s?k={termo.replace(' ', '+')}"
    try:
        resp = scraper.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erro ao buscar na Amazon: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    produtos = []

    items = soup.select("div[data-component-type='s-search-result']")
    for item in items[:10]:
        try:
            nome_el = item.select_one("h2")
            if not nome_el:
                continue

            nome = nome_el.get_text(strip=True)
            if not nome:
                continue

            # Find the link - h2's parent is a span, grandparent may be an a
            link_el = None
            parent = nome_el.parent
            while parent and parent.name != "div":
                if parent.name == "a" and parent.get("href"):
                    link_el = parent
                    break
                parent = parent.parent

            # Fallback: look for a-link-normal with product text
            if not link_el:
                links = item.select("a.a-link-normal")
                for link in links:
                    if link.get_text(strip=True) and len(link.get_text(strip=True)) > 10:
                        link_el = link
                        break

            if not link_el:
                continue

            link = link_el.get("href", "")
            if not link:
                continue
            if link.startswith("/"):
                link = f"https://www.amazon.com.br{link}"

            # Price
            preco_el = item.select_one("span.a-price-whole")
            preco_frac_el = item.select_one("span.a-price-fraction")

            if not preco_el:
                continue

            preco_texto = f"{preco_el.get_text().strip()}{preco_frac_el.get_text().strip() if preco_frac_el else '00'}"
            preco = float(preco_texto.replace(".", "").replace(",", "."))

            if max_preco and preco > max_preco:
                continue

            # Original price
            preco_antigo = None
            preco_orig_el = item.select_one("span.a-price.a-text-price")
            if preco_orig_el:
                orig_text = preco_orig_el.get_text()
                if orig_text:
                    try:
                        preco_antigo_texto = orig_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        preco_antigo = float(preco_antigo_texto)
                    except ValueError:
                        preco_antigo = None

            frete_el = item.select_one("span.a-color-base.a-text-normal")
            frete = "Grátis" if frete_el and "Grátis" in frete_el.get_text() else "Pago"

            produto = {
                "nome": nome,
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link.split("/ref=")[0],
                "loja": "Amazon",
                "frete": frete
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


def buscar_todas_categorias() -> list:
    todos_produtos = []
    for cat_key, cat_info in CATEGORIAS.items():
        for termo in cat_info["palavras_chave"]:
            produtos = buscar_produtos(termo, cat_info.get("max_preco"))
            todos_produtos.extend(produtos)
    return todos_produtos


if __name__ == "__main__":
    produtos = buscar_produtos("fone bluetooth")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
