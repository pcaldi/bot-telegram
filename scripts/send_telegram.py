import aiohttp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TELEGRAM_BOT_TOKEN, CANAL_ID

LOJA_EMOJI = {
    "Amazon": "🟡",
    "Mercado Livre": "🟠",
    "Shopee": "🟠",
    "Netshoes": "🔵",
    "Centauro": "🟢",
    "Decathlon": "🔵",
}

LOJA_COR = {
    "Amazon": "amazon.com.br",
    "Mercado Livre": "mercadolivre.com.br",
    "Shopee": "shopee.com.br",
    "Netshoes": "netshoes.com.br",
    "Centauro": "centauro.com.br",
    "Decathlon": "decathlon.com.br",
}


async def enviar_mensagem(texto: str, chat_id: int = CANAL_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                print(f"Erro ao enviar mensagem: {resp.status} - {error_body[:200]}")
            return resp.status == 200


async def enviar_foto(url_foto: str, caption: str, chat_id: int = CANAL_ID):
    url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": url_foto,
        "caption": caption,
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url_api, data=payload) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                print(f"Erro ao enviar foto: {resp.status} - {error_body[:200]}")
                return await enviar_mensagem(caption, chat_id)
            return resp.status == 200


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
    preco_alvo = produto.get("preco_alvo")

    marca = extrair_marca(nome)
    modelo = extrair_modelo(nome)
    emoji_loja = LOJA_EMOJI.get(loja, "🏪")
    dominio = LOJA_COR.get(loja, "")

    header = "🔥 <b>OFERTA ENCONTRADA!</b>" if tipo == "nova" else "📉 <b>PREÇO CAIU!</b> ⚡"

    texto_preco = ""
    if preco_antigo and preco > 0:
        pct = (1 - preco / preco_antigo) * 100
        texto_preco = f"👉 de {formatar_preco(preco_antigo)} \n✅ por {formatar_preco(preco)}*"
    else:
        texto_preco = f"✅por {formatar_preco(preco)}"

    linha_abaixo = ""
    if preco_alvo and preco <= preco_alvo:
        linha_abaixo = "🎯 <b>ABAIXO DO PREÇO ALVO!</b>"

    linhas = [
        header,
        "",
        f" 🔥<b>{marca}</b>",
        f"📌 <b>{modelo}</b>",
        "",
        f"💰 {texto_preco}",
    ]

    linhas.extend([
        "",
        f"{emoji_loja} Loja: {loja}",
        f"🔗 <a href='{url}'>{dominio}</a>",
    ])

    if linha_abaixo:
        linhas.append("")
        linhas.append(linha_abaixo)

    return "\n".join(linhas)


async def enviar_oferta(produto: dict):
    texto = formatar_oferta(produto)
    imagem = produto.get("imagem", "")
    if imagem:
        return await enviar_foto(imagem, texto)
    return await enviar_mensagem(texto)
