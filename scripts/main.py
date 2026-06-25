import json
import asyncio
import hashlib
import re
import sys
import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Adiciona o diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PRODUTOS_MONITORADOS, SCRAPE_CONFIG, TELEGRAM_BOT_TOKEN
from scripts.scraper_amazon import AmazonScraper
from scripts.scraper_playwright_runner import run_growth_batch
from scripts.send_telegram import enviar_oferta, close_session
from scripts.commands import poll_updates, get_all_products, load_custom

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("bot-ofertas")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SEEN_FILE = os.path.join(DATA_DIR, "seen_products.json")

MAX_PER_SCRAPER = SCRAPE_CONFIG["max_por_scraper"]
MAX_PER_PRODUTO = SCRAPE_CONFIG["max_por_produto"]
SEEN_TTL_DIAS = SCRAPE_CONFIG["seen_dias_ttl"]
SCRAPE_INTERVAL = 3600

_executor = ThreadPoolExecutor(max_workers=2)


def load_seen() -> dict:
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                data = json.load(f)
                if data:
                    return data
        except (json.JSONDecodeError, IOError) as e:
            log.warning("Arquivo seen_products.json corrompido: %s", e)
    return {}


def save_seen(seen: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def prune_seen(seen: dict) -> dict:
    cutoff = (datetime.now() - timedelta(days=SEEN_TTL_DIAS)).isoformat()
    antes = len(seen)
    seen = {k: v for k, v in seen.items()
            if isinstance(v, dict) and v.get("last_seen", "") >= cutoff}
    removidos = antes - len(seen)
    if removidos > 0:
        log.info("Pruning: removidas %d entradas antigas de %d", removidos, antes)
    return seen


def normalizar_url(url: str) -> str:
    parsed = urlparse(url)
    clean = f"{parsed.netloc}{parsed.path}".rstrip("/")
    return clean.lower()


def normalizar_nome(nome: str) -> str:
    n = nome.lower().strip()
    n = re.sub(r'[^a-z0-9\s]', '', n)
    n = re.sub(r'\s+', ' ', n)
    return n


def gerar_id(produto: dict) -> str:
    url = produto.get("url", "")
    loja = produto.get("loja", "").lower()
    if url:
        key = normalizar_url(url)
    else:
        key = f"{loja}__{normalizar_nome(produto.get('nome', ''))}"
    return f"{loja}__{hashlib.md5(key.encode()).hexdigest()[:16]}"


def dedup_produtos(produtos: list) -> list:
    seen_urls = set()
    seen_names = {}
    result = []

    for prod in produtos:
        url_norm = normalizar_url(prod.get("url", ""))
        nome_norm = normalizar_nome(prod.get("nome", ""))
        loja = prod.get("loja", "").lower()

        if url_norm in seen_urls:
            continue

        name_key = f"{loja}__{nome_norm}"
        if name_key in seen_names:
            continue

        seen_urls.add(url_norm)
        seen_names[name_key] = True
        result.append(prod)

    return result


def check_and_mark(prod, seen):
    pid = gerar_id(prod)
    preco_atual = prod["preco"]

    if pid not in seen:
        prod["tipo"] = "nova"
        seen[pid] = {
            "last_price": preco_atual,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        return "nova"

    entry = seen[pid]
    preco_anterior = entry["last_price"] if isinstance(entry, dict) else preco_atual

    if preco_atual < preco_anterior:
        prod["tipo"] = "queda"
        seen[pid]["last_price"] = preco_atual
        seen[pid]["last_seen"] = datetime.now().isoformat()
        return "queda"

    seen[pid]["last_seen"] = datetime.now().isoformat()
    return None


def _scrape_all() -> dict:
    """Executa todos os scrapers e retorna resultados agrupados por termo.

    Returns:
        Dicionário com termos como chaves e listas de produtos como valores
    """
    all_prods = get_all_products(PRODUTOS_MONITORADOS)

    all_terms = []
    growth_terms = []
    term_to_preco_max = {}
    for p in all_prods:
        termo = p["palavras_chave"][0]
        all_terms.append(termo)
        term_to_preco_max[termo] = p["preco_max"]
        if "Growth" in p.get("nome", ""):
            growth_terms.append(termo)

    unique_terms = list(dict.fromkeys(all_terms))

    # Scraping via Amazon (HTTP + cloudscraper)
    amz_scraper = AmazonScraper()
    amz_results = {}
    for termo in unique_terms:
        amz_results[termo] = []
        try:
            pm = term_to_preco_max.get(termo, 999999)
            amz_results[termo].extend(amz_scraper.buscar(termo, pm)[:MAX_PER_SCRAPER])
        except Exception as e:
            log.warning("Amazon falhou para '%s': %s", termo, e)

    # Scraping via Growth (Playwright batch)
    pw_results = {}
    if growth_terms:
        try:
            growth_preco_max = max(term_to_preco_max.get(t, 999999) for t in growth_terms)
            pw_results = run_growth_batch(growth_terms, growth_preco_max, MAX_PER_SCRAPER)
        except Exception as e:
            log.warning("Growth batch falhou: %s", e)

    # Combina resultados
    combined = {}
    for termo in unique_terms:
        combined[termo] = amz_results.get(termo, []) + pw_results.get(termo, [])

    return combined


async def executar_scrapers():
    log.info("Iniciando monitoramento...")

    seen = load_seen()
    seen = prune_seen(seen)
    novos = 0
    quedas = 0
    loop = asyncio.get_running_loop()

    try:
        log.info("  Executando scrapers (Amazon + Growth)...")
        all_results = await loop.run_in_executor(_executor, _scrape_all)

        all_prods = get_all_products(PRODUTOS_MONITORADOS)
        for produto_alvo in all_prods:
            termo = produto_alvo["palavras_chave"][0]

            log.info("  %s (%s)", produto_alvo.get("nome", termo), termo)

            produtos_brutos = all_results.get(termo, [])
            produtos = dedup_produtos(produtos_brutos)

            for prod in produtos[:MAX_PER_PRODUTO]:
                tipo = check_and_mark(prod, seen)
                if tipo:
                    await asyncio.sleep(2)
                    try:
                        await enviar_oferta(prod)
                        save_seen(seen)
                    except Exception as e:
                        log.error("  Erro ao enviar: %s", e)
                    if tipo == "nova":
                        novos += 1
                    elif tipo == "queda":
                        quedas += 1
    finally:
        await close_session()

    save_seen(seen)
    log.info("Finalizado. %d novas + %d quedas de preço.", novos, quedas)
    return novos + quedas


async def scraper_loop():
    while True:
        try:
            await executar_scrapers()
        except Exception as e:
            log.error("Erro no scraper: %s", e)
        log.info("Próximo scrape em %d segundos...", SCRAPE_INTERVAL)
        await asyncio.sleep(SCRAPE_INTERVAL)


async def main():
    load_custom()
    log.info("Bot iniciando...")

    tasks = [
        asyncio.create_task(poll_updates(TELEGRAM_BOT_TOKEN)),
        asyncio.create_task(scraper_loop()),
    ]

    log.info("Escutando comandos + scrape a cada hora. Ctrl+C para parar.")
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        for t in tasks:
            t.cancel()
        await close_session()


if __name__ == "__main__":
    if "--once" in sys.argv:
        asyncio.run(executar_scrapers())
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            log.info("Bot encerrado.")
