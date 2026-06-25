"""Fixtures compartilhadas para testes."""

import sys
import os
import pytest

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def produto_exemplo():
    """Retorna um produto de exemplo para testes."""
    return {
        "nome": "Tênis Nike Air Max 90 Masculino",
        "preco": 349.99,
        "preco_antigo": 599.99,
        "url": "https://www.amazon.com.br/produto1",
        "loja": "Amazon",
        "imagem": "https://m.media-amazon.com/images/I/img1.jpg",
        "frete": "Frete grátis",
    }


@pytest.fixture
def produto_sem_desconto():
    """Retorna um produto sem desconto para testes."""
    return {
        "nome": "Fone JBL Tune 510BT",
        "preco": 199.99,
        "url": "https://www.amazon.com.br/produto2",
        "loja": "Amazon",
        "imagem": "https://m.media-amazon.com/images/I/img2.jpg",
    }


@pytest.fixture
def produto_queda():
    """Retorna uma queda de preço para testes."""
    return {
        "nome": "Whey Protein Concentrado 1kg",
        "preco": 89.99,
        "preco_antigo": 129.99,
        "url": "https://www.gsuplementos.com.br/produto3",
        "loja": "Growth",
        "imagem": "https://gsuplementos.com.br/img3.jpg",
        "tipo": "queda",
    }


@pytest.fixture
def lista_produtos():
    """Retorna uma lista de produtos para testes de deduplicação."""
    return [
        {
            "nome": "Tênis Nike Air Max",
            "preco": 349.99,
            "url": "https://www.amazon.com.br/produto1",
            "loja": "Amazon",
        },
        {
            "nome": "Tênis Nike Air Max",
            "preco": 359.99,
            "url": "https://www.amazon.com.br/produto1-dup",
            "loja": "Amazon",
        },
        {
            "nome": "Tênis Adidas Coreracer",
            "preco": 299.99,
            "url": "https://www.amazon.com.br/produto2",
            "loja": "Amazon",
        },
        {
            "nome": "Tênis Nike Air Max",
            "preco": 339.99,
            "url": "https://www.gsuplementos.com.br/produto3",
            "loja": "Growth",
        },
    ]
