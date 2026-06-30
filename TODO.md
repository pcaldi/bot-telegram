# 📝 TODO - Checklist de Tarefas

## Fase 1: Melhorar Mensagens ao Usuário ✅

- [x] Atualizar função `formatar_oferta()` em `scripts/send_telegram.py`
- [x] Adicionar cálculo de economia em R$ (preco_antigo - preco)
- [x] Adicionar categoria do produto na mensagem
- [x] Melhorar formatação visual (negrito nos preços)
- [x] Testar envio de mensagem formatada

## Fase 2: Banco de Dados SQLite ✅

- [x] Criar `scripts/core/database.py` com SQLite manager
- [x] Criar schema com tabelas (ofertas, historico_precos, ofertas_enviadas)
- [x] Migrar `seen_products.json` para SQLite
- [x] Atualizar `scripts/main.py` para usar database
- [x] Manter compatibilidade com GitHub Actions cache
- [x] Testar persistência de dados (17 testes)

## Fase 3: Adicionar Scraper Procorrer ✅

- [x] Criar `scripts/scraper_procorrer.py`
- [x] Implementar Playwright + stealth para Procorrer
- [x] Adicionar ao `_scrape_all()` em `main.py`
- [x] Adicionar emojis e domínios em `send_telegram.py`
- [x] Adicionar configurações em `config.py`
- [x] Testar busca de produtos (14 testes)

## Fase 4: Refatoração do Código ✅

- [x] Criar `scripts/core/__init__.py`
- [x] Criar `scripts/core/base_scraper.py`
- [x] Criar `scripts/core/price_parser.py`
- [x] Atualizar `scraper_amazon.py` para herdar de BaseScraper
- [x] Atualizar `scraper_growth.py` para herdar de BaseScraper
- [x] Atualizar `scraper_decathlon.py` para herdar de BaseScraper
- [x] Substituir `print()` por `log` em todos scrapers
- [x] Adicionar type hints nos módulos principais

## Fase 5: Testes ✅

- [x] Criar `pytest.ini` com configurações
- [x] Criar `tests/__init__.py`
- [x] Criar `tests/conftest.py` com fixtures
- [x] Criar `tests/test_price_parser.py` (17 testes)
- [x] Criar `tests/test_send_telegram.py` (14 testes)
- [x] Criar `tests/test_dedup.py` (11 testes)
- [x] Criar `tests/test_commands.py` (12 testes)
- [x] Criar `tests/test_database.py` (17 testes)
- [x] Criar `tests/test_scraper_procorrer.py` (14 testes)
- [x] Adicionar `pytest` e `pytest-cov` ao `requirements.txt`
- [x] Rodar testes e verificar se passam (101 testes)

## Fase 6: GitHub Actions com Testes ✅

- [x] Adicionar job `test` antes do scraping
- [x] Adicionar cache de Playwright browsers
- [x] Scrapers só executam se testes passarem

## Fase 7: Comandos de Busca e Categorias ✅

- [x] Criar comando `/search <termo> [loja]`
- [x] Criar comandos de categoria (/corrida, /suplementos, /eletronicos)
- [x] Adicionar /casa, /esportes, /tenis
- [x] Atualizar /start e /help
- [x] Adicionar pytest-asyncio para testes async
- [x] Expandir termos de busca (16 marcas de tênis, vitaminas, etc)

## Fase 8: Correções Procorrer (Pendente)

- [ ] Corrigir seletor CSS (`.js-item-product` em vez de `div.product-card`)
- [ ] Corrigir extração de preço (ignorar parcelas, pegar preço à vista)
- [ ] Melhorar extração de imagem (testar data-src, data-lazy-src)
- [ ] Adicionar `preco_pix` em `criar_produto()`
- [ ] Adicionar `parcelamento` em `criar_produto()`
- [ ] Adicionar `tamanhos` em `criar_produto()`
- [ ] Atualizar `formatar_oferta()` com novos campos
- [ ] Adicionar colunas no banco SQLite
- [ ] Atualizar `check_and_mark()` em `main.py`
- [ ] Corrigir strikethrough (`~~` → `<s>`)
- [ ] Adicionar testes para novos campos

## Fase 9: Scraper Mercado Livre (Pendente)

- [ ] Criar `scripts/scraper_mercadolivre.py`
- [ ] Implementar HTTP scraping (cloudscraper + BeautifulSoup)
- [ ] Parse de produtos (`.ui-search-item__title`, `.price-tag-fraction`)
- [ ] Adicionar ao `_scrape_all()` em `main.py`
- [ ] Adicionar `"Mercado Livre"` ao `KNOWN_STORES`
- [ ] Adicionar emoji e domínio em `send_telegram.py`
- [ ] Adicionar produtos ML em `config.py`
- [ ] Criar testes para scraper ML

## Fase 10: Dashboard Web (Pendente)

- [ ] Criar `scripts/dashboard.py` (Flask)
- [ ] Criar template `templates/dashboard.html`
- [ ] Criar template `templates/produto.html`
- [ ] Rota `/` — lista de ofertas com filtros
- [ ] Rota `/produto/<id>` — detalhe + gráfico de preços
- [ ] Rota `/api/ofertas` — JSON
- [ ] Rota `/api/historico/<id>` — JSON histórico
- [ ] Rota `/api/stats` — estatísticas
- [ ] Integrar Chart.js para gráficos
- [ ] Adicionar `flask` ao `requirements.txt`

## Limpeza ✅

- [x] Remover scrapers legados (Centauro, Netshoes, ML, Shopee)
- [x] Remover `seen_products.json` (migrado para SQLite)
- [x] Atualizar documentação

---

*Atualizado em: 2026-06-30*
