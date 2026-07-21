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

from config import PRODUTOS_MONITORADOS, SCRAPE_CONFIG, TELEGRAM_BOT_TOKEN, SCRAPERS_DISABLED, LOJAS_POR_PRODUTO
from scripts.scraper_amazon import AmazonScraper
from scripts.scraper_procorrer import ProcorrerScraper
from scripts.scraper_decathlon import DecathlonScraper
from scripts.scraper_mercadolivre import MercadoLivreScraper
from scripts.scraper_playwright_runner import run_growth_batch
from scripts.send_telegram import enviar_oferta, close_session, validar_produto
from scripts.commands import poll_updates, get_all_products, load_custom
from scripts.browser_utils import BrowserManager
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

_executor = ThreadPoolExecutor(max_workers=5)
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
            "preco_pix": prod.get("preco_pix"),
            "parcelamento": prod.get("parcelamento"),
            "tamanhos": prod.get("tamanhos"),
        })
        db.salvar_historico(pid, preco_atual)
        return "nova"

    preco_anterior = existing.get("preco_atual", preco_atual)

    if preco_atual < preco_anterior:
        prod["tipo"] = "queda"
        db.atualizar_preco(pid, preco_atual)
        return "queda"

    db.atualizar_vista(pid)
    return None


def _scrape_amazon(unique_terms, term_to_preco_max) -> dict:
    """Scraping Amazon (HTTP + cloudscraper) via subprocess."""
    from scripts.scraper_playwright_runner import run_amazon
    return run_amazon(unique_terms, term_to_preco_max, MAX_PER_SCRAPER)


def _scrape_procorrer(unique_terms, term_to_preco_max) -> dict:
    """Scraping Procorrer (Playwright) via subprocess."""
    from scripts.scraper_playwright_runner import run_playwright_scraper
    return run_playwright_scraper("procorrer", unique_terms, term_to_preco_max, MAX_PER_SCRAPER)


def _scrape_decathlon(unique_terms, term_to_preco_max) -> dict:
    """Scraping Decathlon (Playwright) via subprocess."""
    from scripts.scraper_playwright_runner import run_playwright_scraper
    return run_playwright_scraper("decathlon", unique_terms, term_to_preco_max, MAX_PER_SCRAPER)


def _scrape_ml(unique_terms, term_to_preco_max) -> dict:
    """Scraping Mercado Livre (Playwright) via subprocess."""
    from scripts.scraper_playwright_runner import run_playwright_scraper
    return run_playwright_scraper("ml", unique_terms, term_to_preco_max, MAX_PER_SCRAPER)


def _scrape_growth(growth_terms, term_to_preco_max) -> dict:
    """Scraping Growth (Playwright) via subprocess."""
    from scripts.scraper_playwright_runner import run_growth_batch
    if not growth_terms:
        return {}
    try:
        growth_preco_max = max(term_to_preco_max.get(t, 999999) for t in growth_terms)
        return run_growth_batch(growth_terms, growth_preco_max, MAX_PER_SCRAPER)
    except Exception as e:
        log.warning("Growth batch falhou: %s", e)
        return {}


def _scrape_all() -> dict:
    """Executa todos os scrapers em paralelo (subprocessos) e retorna resultados agrupados por termo.

    Returns:
        Dicionário com termos como chaves e listas de produtos como valores
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

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
    log.info("  Termos únicos: %d - %s", len(unique_terms), unique_terms[:5])

    # Executa scrapers em paralelo (cada um em subprocess separado)
    enabled = [s for s in ["Amazon", "Procorrer", "Decathlon", "ML", "Growth"] if s not in SCRAPERS_DISABLED]
    log.info("  Executando %d scrapers em paralelo: %s", len(enabled), ", ".join(enabled))
    with ThreadPoolExecutor(max_workers=len(enabled)) as executor:
        futures = {}
        if "Amazon" in enabled:
            futures[executor.submit(_scrape_amazon, unique_terms, term_to_preco_max)] = "Amazon"
        if "Procorrer" in enabled:
            futures[executor.submit(_scrape_procorrer, unique_terms, term_to_preco_max)] = "Procorrer"
        if "Decathlon" in enabled:
            futures[executor.submit(_scrape_decathlon, unique_terms, term_to_preco_max)] = "Decathlon"
        if "ML" in enabled:
            futures[executor.submit(_scrape_ml, unique_terms, term_to_preco_max)] = "ML"
        if "Growth" in enabled:
            futures[executor.submit(_scrape_growth, growth_terms, term_to_preco_max)] = "Growth"

        amz_results = {}
        pc_results = {}
        dc_results = {}
        ml_results = {}
        pw_results = {}

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result(timeout=200)
                if name == "Amazon":
                    amz_results = result
                elif name == "Procorrer":
                    pc_results = result
                elif name == "Decathlon":
                    dc_results = result
                elif name == "ML":
                    ml_results = result
                elif name == "Growth":
                    pw_results = result
                log.info("  %s concluído: %d produtos", name, sum(len(v) for v in result.values()))
            except Exception as e:
                log.warning("  %s falhou: %s", name, e)

    # Combina resultados
    combined = {}
    ml_ofertas = ml_results.get("__ofertas__", [])
    for termo in unique_terms:
        combined[termo] = (
            amz_results.get(termo, [])
            + pc_results.get(termo, [])
            + dc_results.get(termo, [])
            + ml_results.get(termo, [])
            + pw_results.get(termo, [])
        )
        # Adiciona ofertas gerais do ML (descontos maiores)
        if ml_ofertas:
            combined[termo].extend(ml_ofertas)

    # Filtra por lojas permitidas por produto
    termo_to_produto_id = {}
    for p in all_prods:
        termo_to_produto_id[p["palavras_chave"][0]] = p["id"]

    for termo in combined:
        produto_id = termo_to_produto_id.get(termo)
        lojas_permitidas = LOJAS_POR_PRODUTO.get(produto_id)
        if lojas_permitidas:
            combined[termo] = [
                p for p in combined[termo]
                if p.get("loja") in lojas_permitidas
            ]

    # Log resumo
    total = sum(len(v) for v in combined.values())
    log.info("  Scrapers: Amazon=%d, Procorrer=%d, Decathlon=%d, ML=%d, Growth=%d",
             sum(len(v) for v in amz_results.values()),
             sum(len(v) for v in pc_results.values()),
             sum(len(v) for v in dc_results.values()),
             sum(len(v) for v in ml_results.values()),
             sum(len(v) for v in pw_results.values()))
    log.info("  Total de produtos encontrados: %d", total)

    return combined


async def executar_scrapers():
    log.info("Iniciando monitoramento...")

    db = get_db()
    db.cleanup_historico(SEEN_TTL_DIAS)
    novos = 0
    quedas = 0
    loop = asyncio.get_running_loop()

    try:
        log.info("  Executando scrapers (Amazon + Procorrer + Decathlon + Mercado Livre + Growth)...")
        all_results = await loop.run_in_executor(_executor, _scrape_all)

        all_prods = get_all_products(PRODUTOS_MONITORADOS)
        for produto_alvo in all_prods:
            termo = produto_alvo["palavras_chave"][0]

            log.info("  %s (%s)", produto_alvo.get("nome", termo), termo)

            produtos_brutos = all_results.get(termo, [])
            produtos = dedup_produtos(produtos_brutos)

            for prod in produtos[:MAX_PER_PRODUTO]:
                prod = validar_produto(prod)

                url_valida = prod.get("url_valido", True) and prod.get("url", "")
                tem_imagem = bool(prod.get("imagem", ""))
                if not url_valida and not tem_imagem:
                    log.info("Pulando produto sem link/imagem: %s", prod.get("nome", "")[:50])
                    continue

                tipo = check_and_mark(prod, db)
                if tipo:
                    pid = gerar_id(prod)
                    menor_preco = db.buscar_menor_preco(pid)
                    if menor_preco is not None and prod["preco"] <= menor_preco:
                        prod["menor_preco"] = menor_preco
                    await asyncio.sleep(2)
                    try:
                        await enviar_oferta(prod)
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
        BrowserManager.get().stop()
        close_db()


if __name__ == "__main__":
    if "--once" in sys.argv:
        asyncio.run(executar_scrapers())
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            log.info("Bot encerrado.")
