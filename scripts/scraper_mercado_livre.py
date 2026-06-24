import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.browser_utils import fetch_playwright


def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
    try:
        html = fetch_playwright(url, wait_selector="li.ui-search-layout__item", extra_wait=5000)
    except Exception as e:
        print(f"Erro ao buscar no ML: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("li.ui-search-layout__item")
    if not items:
        items = soup.select("li[class*=ui-search]")

    for item in items[:10]:
        try:
            nome_el = item.select_one("h2.ui-search-item__title") or item.select_one("h2")
            link_el = item.select_one("a.ui-search-link") or item.select_one("a[href*='mercadolivre']")

            if not nome_el or not link_el:
                continue

            preco_el = (item.select_one("spanandes-money-amount__fraction") or
                       item.select_one("span.ui-search-price__second-line") or
                       item.select_one("span[class*=price]"))

            if not preco_el:
                continue

            preco_texto = preco_el.get_text().replace(".", "").replace(",", ".").strip()
            preco_texto = re.sub(r'[^\d.]', '', preco_texto)
            preco = float(preco_texto)

            if max_preco and preco > max_preco:
                continue

            preco_antigo = None
            preco_orig_el = item.select_one("span.ui-search-price__original-value")
            if preco_orig_el:
                preco_antigo_texto = preco_orig_el.get_text().replace(".", "").replace(",", ".").strip()
                preco_antigo_texto = re.sub(r'[^\d.]', '', preco_antigo_texto)
                try:
                    preco_antigo = float(preco_antigo_texto)
                except ValueError:
                    preco_antigo = None

            link = link_el["href"].split("#")[0]
            if link.startswith("/"):
                link = f"https://www.mercadolivre.com.br{link}"

            imagem = ""
            img_el = item.select_one("img")
            if img_el:
                imagem = img_el.get("src", "") or img_el.get("data-src", "")

            frete_el = item.select_one("span.ui-search-item__shipping--free")
            frete = "Grátis" if frete_el else "Pago"

            produto = {
                "nome": nome_el.get_text(strip=True),
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link,
                "loja": "Mercado Livre",
                "frete": frete,
                "imagem": imagem
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    produtos = buscar_produtos("tênis nike")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
