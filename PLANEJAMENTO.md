# 📋 Planejamento de Melhorias - Bot de Ofertas

## Visão Geral

Este documento descreve as melhorias planejadas para o bot de ofertas de Telegram, organizadas por prioridade e impacto.

---

## Status Atual

| Componente | Estado | Observação |
|---|---|---|
| Amazon scraper | ✅ Funciona | cloudscraper + imagens |
| Growth scraper | ✅ Funciona | Playwright batch + JSON-LD |
| Procorrer scraper | ✅ Funciona | Playwright + stealth |
| Decathlon scraper | ✅ Funciona | Playwright + stealth |
| Telegram commands | ✅ Funciona | /add, /remove, /list |
| GitHub Actions | ✅ Funciona | cron 1h + cache + testes |
| Deduplication | ✅ Funciona | URL + nome |
| Price tracking | ✅ Funciona | SQLite (ofertas.db) |
| Testes | ✅ Funciona | 101 testes (pytest) |

---

## Fase 1: Melhorar Mensagens ao Usuário

**Prioridade:** Alta | **Esforço:** 1-2 dias | **Impacto:** Alto

### Problema Atual
Mensagem funcional mas sem diferenciação visual forte. Não mostra economia em R$, categoria do produto, nem indicadores de melhor preço.

### Melhorias

| Melhoria | Descrição | Impacto |
|---|---|---|
| Badge de desconto visível | Mostrar percentual de desconto em destaque | Alto |
| Economia em R$ | Calcular e exibir valor economizado | Alto |
| Categoria do produto | Tag: Tênis, Eletrônicos, Suplementos | Médio |
| Menor preço visto | Indicar se é o menor preço registrado | Alto |
| Formatação numérica | Negrito nos preços para fácil leitura | Médio |

### Exemplo de Mensagem Melhorada

```
🔥 NOVA OFERTA!

📦 Tênis Nike Air Max 90 Masculino

💰 De R$ 599,99
✅ Por R$ 349,99  -41%
🏷️ Economia: R$ 250,00

🟡 Amazon
🛒 Comprar agora
```

### Arquivos Alterados
- `scripts/send_telegram.py` → função `formatar_oferta()`
- `config.py` → verificar campo `categoria`

---

## Fase 2: Banco de Dados SQLite

**Prioridade:** Alta | **Esforço:** 2-3 dias | **Impacto:** Alto

### Problema Atual
`seen_products.json` é limitado:
- Sem consultas por data/loja/preço
- Sem histórico de preços real
- Sem backup automático
- Cresce infinitamente (pruning manual)

### Solução

#### Schema do Banco

```sql
-- Tabela de ofertas monitoradas
CREATE TABLE ofertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    preco_atual REAL,
    preco_antigo REAL,
    loja TEXT NOT NULL,
    url TEXT,
    imagem TEXT,
    categoria TEXT,
    primeira_vista TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_vista TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de histórico de preços
CREATE TABLE historico_precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id TEXT NOT NULL,
    preco REAL NOT NULL,
    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES ofertas(produto_id)
);

-- Tabela de ofertas enviadas
CREATE TABLE ofertas_enviadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    preco_enviado REAL,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES ofertas(produto_id)
);
```

#### Benefícios
- Consultar "menor preço da semana"
- Gráfico de tendência de preços
- Filtrar por loja/categoria
- Backup automático via GitHub Actions
- Histórico completo de preços

### Arquivos Criados
- `scripts/database.py`
- `data/schema.sql`

### Arquivos Alterados
- `scripts/main.py` → usar database em vez de JSON
- `requirements.txt`

---

## Fase 3: Adicionar Scraper Procorrer

**Prioridade:** Média | **Esforço:** 2-3 dias | **Impacto:** Médio

### Por que Procorrer?
- Nicho similar (tênis de corrida)
- 60-70% de sucesso com Playwright + stealth
- Mesma stack tecnológica existente

### Implementação

#### Estrutura do Scraper

```python
# scripts/scraper_procorrer.py
class ProcorrerScraper:
    def __init__(self):
        self.base_url = "https://www.procorrer.com.br"

    def buscar(self, termo, max_preco=None, context=None):
        # Playwright + stealth
        # Parse de produtos
        # Retorno padronizado
```

#### Integração

1. Criar `scripts/scraper_procorrer.py`
2. Adicionar ao `_scrape_all()` em `main.py`
3. Adicionar emojis e domínios em `send_telegram.py`
4. Adicionar configurações em `config.py`

### Arquivos Criados
- `scripts/scraper_procorrer.py`

### Arquivos Alterados
- `scripts/main.py`
- `scripts/send_telegram.py`
- `config.py`

---

## Fase 4: Refatoração do Código

**Prioridade:** Média | **Esforço:** 3-5 dias | **Impacto:** Alto (manutenção)

### Problemas Identificados

| Problema | Arquivo | Impacto |
|---|---|---|
| `sys.path.append` frágil | Todos scrapers | Import errors |
| Sem classe base | scraper_amazon, decathlon | Duplicação |
| `print()` em vez de `log` | scraper_growth, decathlon | Debug difícil |
| Sem type hints | Todos | Manutenção difícil |
| Sem testes | Nenhum | Regressão |
| Tratamento de erro inconsistente | Todos | Bugs silenciosos |

### Nova Arquitetura

```
scripts/
├── core/
│   ├── __init__.py
│   ├── base_scraper.py      # Classe abstrata para scrapers
│   ├── price_parser.py      # Função comum de parse de preço
│   └── database.py          # SQLite manager
├── scrapers/
│   ├── __init__.py
│   ├── amazon.py            # Herda de BaseScraper
│   ├── growth.py            # Herda de BaseScraper
│   ├── decathlon.py         # Herda de BaseScraper
│   └── procorrer.py         # Herda de BaseScraper
├── main.py
├── send_telegram.py
├── commands.py
└── browser_utils.py
```

### Classe Base

```python
# scripts/core/base_scraper.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, nome_loja: str, emoji: str, dominio: str):
        self.nome_loja = nome_loja
        self.emoji = emoji
        self.dominio = dominio

    @abstractmethod
    def buscar(self, termo: str, max_preco: float = None) -> list:
        pass

    def parse_preco(self, texto: str) -> float:
        """Parse de preço de texto para float"""
        import re
        texto = re.sub(r'[^\d.,]', '', texto)
        texto = texto.replace('.', '').replace(',', '.')
        return float(texto) if texto else 0.0
```

### Arquivos Criados
- `scripts/core/__init__.py`
- `scripts/core/base_scraper.py`
- `scripts/core/price_parser.py`

### Arquivos Alterados
- Todos os scrapers (herdar de BaseScraper)
- `scripts/main.py`

---

## Fase 5: Testes

**Prioridade:** Alta | **Esforço:** 2-3 dias | **Impacto:** Alto (qualidade)

### Por que Testes?
- Garantir que mudanças não quebram funcionalidades existentes
- Facilitar adição de novos scrapers com confiança
- Documentar comportamento esperado do código
- Detectar bugs antes de colocar em produção

### Estrutura de Testes

```
tests/
├── __init__.py
├── test_price_parser.py      # Testes de parse de preço
├── test_send_telegram.py     # Testes de formatação de mensagem
├── test_dedup.py             # Testes de deduplicação
├── test_commands.py          # Testes de comandos Telegram
├── test_database.py          # Testes de persistência
└── conftest.py               # Fixtures compartilhadas
```

### Testes Unitários Importantes

#### 1. Parse de Preço (`test_price_parser.py`)

```python
import pytest
from scripts.core.price_parser import parse_preco

def test_parse_preco_basico():
    assert parse_preco("R$ 199,99") == 199.99

def test_parse_preco_ponto_milhar():
    assert parse_preco("R$ 1.299,99") == 1299.99

def test_parse_preco_vazio():
    assert parse_preco("") == 0.0

def test_parse_preco_none():
    assert parse_preco(None) == 0.0

def test_parse_preco_sem_prefixo():
    assert parse_preco("299,99") == 299.99

def test_parse_preco_zero():
    assert parse_preco("R$ 0,00") == 0.0
```

#### 2. Formatação de Mensagem (`test_send_telegram.py`)

```python
import pytest
from scripts.send_telegram import formatar_oferta

def test_formatar_oferta_nova():
    produto = {
        "nome": "Tênis Nike Air Max",
        "preco": 299.99,
        "loja": "Amazon",
        "url": "https://amazon.com/produto",
        "tipo": "nova"
    }
    texto = formatar_oferta(produto)
    assert "NOVA OFERTA" in texto
    assert "R$ 299,99" in texto
    assert "Amazon" in texto

def test_formatar_oferta_queda():
    produto = {
        "nome": "Tênis Nike Air Max",
        "preco": 299.99,
        "preco_antigo": 599.99,
        "loja": "Amazon",
        "url": "https://amazon.com/produto",
        "tipo": "queda"
    }
    texto = formatar_oferta(produto)
    assert "QUEDA DE PREÇO" in texto
    assert "-50%" in texto
    assert "R$ 300,00" in texto  # Economia

def test_formatar_oferta_com_imagem():
    produto = {
        "nome": "Produto",
        "preco": 100.00,
        "imagem": "https://example.com/img.jpg",
        "tipo": "nova"
    }
    # Verificar se formatação está correta
    texto = formatar_oferta(produto)
    assert "R$ 100,00" in texto
```

#### 3. Deduplicação (`test_dedup.py`)

```python
import pytest
from scripts.main import dedup_produtos

def test_dedup_urls_iguais():
    produtos = [
        {"url": "https://amazon.com/produto1", "nome": "Produto 1", "loja": "Amazon"},
        {"url": "https://amazon.com/produto1", "nome": "Produto 1 Duplicado", "loja": "Amazon"}
    ]
    resultado = dedup_produtos(produtos)
    assert len(resultado) == 1

def test_dedup_nomes_iguais_mesma_loja():
    produtos = [
        {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
        {"url": "https://amazon.com/p2", "nome": "Tênis Nike", "loja": "Amazon"}
    ]
    resultado = dedup_produtos(produtos)
    assert len(resultado) == 1

def test_dedup_nomes_iguais_lojas_diferentes():
    produtos = [
        {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
        {"url": "https://growth.com/p2", "nome": "Tênis Nike", "loja": "Growth"}
    ]
    resultado = dedup_produtos(produtos)
    assert len(resultado) == 2  # Lojas diferentes = produto diferente

def test_dedup_produtos_diferentes():
    produtos = [
        {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
        {"url": "https://amazon.com/p2", "nome": "Tênis Adidas", "loja": "Amazon"}
    ]
    resultado = dedup_produtos(produtos)
    assert len(resultado) == 2
```

#### 4. Comandos (`test_commands.py`)

```python
import pytest
from scripts.commands import _handle_add, _handle_remove, _handle_list, load_custom

@pytest.fixture(autouse=True)
def reset_custom():
    """Reset custom products before each test"""
    import scripts.commands as cmds
    cmds._custom_products = []
    yield
    cmds._custom_products = []

def test_handle_add():
    resultado = _handle_add("air fryer 500")
    assert "Adicionado" in resultado
    assert "Air Fryer" in resultado

def test_handle_add_preco_default():
    resultado = _handle_add("notebook dell")
    assert "Adicionado" in resultado
    assert "500" in resultado  # Preço padrão

def test_handle_add_duplicado():
    _handle_add("air fryer 500")
    resultado = _handle_add("air fryer 500")
    assert "Já existe" in resultado

def test_handle_remove():
    _handle_add("produto teste")
    resultado = _handle_remove("1")
    assert "Removido" in resultado

def test_handle_remove_invalido():
    resultado = _handle_remove("999")
    assert "inválido" in resultado

def test_handle_list_vazio():
    resultado = _handle_list()
    assert "Nenhum produto" in resultado

def test_handle_list_com_produtos():
    _handle_add("produto 1")
    _handle_add("produto 2")
    resultado = _handle_list()
    assert "1." in resultado
    assert "2." in resultado
```

#### 5. Database (`test_database.py`)

```python
import pytest
from scripts.database import Database

@pytest.fixture
def db():
    """Create in-memory database for testing"""
    return Database(":memory:")

def test_salvar_e_buscar_oferta(db):
    db.salvar_oferta({
        "produto_id": "test1",
        "nome": "Produto Teste",
        "preco_atual": 199.99,
        "loja": "Amazon"
    })
    oferta = db.buscar_oferta("test1")
    assert oferta is not None
    assert oferta["nome"] == "Produto Teste"
    assert oferta["preco_atual"] == 199.99

def test_atualizar_preco(db):
    db.salvar_oferta({
        "produto_id": "test1",
        "nome": "Produto",
        "preco_atual": 199.99,
        "loja": "Amazon"
    })
    db.atualizar_preco("test1", 179.99)
    oferta = db.buscar_oferta("test1")
    assert oferta["preco_atual"] == 179.99

def test_historico_precos(db):
    db.salvar_oferta({
        "produto_id": "test1",
        "nome": "Produto",
        "preco_atual": 199.99,
        "loja": "Amazon"
    })
    db.salvar_historico("test1", 199.99)
    db.salvar_historico("test1", 189.99)
    db.salvar_historico("test1", 179.99)
    historico = db.buscar_historico("test1")
    assert len(historico) == 3
    assert historico[0]["preco"] == 199.99

def test_menor_preco(db):
    db.salvar_oferta({
        "produto_id": "test1",
        "nome": "Produto",
        "preco_atual": 199.99,
        "loja": "Amazon"
    })
    db.salvar_historico("test1", 199.99)
    db.salvar_historico("test1", 179.99)
    menor = db.buscar_menor_preco("test1")
    assert menor == 179.99

def test_ofertas_por_loja(db):
    db.salvar_oferta({"produto_id": "p1", "nome": "P1", "loja": "Amazon"})
    db.salvar_oferta({"produto_id": "p2", "nome": "P2", "loja": "Growth"})
    db.salvar_oferta({"produto_id": "p3", "nome": "P3", "loja": "Amazon"})
    ofertas = db.buscar_por_loja("Amazon")
    assert len(ofertas) == 2
```

### Configuração do pytest

**Arquivo:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

**Adicionar ao `requirements.txt`:**

```
pytest>=8.0.0
pytest-cov>=4.0.0
```

### Como Rodar Testes

```bash
# Rodar todos os testes
pytest

# Rodar com cobertura
pytest --cov=scripts

# Rodar teste específico
pytest tests/test_price_parser.py

# Rodar com verbose
pytest -v
```

### Arquivos Criados
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_price_parser.py`
- `tests/test_send_telegram.py`
- `tests/test_dedup.py`
- `tests/test_commands.py`
- `tests/test_database.py`
- `pytest.ini`

### Arquivos Alterados
- `requirements.txt` → adicionar `pytest` e `pytest-cov`

---

## Resumo de Impacto

| Fase | Tempo | Impacto Usuário | Impacto Código |
|---|---|---|---|
| Mensagens | 1-2 dias | ⭐⭐⭐ Alto | ⭐ Baixo |
| SQLite | 2-3 dias | ⭐⭐ Médio | ⭐⭐⭐ Alto |
| Procorrer | 2-3 dias | ⭐⭐ Médio | ⭐⭐ Médio |
| Refatoração | 3-5 dias | ⭐ Baixo | ⭐⭐⭐ Alto |
| Testes | 2-3 dias | ⭐ Baixo | ⭐⭐⭐ Alto |

**Total estimado:** 10-16 dias de trabalho

---

## Sites Bloqueados (Futuro)

| Site | Proteção | Necessário | Sucesso Estimado |
|---|---|---|---|
| Mercado Livre | Cloudflare v2 + ML | Proxy residencial | 30-40% |
| Centauro | Enterprise anti-bot | Proxy residencial | 40-50% |
| Netshoes | Akamai + TLS | Proxy mobile | 30-40% |

**Nota:** Esses sites requerem investimento em infraestrutura (proxies residenciais) para funcionar. Não são viáveis sem gasto.

---

## Decisões Pendentes

1. **SQLite vs PostgreSQL:** SQLite é mais simples para projeto pessoal. PostgreSQL para escala futura.

2. **Refatorar antes ou depois:** Refatorar antes facilita adicionar novos sites. Depois pode gerar mais trabalho.

3. **Procorrer primeiro:** É o site mais viável para adicionar agora.

4. **Testes primeiro ou depois:** Testes podem ser feitos antes (TDD) ou depois (para garantir).

---

*Documento atualizado em: 2026-06-25*
