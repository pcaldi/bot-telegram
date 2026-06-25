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
from scripts.core.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("bot-ofertas")

MAX_PER_SCRAPER = SCRAPE_CONFIG["max_por_scraper"]
MAX_PER_PRODUTO = SCRAPE_CONFIG["max_por_produto"]
SEEN_TTL_DIAS = SCRAPE_CONFIG["seen_dias_ttl"]
SCRAPE_INTERVAL = 3600

_executor = ThreadPoolExecutor(max_workers=2)
_db: Optional[Database] = None


def get_db() -> Database:
    """Retorna instância singleton do banco de dados."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def close_db():
    """Fecha a conexão com o banco."""
    global _db
    if _db:
        _db.close()
        _db = None


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


def check_and_mark(prod: dict, db: Database) -> Optional[str]:
    """Verifica se produto é novo ou teve queda de preço.

    Args:
        prod: Dict do produto.
        db: Instância do banco de dados.

    Returns:
        "nova", "queda", ou None.
    """
    pid = gerar_id(prod)
    preco_atual = prod["preco"]

    existing = db.buscar_oferta(pid)

    if existing is None:
        prod["tipo"] = "nova"
        db.salvar_oferta({
            "produto_id": pid,
            "nome": prod.get("nome", ""),
            "preco_atual": preco_atual,
            "loja": prod.get("loja", ""),
            "url": prod.get("url"),
            "imagem": prod.get("imagem"),
            "categoria": prod.get("categoria"),
        })
        db.salvar_historico(pid, preco_atual)
        return "nova"

    preco_anterior = existing.get("preco_atual", preco_atual)

    if preco_atual < preco_anterior:
        prod["tipo"] = "queda"
        db.atualizar_preco(pid, preco_atual)
        return "queda"

    db.conn.execute(
        "UPDATE ofertas SET ultima_vista=? WHERE produto_id=?",
        (datetime.now().isoformat(), pid),
    )
    db.conn.commit()
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

    db = get_db()
    db.cleanup_historico(SEEN_TTL_DIAS)
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
                tipo = check_and_mark(prod, db)
                if tipo:
                    await asyncio.sleep(2)
                    try:
                        await enviar_oferta(prod)
                        pid = gerar_id(prod)
                        db.registrar_envio(pid, tipo, prod["preco"])
                    except Exception as e:
                        log.error("  Erro ao enviar: %s", e)
                    if tipo == "nova":
                        novos += 1
                    elif tipo == "queda":
                        quedas += 1
    finally:
        await close_session()

    stats = db.stats()
    log.info(
        "Finalizado. %d novas + %d quedas. Banco: %d ofertas, %d históricos.",
        novos, quedas, stats["ofertas"], stats["historico"],
    )
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
        close_db()


if __name__ == "__main__":
    if "--once" in sys.argv:
        asyncio.run(executar_scrapers())
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            log.info("Bot encerrado.")
