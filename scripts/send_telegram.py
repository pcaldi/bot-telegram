import aiohttp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TELEGRAM_BOT_TOKEN, CANAL_ID, GRUPO_ID


async def enviar_mensagem(texto: str, chat_id: int = CANAL_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                print(f"Erro ao enviar mensagem: {resp.status}")
            return resp.status == 200


async def enviar_oferta(produto: dict):
    texto = formatar_oferta(produto)
    return await enviar_mensagem(texto)


def formatar_oferta(produto: dict) -> str:
    desconto = ""
    if produto.get("preco_antigo") and produto.get("preco"):
        pct = (1 - produto["preco"] / produto["preco_antigo"]) * 100
        desconto = f"\n📉 <b>Desconto:</b> {pct:.0f}% OFF"

    preco_antigo = ""
    if produto.get("preco_antigo"):
        preco_antigo = f"\n De <s>R$ {produto['preco_antigo']:.2f}</s>"

    loja_emoji = {
        "Mercado Livre": "🟠",
        "Amazon": "🟡",
        "Shopee": "🟠",
        "Centauro": "🟢",
        "Netshoes": "🔵",
        "Decathlon": "🔵"
    }
    emoji = loja_emoji.get(produto.get("loja", ""), "🏪")

    texto = f"""
🔥 <b>NOVA OFERTA!</b>

<b>{produto.get('nome', 'Produto')}</b>

💰 <b>Por R$ {produto.get('preco', 0):.2f}</b>{preco_antigo}{desconto}

{emoji} <b>Loja:</b> {produto.get('loja', 'N/A')}
🚚 <b>Frete:</b> {produto.get('frete', 'Não informado')}

🔗 <a href="{produto.get('url', '#')}">Ver Produto</a>
"""
    return texto.strip()
