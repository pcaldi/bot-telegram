import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CANAL_ID = int(os.getenv("CANAL_ID", "-1004330223980"))
GRUPO_ID = int(os.getenv("GRUPO_ID", "-1004358265563"))

CATEGORIAS = {
    "tenis": {
        "nome": "Tênis",
        "palavras_chave": [
            "tênis nike", "tênis adidas", "tênis puma",
            "tênis olympikus", "tênis mizuno", "tênis asics",
            "tênis new balance", "tênis reebok"
        ],
        "max_preco": 500.00
    },
    "suplementos": {
        "nome": "Suplementos",
        "palavras_chave": [
            "whey protein", "creatina", "pre treino",
            "bcaa", "protein bar", "glutamina"
        ],
        "max_preco": 200.00
    },
    "eletronicos": {
        "nome": "Eletrônicos",
        "palavras_chave": [
            "fone bluetooth", "mouse gamer", "teclado mecânico",
            "monitor", "ssd", "placa de video", "headphone",
            "capa celular", "carregador"
        ],
        "max_preco": 2000.00
    }
}
