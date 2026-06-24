import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def buscar_produtos(termo: str, max_preco: float = None, context=None) -> list:
    url = f"https://www.centauro.com.br/busca?q={termo.replace(' ', '+')}"

    close_page = False
    pw = None
    browser = None
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
        print(f"Erro ao buscar no Centauro: {e}")
        return []
    finally:
        try:
            page.close()
        except Exception:
            pass
        if not close_page:
            try:
                if browser:
                    browser.close()
                if pw:
                    pw.stop()
            except Exception:
                pass

    soup = BeautifulSoup(html, "lxml")
    produtos = []

    items = soup.select("a[href*='/p/']")
    if not items:
        items = soup.select("[class*=product] a[href]")

    seen = set()
    for item in items[:15]:
        try:
            href = item.get("href", "")
            if not href or "/p/" not in href:
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

            imagem = ""
            img_el = item.select_one("img")
            if img_el:
                imagem = img_el.get("src", "") or img_el.get("data-src", "")

            preco_antigo = None
            old_el = card.select_one("[class*=old-price]") or card.select_one("[class*=original]")
            if old_el:
                old_text = old_el.get_text().strip()
                old_text = re.sub(r'[^\d.,]', '', old_text).replace(".", "").replace(",", ".")
                try:
                    preco_antigo = float(old_text)
                except ValueError:
                    preco_antigo = None

            produto = {
                "nome": name[:100],
                "preco": preco,
                "preco_antigo": preco_antigo,
                "url": link,
                "loja": "Centauro",
                "frete": "Consulta",
                "imagem": imagem
            }
            produtos.append(produto)
        except Exception:
            continue

    return produtos


if __name__ == "__main__":
    produtos = buscar_produtos("tênis adidas")
    for p in produtos[:5]:
        print(f"{p['nome']} - R$ {p['preco']:.2f}")
