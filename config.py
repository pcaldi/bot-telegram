import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CANAL_ID = int(os.getenv("CANAL_ID", "-1004330223980"))
GRUPO_ID = int(os.getenv("GRUPO_ID", "-1004358265563"))

PRODUTOS_MONITORADOS = [
    {
        "id": "tenis_nike_air_max",
        "nome": "Tênis Nike Air Max",
        "palavras_chave": ["tenis nike air max", "nike air max sc"],
        "preco_max": 500.0,
        "preco_alvo": 300.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_nike_downshifter",
        "nome": "Tênis Nike Downshifter",
        "palavras_chave": ["tenis nike downshifter"],
        "preco_max": 400.0,
        "preco_alvo": 250.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_adidas_coreracer",
        "nome": "Tênis Adidas Coreracer",
        "palavras_chave": ["tenis adidas coreracer", "adidas coreracer"],
        "preco_max": 400.0,
        "preco_alvo": 250.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_olympikus",
        "nome": "Tênis Olympikus (geral)",
        "palavras_chave": ["tenis olympikus"],
        "preco_max": 300.0,
        "preco_alvo": 180.0,
        "categoria": "Tênis"
    },
    {
        "id": "whey_growth",
        "nome": "Whey Protein Growth",
        "palavras_chave": ["whey protein growth", "growth whey"],
        "preco_max": 150.0,
        "preco_alvo": 100.0,
        "categoria": "Suplementos"
    },
    {
        "id": "whey_integralmedica",
        "nome": "Whey Protein Integralmedica",
        "palavras_chave": ["whey integralmedica", "whey protein integralmedica"],
        "preco_max": 150.0,
        "preco_alvo": 90.0,
        "categoria": "Suplementos"
    },
    {
        "id": "creatina",
        "nome": "Creatina (Growth/Integralmedica)",
        "palavras_chave": ["creatina growth", "creatin monohidratada"],
        "preco_max": 120.0,
        "preco_alvo": 70.0,
        "categoria": "Suplementos"
    },
    {
        "id": "fone_jbl",
        "nome": "Fone JBL Bluetooth",
        "palavras_chave": ["fone jbl bluetooth", "jbl tune"],
        "preco_max": 300.0,
        "preco_alvo": 150.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "fone_soundcore",
        "nome": "Fone Soundcore Anker",
        "palavras_chave": ["soundcore anker", "fone anker"],
        "preco_max": 300.0,
        "preco_alvo": 150.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "mouse_gamer",
        "nome": "Mouse Gamer",
        "palavras_chave": ["mouse gamer sem fio", "mouse redragon"],
        "preco_max": 200.0,
        "preco_alvo": 100.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "ssd",
        "nome": "SSD 480GB+",
        "palavras_chave": ["ssd 480gb", "ssd 1tb"],
        "preco_max": 500.0,
        "preco_alvo": 250.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "monitor",
        "nome": "Monitor 24+",
        "palavras_chave": ["monitor 24 polegadas", "monitor full hd"],
        "preco_max": 1200.0,
        "preco_alvo": 700.0,
        "categoria": "Eletrônicos"
    }
]
