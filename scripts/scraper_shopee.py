import cloudscraper
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

scraper = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://shopee.com.br/"
}


def buscar_produtos(termo: str, max_preco: float = None) -> list:
    url = "https://shopee.com.br/api/v4/search/search_items"
    params = {
        "by": "relevancy",
        "keyword": termo,
        "limit": 10,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2
    }
    try:
        resp = scraper.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 403:
            print(f"Shopee bloqueou o acesso (403)")
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Erro ao buscar na Shopee: {e}")
        return []

    produtos = []
    items = data.get("items", [])

    for item in items[:10]:
        try:
            item_data = item.get("item_basic", {})
            nome = item_data.get("name", "")
            price = item_data.get("price", 0) / 100000
            price_min = item_data.get("price_min", 0) / 100000
            price_max = item_data.get("price_max", 0) / 100000

            if not nome or price <= 0:
                continue

            if max_preco and price > max_preco:
                continue

            item_id = item_data.get("itemid")
            shop_id = item_data.get("shopid")
            url_produto = f"https://shopee.com.br/product/{shop_id}/{item_id}"

            imagem = ""
            images = item_data.get("images", [])
            if images:
                imagem = f"https://cf.shopee.com.br/file/{images[0]}"

            produto = {
                "nome": nome,
                "preco": price,
                "preco_antigo": None,
                "url": url_produto,
                "loja": "Shopee",
                "frete": "Grátis" if item_data.get("show_free_shipping") else "Pago",
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
