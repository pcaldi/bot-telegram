import json
import os
import logging
import aiohttp
import asyncio

from scripts.core.database import Database

log = logging.getLogger("bot-ofertas")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
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
        "disable_web_page_preview": True
    }
    session = _get_session()
    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            log.warning("Erro ao enviar resposta: %d", resp.status)


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
        "categoria": "Custom"
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


async def handle_message(token: str, message: dict):
    global _offset

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    responses = {
        "/start": "Bem-vindo! Comandos:\n"
                  "/add &lt;termo&gt; [preco_max] — Adicionar produto\n"
                  "/remove &lt;id&gt; — Remover produto\n"
                  "/list — Listar produtos custom\n"
                  "/status — Ver estatísticas do bot\n"
                  "/help — Esta ajuda",
        "/help": "Comandos:\n"
                 "/add &lt;termo&gt; [preco_max] — Ex: /add air fryer 500\n"
                 "/remove &lt;número ou id&gt; — Ex: /remove 3\n"
                 "/list — Ver produtos adicionados\n"
                 "/status — Ver estatísticas",
        "/list": _handle_list(),
        "/status": _handle_status(),
    }

    if command in responses:
        await _send_message(token, chat_id, responses[command])
    elif command == "/add":
        await _send_message(token, chat_id, _handle_add(args))
    elif command == "/remove":
        await _send_message(token, chat_id, _handle_remove(args))


async def poll_updates(token: str, interval: int = 5):
    global _offset
    load_custom()
    log.info("Escutando comandos Telegram...")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"offset": _offset, "timeout": interval}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=interval + 10)) as resp:
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
