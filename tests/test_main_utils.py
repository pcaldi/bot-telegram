"""Testes para check_and_mark() e utilitários de main.py."""

import pytest
from unittest.mock import MagicMock, patch
from scripts.main import gerar_id, normalizar_url, normalizar_nome, dedup_produtos, check_and_mark
from scripts.core.database import Database


@pytest.fixture
def db():
    """Cria banco em memória para testes."""
    return Database(":memory:")


class TestGerarId:
    """Testes para gerar_id."""

    def test_id_com_url(self):
        prod = {"url": "https://amazon.com.br/dp/B123", "loja": "Amazon"}
        pid = gerar_id(prod)
        assert pid.startswith("amazon__")
        assert len(pid) > 10

    def test_id_sem_url(self):
        prod = {"nome": "Fone Bluetooth", "loja": "Amazon"}
        pid = gerar_id(prod)
        assert pid.startswith("amazon__")

    def test_id_consistente(self):
        prod = {"url": "https://amazon.com.br/dp/B123", "loja": "Amazon"}
        assert gerar_id(prod) == gerar_id(prod)

    id_diferente = [
        ({"url": "https://amazon.com.br/dp/B123", "loja": "Amazon"},
         {"url": "https://amazon.com.br/dp/B456", "loja": "Amazon"}),
        ({"url": "https://amazon.com.br/dp/B123", "loja": "Amazon"},
         {"url": "https://amazon.com.br/dp/B123", "loja": "Growth"}),
    ]

    @pytest.mark.parametrize("p1,p2", id_diferente)
    def test_id_diferente(self, p1, p2):
        assert gerar_id(p1) != gerar_id(p2)


class TestNormalizarUrl:
    """Testes para normalizar_url."""

    def test_remove_query(self):
        assert normalizar_url("https://amazon.com.br/dp/B123?tag=x&ref=y") == "amazon.com.br/dp/b123"

    def test_remove_ref(self):
        assert normalizar_url("https://amazon.com.br/dp/B123/ref=sr_1_1") == "amazon.com.br/dp/b123/ref=sr_1_1"

    def test_lowercase(self):
        url = normalizar_url("https://Amazon.com.br/Dp/B123")
        assert url == url.lower()

    def test_remove_trailing_slash(self):
        assert normalizar_url("https://amazon.com.br/") == "amazon.com.br"


class TestNormalizarNome:
    """Testes para normalizar_nome."""

    def test_lowercase(self):
        assert normalizar_nome("FONE BLUETOOTH") == "fone bluetooth"

    def test_remove_acentos(self):
        assert normalizar_nome("tênis corrida") == "tnis corrida"

    def test_remove_espacos(self):
        assert normalizar_nome("  fone   bluetooth  ") == "fone bluetooth"

    def test_remove_especiais(self):
        assert normalizar_nome("fone & bluetooth!") == "fone bluetooth"


class TestDedupProdutos:
    """Testes para dedup_produtos."""

    def test_dedup_por_url(self):
        prods = [
            {"url": "https://amazon.com.br/dp/B123", "nome": "Fone", "loja": "Amazon"},
            {"url": "https://amazon.com.br/dp/B123", "nome": "Fone Mesmo", "loja": "Amazon"},
        ]
        result = dedup_produtos(prods)
        assert len(result) == 1

    def test_dedup_por_nome(self):
        prods = [
            {"nome": "Fone Bluetooth", "loja": "Amazon"},
            {"nome": "Fone Bluetooth", "loja": "Amazon"},
        ]
        result = dedup_produtos(prods)
        assert len(result) == 1

    def test_sem_dedup_lojas_diferentes(self):
        prods = [
            {"url": "https://amazon.com.br/dp/B123", "nome": "Fone", "loja": "Amazon"},
            {"url": "https://growth.com.br/fone", "nome": "Fone", "loja": "Growth"},
        ]
        result = dedup_produtos(prods)
        assert len(result) == 2


class TestCheckAndMark:
    """Testes para check_and_mark."""

    def test_produto_novo(self, db):
        prod = {
            "nome": "Fone Bluetooth",
            "preco": 99.99,
            "loja": "Amazon",
            "url": "https://amazon.com.br/dp/B123",
        }
        result = check_and_mark(prod, db)
        assert result == "nova"

    def test_produto_preco_igual(self, db):
        prod = {
            "nome": "Fone Bluetooth",
            "preco": 99.99,
            "loja": "Amazon",
            "url": "https://amazon.com.br/dp/B123",
        }
        check_and_mark(prod, db)
        result = check_and_mark(prod, db)
        assert result is None

    def test_produto_queda_preco(self, db):
        prod1 = {
            "nome": "Fone Bluetooth",
            "preco": 199.99,
            "loja": "Amazon",
            "url": "https://amazon.com.br/dp/B123",
        }
        check_and_mark(prod1, db)

        prod2 = {
            "nome": "Fone Bluetooth",
            "preco": 99.99,
            "loja": "Amazon",
            "url": "https://amazon.com.br/dp/B123",
        }
        result = check_and_mark(prod2, db)
        assert result == "queda"
