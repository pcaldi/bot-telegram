import aiohttp
import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TELEGRAM_BOT_TOKEN, CANAL_ID

log = logging.getLogger("bot-ofertas")

MAX_RETRIES = 3
RETRY_DELAY = 1

LOJA_EMOJI = {
    "Amazon": "🟡",
    "Mercado Livre": "🟠",
    "Shopee": "🟠",
    "Netshoes": "🔵",
    "Centauro": "🟢",
    "Decathlon": "🔵",
    "Growth": "💪",
}

LOJA_DOMINIO = {
    "Amazon": "amazon.com.br",
    "Mercado Livre": "mercadolivre.com.br",
    "Shopee": "shopee.com.br",
    "Netshoes": "netshoes.com.br",
    "Centauro": "centauro.com.br",
    "Decathlon": "decathlon.com.br",
    "Growth": "gsuplementos.com.br",
}

_session = None


def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


async def _send_with_retry(url: str, payload: dict, timeout: int = 10, use_json: bool = True) -> bool:
    for attempt in range(MAX_RETRIES):
        try:
            session = _get_session()
            kwargs = {"json": payload} if use_json else {"data": payload}
            async with session.post(url, timeout=aiohttp.ClientTimeout(total=timeout), **kwargs) as resp:
                if resp.status == 200:
                    return True
                if resp.status == 429:
                    retry_after = 5
                    try:
                        data = await resp.json()
                        retry_after = data.get("parameters", {}).get("retry_after", 5)
                    except Exception:
                        pass
                    log.warning("Rate limit Telegram, aguardando %ds", retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                error_body = await resp.text()
                log.warning("Erro Telegram %d: %s", resp.status, error_body[:200])
                if resp.status >= 500 and attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return False
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.warning("Tentativa %d/%d falhou: %s", attempt + 1, MAX_RETRIES, e)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    return False


async def enviar_mensagem(texto: str, chat_id: int = CANAL_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    return await _send_with_retry(url, payload, timeout=10, use_json=True)


async def enviar_foto(url_foto: str, caption: str, chat_id: int = CANAL_ID):
    url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": url_foto,
        "caption": caption,
        "parse_mode": "HTML"
    }
    ok = await _send_with_retry(url_api, payload, timeout=15, use_json=False)
    if not ok:
        return await enviar_mensagem(caption, chat_id)
    return True


def formatar_preco(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def extrair_marca(nome: str) -> str:
    marcas = {
        "nike": "Nike", "adidas": "Adidas", "puma": "Puma",
        "mizuno": "Mizuno", "olympikus": "Olympikus", "asics": "Asics",
        "new balance": "New Balance", "reebok": "Reebok",
        "jbl": "JBL", "soundcore": "Soundcore", "anker": "Anker",
        "growth": "Growth", "integralmedica": "Integralmedica",
    }
    nome_lower = nome.lower()
    for key, val in marcas.items():
        if key in nome_lower:
            return val
    return nome.split()[0] if nome else "Produto"


def extrair_modelo(nome: str) -> str:
    marca = extrair_marca(nome).lower()
    resto = nome.lower().replace(marca, "").strip()
    palavras = resto.split()[:4]
    return " ".join(palavras).title() if palavras else nome[:30]


def formatar_oferta(produto: dict) -> str:
    nome = produto.get("nome", "Produto")
    preco = produto.get("preco", 0)
    preco_antigo = produto.get("preco_antigo")
    loja = produto.get("loja", "Loja")
    url = produto.get("url", "#")
    tipo = produto.get("tipo", "nova")

    marca = extrair_marca(nome)
    emoji_loja = LOJA_EMOJI.get(loja, "🏪")
    dominio = LOJA_DOMINIO.get(loja, "")

    if tipo == "queda":
        header = "⚡ <b>QUEDA DE PREÇO!</b>"
    else:
        header = "🔥 <b>NOVA OFERTA!</b>"

    linhas = [
        header,
        "",
        f"📦 <b>{nome[:80]}</b>",
        "",
    ]

    if preco_antigo and preco_antigo > preco:
        desconto = int((1 - preco / preco_antigo) * 100)
        linhas.append(f"❌ De {formatar_preco(preco_antigo)}")
        linhas.append(f"✅ Por <b>{formatar_preco(preco)}</b>  <b>-{desconto}%</b>")
    else:
        linhas.append(f"💰 <b>{formatar_preco(preco)}</b>")

    linhas.extend([
        "",
        f"{emoji_loja} <b>{loja}</b>",
        f"🔗 <a href='{url}'>Comprar agora</a>",
    ])

    return "\n".join(linhas)


async def enviar_oferta(produto: dict):
    texto = formatar_oferta(produto)
    imagem = produto.get("imagem", "")
    if imagem:
        return await enviar_foto(imagem, texto)
    return await enviar_mensagem(texto)
