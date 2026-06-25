"""Testes para o módulo send_telegram."""

import pytest
from scripts.send_telegram import (
    formatar_oferta,
    extrair_marca,
    extrair_categoria,
)


class TestExtrairMarca:
    """Testes para a função extrair_marca."""

    def test_marca_nike(self):
        """Testa extração de marca Nike."""
        assert extrair_marca("Tênis Nike Air Max") == "Nike"

    def test_marca_adidas(self):
        """Testa extração de marca Adidas."""
        assert extrair_marca("Tênis Adidas Coreracer") == "Adidas"

    def test_marca_jbl(self):
        """Testa extração de marca JBL."""
        assert extrair_marca("Fone JBL Tune 510BT") == "JBL"

    def test_marca_nao_encontrada(self):
        """Testa quando marca não é encontrada."""
        assert extrair_marca("Produto Genérico") == "Produto"

    def test_marca_case_insensitive(self):
        """Testa extração de marca case insensitive."""
        assert extrair_marca("tênis NIKE air max") == "Nike"


class TestExtrairCategoria:
    """Testes para a função extrair_categoria."""

    def test_categoria_tenis(self):
        """Testa extração de categoria Tênis."""
        assert extrair_categoria("Tênis Nike Air Max") == "Tênis"

    def test_categoria_eletronicos(self):
        """Testa extração de categoria Eletrônicos."""
        assert extrair_categoria("Fone JBL Bluetooth") == "Eletrônicos"

    def test_categoria_suplementos(self):
        """Testa extração de categoria Suplementos."""
        assert extrair_categoria("Whey Protein Concentrado") == "Suplementos"

    def test_categoria_roupas(self):
        """Testa extração de categoria Roupas."""
        assert extrair_categoria("Camiseta Nike") == "Roupas"

    def test_categoria_acessorios(self):
        """Testa extração de categoria Acessórios."""
        assert extrair_categoria("Mochila Esportiva") == "Acessórios"

    def test_categoria_casa(self):
        """Testa extração de categoria Casa."""
        assert extrair_categoria("Air Fryer Mondial") == "Casa"

    def test_categoria_esportes(self):
        """Testa extração de categoria Esportes."""
        assert extrair_categoria("Bola de Futebol") == "Esportes"

    def test_categoria_outros(self):
        """Testa quando categoria não é encontrada."""
        assert extrair_categoria("Produto Qualquer") == "Outros"


class TestFormatarOferta:
    """Testes para a função formatar_oferta."""

    def test_oferta_nova(self, produto_exemplo):
        """Testa formatação de nova oferta."""
        texto = formatar_oferta(produto_exemplo)
        assert "NOVA OFERTA" in texto
        assert "R$ 349,99" in texto
        assert "Amazon" in texto

    def test_oferta_com_desconto(self, produto_exemplo):
        """Testa formatação com desconto."""
        texto = formatar_oferta(produto_exemplo)
        assert "R$ 599,99" in texto
        assert "-41%" in texto
        assert "Economia" in texto

    def test_oferta_sem_desconto(self, produto_sem_desconto):
        """Testa formatação sem desconto."""
        texto = formatar_oferta(produto_sem_desconto)
        assert "NOVA OFERTA" in texto
        assert "R$ 199,99" in texto
        assert "De R$" not in texto

    def test_oferta_queda(self, produto_queda):
        """Testa formatação de queda de preço."""
        texto = formatar_oferta(produto_queda)
        assert "QUEDA DE PREÇO" in texto
        assert "R$ 89,99" in texto
        assert "-30%" in texto

    def test_oferta_categoria(self, produto_exemplo):
        """Testa se categoria é exibida na mensagem."""
        texto = formatar_oferta(produto_exemplo)
        assert "Tênis" in texto

    def test_oferta_link(self, produto_exemplo):
        """Testa se link está na mensagem."""
        texto = formatar_oferta(produto_exemplo)
        assert "Comprar agora" in texto
        assert "href=" in texto

    def test_oferta_nome_limitado(self):
        """Testa se nome é limitado a 80 caracteres."""
        produto = {
            "nome": "A" * 100,
            "preco": 100.00,
            "url": "https://example.com",
            "loja": "Amazon",
        }
        texto = formatar_oferta(produto)
        # O nome deve ser truncado para 80 caracteres
        assert "A" * 80 in texto
        assert "A" * 81 not in texto

    def test_oferta_menor_preco(self):
        """Testa indicador de menor preço já visto."""
        produto = {
            "nome": "Produto Teste",
            "preco": 99.99,
            "url": "https://example.com",
            "loja": "Amazon",
            "menor_preco": 99.99,
        }
        texto = formatar_oferta(produto)
        assert "Menor preço já visto" in texto

    def test_oferta_sem_menor_preco(self):
        """Testa quando não é menor preço."""
        produto = {
            "nome": "Produto Teste",
            "preco": 199.99,
            "url": "https://example.com",
            "loja": "Amazon",
            "menor_preco": 99.99,
        }
        texto = formatar_oferta(produto)
        assert "Menor preço já visto" not in texto
