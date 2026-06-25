"""Testes para o módulo main (deduplicação)."""

import pytest
from scripts.main import dedup_produtos, normalizar_url, normalizar_nome, gerar_id


class TestNormalizarUrl:
    """Testes para a função normalizar_url."""

    def test_url_basica(self):
        """Testa normalização de URL básica."""
        url = "https://www.amazon.com.br/produto"
        assert normalizar_url(url) == "www.amazon.com.br/produto"

    def test_url_com_trailing_slash(self):
        """Testa normalização removendo trailing slash."""
        url = "https://www.amazon.com.br/produto/"
        assert normalizar_url(url) == "www.amazon.com.br/produto"

    def test_url_case_insensitive(self):
        """Testa normalização case insensitive."""
        url = "https://WWW.AMAZON.COM.BR/PRODUTO"
        assert normalizar_url(url) == "www.amazon.com.br/produto"


class TestNormalizarNome:
    """Testes para a função normalizar_nome."""

    def test_nome_basico(self):
        """Testa normalização de nome básico."""
        nome = "Tenis Nike Air Max"
        assert normalizar_nome(nome) == "tenis nike air max"

    def test_nome_com_caracteres_especiais(self):
        """Testa normalização removendo caracteres especiais."""
        nome = "Tenis Nike Air-Max"
        assert normalizar_nome(nome) == "tenis nike airmax"

    def test_nome_com_espacos_extras(self):
        """Testa normalização removendo espaços extras."""
        nome = "Tenis   Nike   Air   Max"
        assert normalizar_nome(nome) == "tenis nike air max"


class TestGerarId:
    """Testes para a função gerar_id."""

    def test_id_com_url(self):
        """Testa geração de ID com URL."""
        produto = {
            "url": "https://www.amazon.com.br/produto",
            "loja": "Amazon",
        }
        pid = gerar_id(produto)
        assert pid.startswith("amazon__")
        assert len(pid) == 24  # amazon__ (8) + 16 chars do hash

    def test_id_sem_url(self):
        """Testa geração de ID sem URL."""
        produto = {
            "nome": "Tênis Nike Air Max",
            "loja": "Amazon",
        }
        pid = gerar_id(produto)
        assert pid.startswith("amazon__")
        assert len(pid) == 24


class TestDedupProdutos:
    """Testes para a função dedup_produtos."""

    def test_dedup_urls_iguais(self):
        """Testa deduplicação de URLs idênticas."""
        produtos = [
            {"url": "https://amazon.com/p1", "nome": "Produto 1", "loja": "Amazon"},
            {"url": "https://amazon.com/p1", "nome": "Produto 1 Duplicado", "loja": "Amazon"},
        ]
        resultado = dedup_produtos(produtos)
        assert len(resultado) == 1

    def test_dedup_nomes_iguais_mesma_loja(self):
        """Testa deduplicação de nomes iguais na mesma loja."""
        produtos = [
            {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
            {"url": "https://amazon.com/p2", "nome": "Tênis Nike", "loja": "Amazon"},
        ]
        resultado = dedup_produtos(produtos)
        assert len(resultado) == 1

    def test_dedup_nomes_iguais_lojas_diferentes(self):
        """Testa que produtos iguais em lojas diferentes NÃO são deduplicados."""
        produtos = [
            {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
            {"url": "https://growth.com/p2", "nome": "Tênis Nike", "loja": "Growth"},
        ]
        resultado = dedup_produtos(produtos)
        assert len(resultado) == 2

    def test_dedup_produtos_diferentes(self):
        """Testa que produtos diferentes NÃO são deduplicados."""
        produtos = [
            {"url": "https://amazon.com/p1", "nome": "Tênis Nike", "loja": "Amazon"},
            {"url": "https://amazon.com/p2", "nome": "Tênis Adidas", "loja": "Amazon"},
        ]
        resultado = dedup_produtos(produtos)
        assert len(resultado) == 2

    def test_dedup_lista_vazia(self):
        """Testa deduplicação de lista vazia."""
        resultado = dedup_produtos([])
        assert len(resultado) == 0

    def test_dedup_lista_unica(self):
        """Testa deduplicação com um único produto."""
        produtos = [
            {"url": "https://amazon.com/p1", "nome": "Produto", "loja": "Amazon"},
        ]
        resultado = dedup_produtos(produtos)
        assert len(resultado) == 1
