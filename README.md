# Bot Telegram Ofertas

Bot que monitora ofertas em lojas brasileiras e posta automaticamente em um canal do Telegram.

## Lojas suportadas

- **Amazon Brasil** (HTTP + cloudscraper)
- **Procorrer** (Playwright)
- **Decathlon** (Playwright)
- **Mercado Livre** (HTTP + cloudscraper)
- **Growth Suplementos** (Playwright)

## Comandos do bot

| Comando | Descrição |
|---------|-----------|
| `/start` | Mostra todos os comandos |
| `/help` | Ajuda detalhada |
| `/search <termo> [loja]` | Busca ofertas em tempo real |
| `/corrida` | Ofertas de corrida |
| `/suplementos` | Ofertas de suplementos |
| `/eletronicos` | Ofertas de eletrônicos |
| `/casa` | Ofertas de casa |
| `/esportes` | Ofertas de esportes |
| `/tenis` | Ofertas de tênis |
| `/add <termo> [preco_max]` | Adiciona produto custom (admin) |
| `/remove <id>` | Remove produto custom (admin) |
| `/list` | Lista produtos custom |
| `/status` | Estatísticas do bot |
| `/myid` | Mostra seu user_id |

## Setup

1. Clone o repositório:
```bash
git clone <url>
cd bot-telegram-ofertas
```

2. Crie o `.env` a partir do exemplo:
```bash
cp .env.example .env
# Edite com seu token e canal
```

3. Instale dependências:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Execute os testes:
```bash
python -m pytest tests/ -v
```

5. Execute o bot:
```bash
python scripts/main.py
```

## GitHub Actions

O scraping roda automaticamente via cron a cada hora. Configure os secrets:

- `TELEGRAM_BOT_TOKEN`
- `CANAL_ID`
- `ML_AFFILIATE_TAG` (opcional, padrão: `pcaldi`)

## Arquitetura

```
config.py              — Configurações e produtos monitorados
scripts/
  main.py              — Execução principal (scraping paralelo)
  commands.py          — Comandos do Telegram
  send_telegram.py     — Formatação e envio de ofertas
  scraper_amazon.py    — Scraper Amazon (HTTP)
  scraper_procorrer.py — Scraper Procorrer (Playwright)
  scraper_decathlon.py — Scraper Decathlon (Playwright)
  scraper_mercadolivre.py — Scraper Mercado Livre (HTTP)
  scraper_growth.py    — Scraper Growth (Playwright)
  scraper_playwright_runner.py — Executa scrapers em subprocessos
  browser_utils.py     — Gerenciador de browser Playwright
  core/
    base_scraper.py    — Classe base abstrata
    database.py        — SQLite (ofertas, histórico, enviadas)
    price_parser.py    — Parse e formatação de preços
tests/                 — 219 testes
```
