import json
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PRODUTOS_MONITORADOS
from scripts.scraper_amazon import buscar_produtos as amz_buscar
from scripts.scraper_netshoes import buscar_produtos as net_buscar
from scripts.scraper_decathlon import buscar_produtos as dec_buscar
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
    nome_curto = produto.get("nome", "")[:60].strip().lower()
    loja = produto.get("loja", "").lower()
    return f"{loja}__{nome_curto}"


async def rate_limited_send(produto: dict):
    await asyncio.sleep(2)
    try:
        return await enviar_oferta(produto)
    except Exception as e:
        print(f"  Erro ao enviar: {e}")
        await asyncio.sleep(5)
        return False


def check_and_mark(prod, seen, preco_alvo):
    pid = gerar_id(prod)
    preco_atual = prod["preco"]

    if pid not in seen:
        prod["tipo"] = "nova"
        prod["preco_alvo"] = preco_alvo
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
        prod["preco_alvo"] = preco_alvo
        seen[pid]["last_price"] = preco_atual
        seen[pid]["last_seen"] = datetime.now().isoformat()
        return "queda"

    return None


async def executar_scrapers():
    print(f"[{datetime.now()}] Iniciando monitoramento...")

    seen = load_seen()
    novos = 0
    quedas = 0

    for produto_alvo in PRODUTOS_MONITORADOS:
        termo = produto_alvo["palavras_chave"][0]
        preco_max = produto_alvo["preco_max"]
        preco_alvo = produto_alvo["preco_alvo"]

        print(f"  {produto_alvo['nome']} ({termo})")

        # Amazon (sync - rápido)
        try:
            for prod in amz_buscar(termo, preco_max)[:3]:
                tipo = check_and_mark(prod, seen, preco_alvo)
                if tipo:
                    await rate_limited_send(prod)
                    novos += 1 if tipo == "nova" else 0
                    quedas += 1 if tipo == "queda" else 0
        except Exception as e:
            print(f"    Erro Amazon: {e}")

        # Netshoes (async - Playwright)
        try:
            for prod in (await net_buscar(termo, preco_max))[:3]:
                tipo = check_and_mark(prod, seen, preco_alvo)
                if tipo:
                    await rate_limited_send(prod)
                    novos += 1 if tipo == "nova" else 0
                    quedas += 1 if tipo == "queda" else 0
        except Exception as e:
            print(f"    Erro Netshoes: {e}")

        # Decathlon (async - Playwright)
        try:
            for prod in (await dec_buscar(termo, preco_max))[:3]:
                tipo = check_and_mark(prod, seen, preco_alvo)
                if tipo:
                    await rate_limited_send(prod)
                    novos += 1 if tipo == "nova" else 0
                    quedas += 1 if tipo == "queda" else 0
        except Exception as e:
            print(f"    Erro Decathlon: {e}")

    save_seen(seen)
    print(f"[{datetime.now()}] Finalizado. {novos} novas + {quedas} quedas de preço.")
    return novos + quedas


if __name__ == "__main__":
    asyncio.run(executar_scrapers())
