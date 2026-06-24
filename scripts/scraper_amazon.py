import cloudscraper
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            link_el = nome_el.find_parent("a") if nome_el else None
            img_el = item.select_one("img.s-image")

            if not nome_el or not link_el:
                continue

            nome = nome_el.get_text(strip=True)
            if not nome:
                continue

            link = link_el.get("href", "")
            if not link:
                continue
            if link.startswith("/"):
                link = f"https://www.amazon.com.br{link}"

            preco_el = item.select_one("span.a-price-whole")
            preco_frac_el = item.select_one("span.a-price-fraction")

            if not preco_el:
                continue

            preco_texto = f"{preco_el.get_text().strip()}{preco_frac_el.get_text().strip() if preco_frac_el else '00'}"
            preco = float(preco_texto.replace(".", "").replace(",", "."))

            if max_preco and preco > max_preco:
                continue

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

            imagem = img_el.get("src", "") if img_el else ""

            produto = {
                "nome": nome,
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link.split("/ref=")[0],
                "loja": "Amazon",
                "frete": "Consulta",
                "imagem": imagem
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    produtos = buscar_produtos("fone bluetooth")
    for p in produtos[:5]:
        print(f"{p['nome'][:50]} - R$ {p['preco']:.2f}")
        print(f"  img: {p.get('imagem', '')[:60]}")
