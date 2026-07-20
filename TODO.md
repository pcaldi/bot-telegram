# TODO - Checklist de Tarefas

## Fase 1: Melhorar Mensagens ao Usuario ✅

- [x] Atualizar funcao `formatar_oferta()` em `scripts/send_telegram.py`
- [x] Adicionar calculo de economia em R$ (preco_antigo - preco)
- [x] Adicionar categoria do produto na mensagem
- [x] Melhorar formatacao visual (negrito nos precos)
- [x] Testar envio de mensagem formatada

## Fase 2: Banco de Dados SQLite ✅

- [x] Criar `scripts/core/database.py` com SQLite manager
- [x] Criar schema com tabelas (ofertas, historico_precos, ofertas_enviadas)
- [x] Migrar `seen_products.json` para SQLite
- [x] Atualizar `scripts/main.py` para usar database
- [x] Manter compatibilidade com GitHub Actions cache
- [x] Testar persistencia de dados (17 testes)

## Fase 3: Adicionar Scraper Procorrer ✅

- [x] Criar `scripts/scraper_procorrer.py`
- [x] Implementar Playwright + stealth para Procorrer
- [x] Adicionar ao `_scrape_all()` em `main.py`
- [x] Adicionar emojis e dominios em `send_telegram.py`
- [x] Adicionar configuracoes em `config.py`
- [x] Testar busca de produtos (14 testes)

## Fase 4: Refatoracao do Codigo ✅

- [x] Criar `scripts/core/__init__.py`
- [x] Criar `scripts/core/base_scraper.py`
- [x] Criar `scripts/core/price_parser.py`
- [x] Atualizar `scraper_amazon.py` para herdar de BaseScraper
- [x] Atualizar `scraper_growth.py` para herdar de BaseScraper
- [x] Atualizar `scraper_decathlon.py` para herdar de BaseScraper
- [x] Substituir `print()` por `log` em todos scrapers
- [x] Adicionar type hints nos modulos principais

## Fase 5: Testes ✅

- [x] Criar `pytest.ini` com configuracoes
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
- [x] Scrapers so executam se testes passarem

## Fase 7: Comandos de Busca e Categorias ✅

- [x] Criar comando `/search <termo> [loja]`
- [x] Criar comandos de categoria (/corrida, /suplementos, /eletronicos)
- [x] Adicionar /casa, /esportes, /tenis
- [x] Atualizar /start e /help
- [x] Adicionar pytest-asyncio para testes async
- [x] Expandir termos de busca (16 marcas de tenis, vitaminas, etc)

## Fase 8: Correcoes Procorrer ✅

- [x] Corrigir seletor CSS (`.js-item-product` em vez de `div.product-card`)
- [x] Corrigir extracao de preco (ignorar parcelas, pegar preco a vista)
- [x] Melhorar extracao de imagem (data-src, data-lazy-src, data-original, filtra data:)
- [x] Adicionar `preco_pix` em `criar_produto()`
- [x] Adicionar `parcelamento` em `criar_produto()`
- [x] Adicionar `tamanhos` em `criar_produto()`
- [x] Atualizar `formatar_oferta()` com novos campos (PIX, parcelamento, tamanhos)
- [x] Adicionar colunas no banco SQLite (preco_pix, parcelamento, tamanhos)
- [x] Atualizar `check_and_mark()` em `main.py`
- [x] Corrigir strikethrough (`~~` → `<s>`)
- [x] Adicionar testes para novos campos

## Fase 9: Scraper Mercado Livre ✅

- [x] Criar `scripts/scraper_mercadolivre.py`
- [x] Implementar Playwright + stealth para ML
- [x] Parse de produtos (poly-card, andes-money-amount)
- [x] Adicionar tag de afiliado `?tag=pcaldi`
- [x] Adicionar ao `_scrape_all()` em `main.py`
- [x] Adicionar "Mercado Livre" ao `KNOWN_STORES`
- [x] Adicionar emoji e dominio em `send_telegram.py`
- [x] Adicionar produtos ML em `config.py`
- [x] Criar testes para scraper ML (13 testes)
- [x] Buscar por termo ao vez de /ofertas (produtos relevantes)

## Fase 10: Dashboard Web (Pendente)

- [ ] Criar `scripts/dashboard.py` (Flask)
- [ ] Criar template `templates/dashboard.html`
- [ ] Criar template `templates/produto.html`
- [ ] Rota `/` — lista de ofertas com filtros
- [ ] Rota `/produto/<id>` — detalhe + grafico de precos
- [ ] Rota `/api/ofertas` — JSON
- [ ] Rota `/api/historico/<id>` — JSON historico
- [ ] Rota `/api/stats` — estatisticas
- [ ] Integrar Chart.js para graficos
- [ ] Adicionar `flask` ao `requirements.txt`

## Fase 11: Otimizacoes de Performance ✅

- [x] Paralelizar scrapers via subprocess (5 em paralelo)
- [x] BrowserManager suporta multiplas instancias
- [x] Decathlon so busca termos relevantes (DECATHLON_TERMOS)
- [x] LOJAS_POR_PRODUTO — filtra lojas por categoria
- [x] SCRAPERS_DISABLED — desabilita scrapers temporariamente
- [x] max_por_scraper: 2 → 5 para mais variedade

## Fase 12: Controle de Acesso ✅

- [x] ADMIN_USER_IDS no config.py
- [x] Extrair user_id de message.from
- [x] Funcao _is_admin() com fallback (vazio = todos admin)
- [x] /add e /remove restritos a admins
- [x] Comando /myid para descobrir user_id
- [x] Atualizar /start e /help

## Fase 13: Correcao de Imagens Amazon ✅

- [x] Detectar placeholder grey-pixel.gif
- [x] Fallback para srcset quando placeholder detectado
- [x] Evitar ofertas com imagem quebrada no Telegram

## Fase 14: Melhorias Pendentes (Proxima Sprint)

### Performance Critica
- [ ] Reduzir sleep de 30s para 2s entre envios (`main.py:323`)
- [ ] Paralelizar comandos de categoria (evitar 80 chamadas sequenciais)
- [ ] Usar SELECT MIN(preco) no SQL em vez de carregar tudo no Python (`database.py:256`)
- [ ] Adicionar retry em `_send_message` do `commands.py`

### Correcoes de Codigo
- [ ] Remover `run_growth_batch` duplicado (`scraper_playwright_runner.py`)
- [ ] Validar CANAL_ID != 0 no startup (`config.py`)
- [ ] Remover GRUPO_ID nao utilizado (`config.py`)
- [ ] Usar funcoes importadas calcular_desconto/calcular_economia (`send_telegram.py`)

### Banco de Dados
- [ ] Adicionar indice em `ofertas.loja`
- [ ] Adicionar indice em `ofertas_enviadas.data_envio`
- [ ] Adicionar cleanup para `ofertas_enviadas` (tabela cresce infinito)
- [ ] Usar ON DELETE CASCADE nas foreign keys

### Seguranca
- [ ] Configurar ADMIN_USER_IDS com IDs reais
- [ ] Adicionar rate limiting por usuario nos comandos

### Testes
- [ ] Criar testes para `scraper_amazon.py`
- [ ] Criar testes para `scraper_decathlon.py`
- [ ] Criar testes para `scraper_growth.py`
- [ ] Criar testes para `check_and_mark()` em `main.py`
- [ ] Criar testes para `handle_message()` dispatch

### Documentacao
- [x] Atualizar TODO.md (Fase 9 ja concluida)
- [ ] Adicionar README.md com instrucoes de uso
- [ ] Documentar variaveis de ambiente (.env.example)

## Limpeza ✅

- [x] Remover scrapers legados (Centauro, Netshoes, ML, Shopee)
- [x] Remover `seen_products.json` (migrado para SQLite)
- [x] Atualizar documentacao

---

*Atualizado em: 2026-07-16*
