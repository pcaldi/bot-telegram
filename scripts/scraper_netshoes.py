import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def buscar_produtos(termo: str, max_preco: float = None, context=None) -> list:
    url = f"https://www.netshoes.com.br/busca/{termo.replace(' ', '-')}"

    close_page = False
    if context:
        page = context.new_page()
        close_page = True
    else:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = context.new_page()

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(8000)
        html = page.content()
    except Exception as e:
        print(f"Erro ao buscar no Netshoes: {e}")
        return []
    finally:
        try:
            page.close()
        except Exception:
            pass
        if not close_page:
            try:
                browser.close()
                pw.stop()
            except Exception:
                pass

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("a.f-ads-product")
    if not items:
        items = soup.select("[class*=product] a")
    for item in items[:10]:
        try:
            nome_el = item.select_one("p.f-ads-name") or item.select_one("h3") or item.select_one("[class*=name]")
            preco_el = item.select_one("p.f-ads-sale-price") or item.select_one("[class*=price]")

            if not nome_el or not preco_el:
                continue

            preco_texto = preco_el.get_text().strip()
            preco_texto = re.sub(r'[^\d.,]', '', preco_texto).replace(".", "").replace(",", ".")
            if not preco_texto:
                continue
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

            imagem = ""
            img_el = item.select_one("img")
            if img_el:
                imagem = img_el.get("src", "") or img_el.get("data-src", "")

            produto = {
                "nome": nome_el.get_text(strip=True),
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link,
                "loja": "Netshoes",
                "frete": "Consulta",
                "imagem": imagem
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    produtos = buscar_produtos("tênis puma")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
