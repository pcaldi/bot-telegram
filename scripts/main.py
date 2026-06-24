import json
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CATEGORIAS
from scripts.scraper_amazon import buscar_produtos as amz_buscar
from scripts.scraper_netshoes import buscar_produtos as net_buscar
from scripts.scraper_decathlon import buscar_produtos as dec_buscar
from scripts.scraper_shopee import buscar_produtos as sho_buscar
from scripts.send_telegram import enviar_oferta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SEEN_FILE = os.path.join(DATA_DIR, "seen_products.json")


def load_seen() -> dict:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def gerar_id(produto: dict) -> str:
    return f"{produto.get('loja', '')}_{produto.get('url', '')[:80]}"


async def rate_limited_send(produto: dict):
    await asyncio.sleep(2)
    try:
        ok = await enviar_oferta(produto)
        return ok
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        await asyncio.sleep(5)
        return False


async def executar_scrapers():
    print(f"[{datetime.now()}] Iniciando scrapers...")

    seen = load_seen()
    novos = 0

    termos_para_buscar = []
    for cat_key, cat_info in CATEGORIAS.items():
        for termo in cat_info["palavras_chave"][:3]:
            termos_para_buscar.append((termo, cat_info.get("max_preco")))

    for termo, max_preco in termos_para_buscar:
        print(f"  Buscando: {termo}")

        # Amazon (sync - funciona)
        try:
            produtos = amz_buscar(termo, max_preco)
            for produto in produtos[:3]:
                pid = gerar_id(produto)
                if pid not in seen:
                    await rate_limited_send(produto)
                    seen[pid] = datetime.now().isoformat()
                    novos += 1
        except Exception as e:
            print(f"  Erro Amazon: {e}")

        # Netshoes (async - funciona)
        try:
            produtos_net = await net_buscar(termo, max_preco)
            for produto in produtos_net[:3]:
                pid = gerar_id(produto)
                if pid not in seen:
                    await rate_limited_send(produto)
                    seen[pid] = datetime.now().isoformat()
                    novos += 1
        except Exception as e:
            print(f"  Erro Netshoes: {e}")

        # Decathlon (async - funciona)
        try:
            produtos_dec = await dec_buscar(termo, max_preco)
            for produto in produtos_dec[:3]:
                pid = gerar_id(produto)
                if pid not in seen:
                    await rate_limited_send(produto)
                    seen[pid] = datetime.now().isoformat()
                    novos += 1
        except Exception as e:
            print(f"  Erro Decathlon: {e}")

        # Shopee (tentativa)
        try:
            produtos_sho = sho_buscar(termo, max_preco)
            for produto in produtos_sho[:3]:
                pid = gerar_id(produto)
                if pid not in seen:
                    await rate_limited_send(produto)
                    seen[pid] = datetime.now().isoformat()
                    novos += 1
        except Exception as e:
            print(f"  Erro Shopee: {e}")

    save_seen(seen)
    print(f"[{datetime.now()}] Finalizado. {novos} ofertas novas enviadas.")
    return novos


if __name__ == "__main__":
    asyncio.run(executar_scrapers())
