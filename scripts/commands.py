import asyncio
import json
import logging
import os
import sys

import aiohttp

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.database import Database
from config import ADMIN_USER_IDS

log = logging.getLogger("bot-ofertas")

KNOWN_STORES = {"amazon", "growth", "procorrer", "decathlon", "mercado livre"}


def _is_admin(user_id: int) -> bool:
    """Verifica se o usuário é admin. Se ADMIN_USER_IDS vazio, todos são admin."""
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS

CATEGORY_COMMANDS = {
    "/corrida": {
        "termos": [
            "tênis corrida",
            "shorts corrida",
            "relógio gps corrida",
            "camiseta corrida",
            "meia corrida",
        ],
        "lojas": ["Amazon", "Procorrer", "Decathlon", "mercado livre"],
    },
    "/suplementos": {
        "termos": [
            "whey protein",
            "creatina",
            "bcaa",
            "glutamina",
            "vitamina d",
            "vitamina c",
            "multivitamínico",
        ],
        "lojas": ["Amazon", "Growth", "mercado livre"],
    },
    "/eletronicos": {
        "termos": [
            "fone bluetooth",
            "monitor 24 polegadas",
            "monitor 27 polegadas",
            "tv 4k",
            "robo aspirador",
        ],
        "lojas": ["Amazon", "mercado livre"],
    },
    "/casa": {
        "termos": ["air fryer", "aspirador robot", "cafeteira", "liquidificador"],
        "lojas": ["Amazon", "mercado livre"],
    },
    "/esportes": {
        "termos": ["bola futebol", "raquete tênis", "luva boxe", "capacete bike"],
        "lojas": ["Amazon", "Decathlon", "mercado livre"],
    },
    "/tenis": {
        "termos": [
            "tênis nike",
            "tênis adidas",
            "tênis asics",
            "tênis olympikus",
            "tênis mizuno",
            "tênis puma",
            "tênis new balance",
            "tênis under armour",
            "tênis saucony",
            "tênis brooks",
            "tênis salomon",
            "tênis hoka",
            "tênis reebok",
            "tênis fila",
            "tênis vans",
            "tênis on",
        ],
        "lojas": ["Amazon", "Procorrer", "Decathlon", "mercado livre"],
    },
}

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
CUSTOM_FILE = os.path.join(DATA_DIR, "custom_products.json")

_custom_products = []
_offset = 0


def load_custom() -> list:
    global _custom_products
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE, "r") as f:
                _custom_products = json.load(f)
        except (json.JSONDecodeError, IOError):
            _custom_products = []
    return _custom_products


def save_custom():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CUSTOM_FILE, "w") as f:
        json.dump(_custom_products, f, indent=2, ensure_ascii=False)


def get_all_products(base_products: list) -> list:
    return base_products + _custom_products


async def _send_message(token: str, chat_id: int, text: str):
    from scripts.send_telegram import _get_session

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    session = _get_session()
    for attempt in range(3):
        try:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return
                if resp.status == 429:
                    data = await resp.json()
                    retry_after = data.get("parameters", {}).get("retry_after", 5)
                    log.warning("Rate limit, aguardando %ds", retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                log.warning("Erro ao enviar resposta: %d", resp.status)
                return
        except Exception as e:
            log.warning("Erro ao enviar (tentativa %d): %s", attempt + 1, e)
            if attempt < 2:
                await asyncio.sleep(2)


def _format_list(products: list) -> str:
    if not products:
        return "Nenhum produto monitorado."

    linhas = ["<b>Produtos monitorados:</b>", ""]
    for i, p in enumerate(products, 1):
        nome = p.get("nome", p.get("palavras_chave", ["?"])[0])
        preco = p.get("preco_max", "?")
        loja = " (Growth)" if "Growth" in p.get("nome", "") else ""
        linhas.append(f"  {i}. {nome}{loja} — máx R$ {preco}")
    return "\n".join(linhas)


def _handle_add(args: str) -> str:
    parts = args.strip().split()
    if not parts:
        return "Uso: /add &lt;termo&gt; [preco_max]\nEx: /add air fryer 500"

    preco_max = 500.0
    if len(parts) > 1:
        try:
            preco_max = float(parts[-1])
            parts = parts[:-1]
        except ValueError:
            pass

    termo = " ".join(parts)

    product = {
        "id": f"custom_{termo.replace(' ', '_').lower()}",
        "nome": termo.title(),
        "palavras_chave": [termo.lower()],
        "preco_max": preco_max,
        "categoria": "Custom",
    }

    for p in _custom_products:
        if p.get("palavras_chave", [None])[0] == termo.lower():
            return f"Já existe: <b>{termo}</b>"

    _custom_products.append(product)
    save_custom()
    return f"Adicionado: <b>{termo.title()}</b> (máx R$ {preco_max})"


def _handle_remove(args: str) -> str:
    parts = args.strip().split()
    if not parts:
        return "Uso: /remove &lt;id ou número&gt;\nEx: /remove 3 ou /remove custom_air_fryer"

    key = parts[0].strip()

    try:
        idx = int(key) - 1
        if 0 <= idx < len(_custom_products):
            removed = _custom_products.pop(idx)
            save_custom()
            return f"Removido: <b>{removed.get('nome', key)}</b>"
        return f"Número {key} inválido."
    except ValueError:
        for i, p in enumerate(_custom_products):
            if p.get("id") == key or p.get("palavras_chave", [None])[0] == key.lower():
                removed = _custom_products.pop(i)
                save_custom()
                return f"Removido: <b>{removed.get('nome', key)}</b>"
        return f"Não encontrado: <b>{key}</b>"


def _handle_list() -> str:
    return _format_list(_custom_products)


def _handle_status() -> str:
    """Retorna estatísticas do bot."""
    try:
        db = Database()
        stats = db.stats()
        db.close()
    except Exception as e:
        return f"Erro ao consultar status: {e}"

    lojas = ", ".join(stats["lojas"]) if stats["lojas"] else "Nenhuma"
    return (
        "📊 <b>Status do Bot</b>\n\n"
        f"🏪 Ofertas rastreadas: <b>{stats['ofertas']}</b>\n"
        f"📈 Registros de preço: <b>{stats['historico']}</b>\n"
        f"📤 Ofertas enviadas: <b>{stats['enviadas']}</b>\n"
        f"🏬 Lojas ativas: <b>{lojas}</b>\n"
        f"📦 Produtos custom: <b>{len(_custom_products)}</b>"
    )


def _get_scrapers(lojas: list = None):
    """Retorna instâncias de scrapers filtradas por loja."""
    from scripts.scraper_amazon import AmazonScraper
    from scripts.scraper_decathlon import DecathlonScraper
    from scripts.scraper_mercadolivre import MercadoLivreScraper
    from scripts.scraper_playwright_runner import run_growth_batch
    from scripts.scraper_procorrer import ProcorrerScraper

    all_scrapers = {
        "Amazon": lambda: AmazonScraper(),
        "Procorrer": lambda: ProcorrerScraper(),
        "Decathlon": lambda: DecathlonScraper(),
        "Mercado Livre": lambda: MercadoLivreScraper(),
    }

    if lojas:
        return {k: v for k, v in all_scrapers.items() if k in lojas}, run_growth_batch
    return all_scrapers, run_growth_batch


def _run_scrapers_sync(
    termos: list, lojas: list = None, max_por_scraper: int = 3
) -> list:
    """Executa scrapers de forma síncrona e retorna todos os produtos encontrados."""
    from scripts.main import dedup_produtos

    scrapers, run_growth = _get_scrapers(lojas)
    results = []

    for termo in termos:
        for nome_loja, scraper_fn in scrapers.items():
            try:
                scraper = scraper_fn()
                produtos = scraper.buscar(termo, None)[:max_por_scraper]
                results.extend(produtos)
            except Exception as e:
                log.warning("Scraper %s falhou para '%s': %s", nome_loja, termo, e)

        if lojas is None or "Growth" in lojas:
            try:
                growth_results = run_growth([termo], None, max_por_scraper)
                for termo_r, prods in growth_results.items():
                    results.extend(prods)
            except Exception as e:
                log.warning("Growth falhou para '%s': %s", termo, e)

    return dedup_produtos(results)


async def _handle_search(token: str, chat_id: int, args: str):
    """Busca produtos nos scrapers existentes."""
    if not args.strip():
        await _send_message(
            token,
            chat_id,
            "Uso: /search &lt;termo&gt; [loja]\n"
            "Lojas: amazon, growth, procorrer, decathlon, mercado livre\n"
            "Ex: /search nike air max",
        )
        return

    parts = args.strip().split()
    loja_filter = None
    if parts[-1].lower() in KNOWN_STORES:
        loja_filter = parts.pop().title()

    termo = " ".join(parts)
    if not termo:
        await _send_message(token, chat_id, "Informe um termo de busca.")
        return

    await _send_message(
        token,
        chat_id,
        f"🔍 Buscando <b>{termo}</b>"
        + (f" na <b>{loja_filter}</b>" if loja_filter else "")
        + "...",
    )

    loop = asyncio.get_running_loop()
    lojas_list = [loja_filter] if loja_filter else None
    produtos = await loop.run_in_executor(
        None, _run_scrapers_sync, [termo], lojas_list, 3
    )

    if not produtos:
        await _send_message(token, chat_id, "Nenhum resultado encontrado.")
        return

    await _send_message(
        token, chat_id, f"📦 {len(produtos)} resultado(s) encontrado(s):"
    )

    for prod in produtos[:10]:
        from scripts.send_telegram import formatar_oferta, validar_produto

        prod = validar_produto(prod)
        texto = formatar_oferta(prod)
        await _send_message(token, chat_id, texto)
        await asyncio.sleep(2)


async def _handle_category(token: str, chat_id: int, category_key: str):
    """Busca produtos de uma categoria pré-definida."""
    cat = CATEGORY_COMMANDS[category_key]
    termos = cat["termos"]
    lojas = cat["lojas"]

    await _send_message(
        token, chat_id, f"🔍 Buscando ofertas de <b>{category_key[1:]}</b>..."
    )

    loop = asyncio.get_running_loop()
    produtos = await loop.run_in_executor(None, _run_scrapers_sync, termos, lojas, 3)

    if not produtos:
        await _send_message(
            token, chat_id, "Nenhum resultado encontrado para esta categoria."
        )
        return

    await _send_message(token, chat_id, f"📦 {len(produtos)} resultado(s):")

    for prod in produtos[:10]:
        from scripts.send_telegram import formatar_oferta, validar_produto

        prod = validar_produto(prod)
        texto = formatar_oferta(prod)
        await _send_message(token, chat_id, texto)
        await asyncio.sleep(2)


async def handle_message(token: str, message: dict):
    global _offset

    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id", 0)
    text = message.get("text", "").strip()

    if not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # Comando /myid - mostra o user_id do usuário
    if command == "/myid":
        username = message.get("from", {}).get("username", "")
        nome = message.get("from", {}).get("first_name", "")
        await _send_message(token, chat_id, f"Seu user_id: <b>{user_id}</b>\nUsername: @{username}\nNome: {nome}")
        return

    # Comandos restritos a admins
    admin_commands = {"/add", "/remove"}
    if command in admin_commands and not _is_admin(user_id):
        await _send_message(token, chat_id, "Acesso negado. Somente administradores podem usar este comando.")
        return

    static_responses = {
        "/start": "Bem-vindo! Comandos:\n"
        "/add &lt;termo&gt; [preco_max] — Adicionar produto\n"
        "/remove &lt;id&gt; — Remover produto\n"
        "/list — Listar produtos custom\n"
        "/status — Ver estatísticas do bot\n"
        "/search &lt;termo&gt; [loja] — Buscar ofertas\n"
        "/corrida — Ofertas de corrida\n"
        "/suplementos — Ofertas de suplementos\n"
        "/eletronicos — Ofertas de eletrônicos\n"
        "/casa — Ofertas de casa\n"
        "/esportes — Ofertas de esportes\n"
        "/tenis — Ofertas de tênis\n"
        "/myid — Ver seu user_id\n"
        "/help — Esta ajuda",
        "/help": "Comandos:\n"
        "/add &lt;termo&gt; [preco_max] — Ex: /add air fryer 500\n"
        "/remove &lt;número ou id&gt; — Ex: /remove 3\n"
        "/list — Ver produtos adicionados\n"
        "/status — Ver estatísticas\n"
        "/search &lt;termo&gt; [loja] — Ex: /search nike air max\n"
        "  Lojas: amazon, growth, procorrer, decathlon, mercado livre\n"
        "/corrida — Tênis, shorts, relógio, camiseta, meia\n"
        "/suplementos — Whey, creatina, bcaa, vitaminas\n"
        "/eletronicos — Fones, monitores, tv, robo aspirador\n"
        "/casa — Air fryer, aspirador, cafeteira, liquidificador\n"
        "/esportes — Bola, raquete, luva, capacete\n"
        "/tenis — Nike, Adidas, Asics, Mizuno, etc\n"
        "/myid — Ver seu user_id (necessário para configurar admin)",
    }

    if command in static_responses:
        await _send_message(token, chat_id, static_responses[command])
    elif command == "/list":
        await _send_message(token, chat_id, _handle_list())
    elif command == "/status":
        await _send_message(token, chat_id, _handle_status())
    elif command == "/add":
        await _send_message(token, chat_id, _handle_add(args))
    elif command == "/remove":
        await _send_message(token, chat_id, _handle_remove(args))
    elif command == "/search":
        await _handle_search(token, chat_id, args)
    elif command in CATEGORY_COMMANDS:
        await _handle_category(token, chat_id, command)


async def poll_updates(token: str, interval: int = 5):
    global _offset
    load_custom()
    log.info("Escutando comandos Telegram...")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"offset": _offset, "timeout": interval}
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=interval + 10),
                ) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(interval)
                        continue
                    data = await resp.json()

                for update in data.get("result", []):
                    _offset = update["update_id"] + 1
                    if "message" in update:
                        await handle_message(token, update["message"])

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                log.warning("Erro ao buscar updates: %s", e)
                await asyncio.sleep(interval)
            except Exception as e:
                log.error("Erro inesperado no poll: %s", e)
                await asyncio.sleep(interval)
