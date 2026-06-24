import sys
import os
import re
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GrowthScraper:
    def __init__(self):
        self.base_url = "https://www.gsuplementos.com.br"
        self.known_products = {
            "whey protein concentrado 1kg": "/whey-protein-concentrado-1kg-growth-supplements-p985936",
            "creatina monohidratada 250g": "/creatina-monohidratada-250gr-growth-supplements-p985931",
            "kit whey creatina": "/kit-whey-protein-concentrado-1kg-e-creatina-monohidratada-250g-growth-supplements",
        }

    def scrape(self, product_names, context=None):
        products = []
        page = context.new_page()

        try:
            for name in product_names:
                try:
                    if name.lower() in self.known_products:
                        product_path = self.known_products[name.lower()]
                        product_url = f"{self.base_url}{product_path}"
                        product = self._scrape_product_page(page, product_url)
                        if product:
                            products.append(product)
                    else:
                        results = self._search_products(page, name)
                        for url in results[:3]:
                            product = self._scrape_product_page(page, url)
                            if product:
                                products.append(product)
                except Exception as e:
                    print(f"  Erro Growth busca '{name}': {e}")
        finally:
            try:
                page.close()
            except Exception:
                pass

        return products

    def _search_products(self, page, query):
        urls = []
        search_url = f"{self.base_url}/busca?q={query}"
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(10000)

        links = page.query_selector_all("a[href]")
        for link in links:
            try:
                href = link.get_attribute("href")
                text = link.inner_text().strip()

                if not href or not text or "R$" not in text:
                    continue
                if href.startswith("/busca") or href.startswith("/categoria"):
                    continue
                if len(href) < 10 or href.count("-") < 2:
                    continue
                if not href.startswith("/"):
                    continue

                full_url = f"{self.base_url}{href}"
                if full_url not in urls:
                    urls.append(full_url)
            except Exception:
                continue

        return urls

    def _scrape_product_page(self, page, url):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            json_ld = page.evaluate("""() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'Product') return data;
                        if (Array.isArray(data)) {
                            for (const item of data) {
                                if (item['@type'] === 'Product') return item;
                            }
                        }
                    } catch(e) {}
                }
                return null;
            }""")

            if not json_ld:
                return None

            offers = json_ld.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]

            price = float(offers.get("price", 0))
            if price <= 0:
                return None

            image = json_ld.get("image", "")
            if isinstance(image, list) and image:
                image = image[0]

            name = json_ld.get("name", "")

            return {
                "nome": name,
                "preco": price,
                "imagem": image,
                "url": url,
                "loja": "Growth",
            }

        except Exception as e:
            print(f"  Erro Growth produto {url}: {e}")
            return None


def buscar_produtos(termo, preco_maximo=None, page=None, context=None):
    scraper = GrowthScraper()

    if context is not None:
        products = scraper.scrape([termo], context=context)
    elif page is not None:
        ctx = page.context
        products = scraper.scrape([termo], context=ctx)
    else:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                locale="pt-BR"
            )
            products = scraper.scrape([termo], context=ctx)
            browser.close()

    if preco_maximo:
        products = [p for p in products if p.get("preco", 0) <= preco_maximo]

    return products
