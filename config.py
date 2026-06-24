import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN não configurado. Adicione no .env ou nos secrets do GitHub Actions.")

CANAL_ID = int(os.environ["CANAL_ID"])
GRUPO_ID = int(os.environ["GRUPO_ID"])

PRODUTOS_MONITORADOS = [
    # ==================== TÊNIS ====================
    {
        "id": "tenis_nike_air_max",
        "nome": "Tênis Nike Air Max",
        "palavras_chave": ["nike air max"],
        "preco_max": 500.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_nike_downshifter",
        "nome": "Tênis Nike Downshifter",
        "palavras_chave": ["nike downshifter"],
        "preco_max": 400.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_adidas_coreracer",
        "nome": "Tênis Adidas Coreracer",
        "palavras_chave": ["adidas coreracer"],
        "preco_max": 400.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_olympikus",
        "nome": "Tênis Olympikus",
        "palavras_chave": ["tenis olympikus"],
        "preco_max": 300.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_asics_superblast3",
        "nome": "Tênis ASICS Superblast 3",
        "palavras_chave": ["asics superblast"],
        "preco_max": 1699.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_asics_superblast2",
        "nome": "Tênis ASICS Superblast 2",
        "palavras_chave": ["asics superblast 2"],
        "preco_max": 1699.0,
        "categoria": "Tênis"
    },
    {
        "id": "tenis_adidas_adizero",
        "nome": "Tênis Adidas Adizero",
        "palavras_chave": ["adidas adizero"],
        "preco_max": 1079.0,
        "categoria": "Tênis"
    },

    # ==================== SUPLEMENTOS ====================
    {
        "id": "whey_protein",
        "nome": "Whey Protein",
        "palavras_chave": ["whey protein"],
        "preco_max": 200.0,
        "categoria": "Suplementos"
    },
    {
        "id": "creatina",
        "nome": "Creatina Monohidratada",
        "palavras_chave": ["creatina"],
        "preco_max": 120.0,
        "categoria": "Suplementos"
    },
    {
        "id": "whey_max",
        "nome": "Whey Max",
        "palavras_chave": ["whey max"],
        "preco_max": 150.0,
        "categoria": "Suplementos"
    },

    # ==================== ELETRÔNICOS ====================
    {
        "id": "fone_jbl",
        "nome": "Fone JBL Bluetooth",
        "palavras_chave": ["fone jbl"],
        "preco_max": 300.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "fone_soundcore",
        "nome": "Fone Soundcore Anker",
        "palavras_chave": ["fone anker"],
        "preco_max": 300.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "mouse_gamer",
        "nome": "Mouse Gamer",
        "palavras_chave": ["mouse gamer"],
        "preco_max": 200.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "ssd",
        "nome": "SSD 1TB",
        "palavras_chave": ["ssd 1tb"],
        "preco_max": 500.0,
        "categoria": "Eletrônicos"
    },
    {
        "id": "monitor",
        "nome": "Monitor 24+",
        "palavras_chave": ["monitor 24"],
        "preco_max": 1200.0,
        "categoria": "Eletrônicos"
    },

    # ==================== GROWTH (URLs diretas) ====================
    {
        "id": "whey_growth_concentrado_1kg",
        "nome": "Whey Protein Concentrado 1kg (Growth)",
        "palavras_chave": ["whey protein concentrado 1kg"],
        "preco_max": 200.0,
        "categoria": "Suplementos"
    },
    {
        "id": "creatina_monohidratada_250g",
        "nome": "Creatina Monohidratada 250g (Growth)",
        "palavras_chave": ["creatina monohidratada 250g"],
        "preco_max": 80.0,
        "categoria": "Suplementos"
    },
    {
        "id": "kit_whey_creatina_growth",
        "nome": "Kit Whey + Creatina (Growth)",
        "palavras_chave": ["kit whey creatina"],
        "preco_max": 250.0,
        "categoria": "Suplementos"
    },
]

SCRAPE_CONFIG = {
    "max_por_scraper": 2,
    "max_por_produto": 4,
    "seen_dias_ttl": 90,
}
