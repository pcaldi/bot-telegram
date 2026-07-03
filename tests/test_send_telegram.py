"""Testes para o módulo send_telegram."""

import pytest
from unittest.mock import patch, AsyncMock
from scripts.send_telegram import (
    formatar_oferta,
    extrair_marca,
    extrair_categoria,
    validar_produto,
    enviar_oferta,
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

    def test_oferta_url_invalida(self):
        """Testa formatação com link inválido."""
        produto = {
            "nome": "Produto Teste",
            "preco": 99.99,
            "url": "https://example.com",
            "loja": "Amazon",
            "url_valido": False,
        }
        texto = formatar_oferta(produto)
        assert "Link indisponível" in texto
        assert "Comprar agora" not in texto

    def test_oferta_com_pix(self):
        """Testa formatação com preço PIX."""
        produto = {
            "nome": "Produto PIX",
            "preco": 199.99,
            "preco_pix": 179.99,
            "url": "https://example.com",
            "loja": "Amazon",
        }
        texto = formatar_oferta(produto)
        assert "no PIX: R$" in texto
        assert "179,99" in texto

    def test_oferta_com_parcelamento(self):
        """Testa formatação com parcelamento."""
        produto = {
            "nome": "Produto Parcelado",
            "preco": 299.99,
            "parcelamento": "10x de R$29,99",
            "url": "https://example.com",
            "loja": "Amazon",
        }
        texto = formatar_oferta(produto)
        assert "10x de R$29,99" in texto

    def test_oferta_com_tamanhos(self):
        """Testa formatação com tamanhos disponíveis."""
        produto = {
            "nome": "Produto com Tamanhos",
            "preco": 199.99,
            "tamanhos": ["38", "39", "40", "41"],
            "url": "https://example.com",
            "loja": "Amazon",
        }
        texto = formatar_oferta(produto)
        assert "38, 39, 40, 41" in texto

    def test_oferta_sem_pix_maior(self):
        """Testa quando PIX é maior que preço (não mostra)."""
        produto = {
            "nome": "Produto",
            "preco": 100.00,
            "preco_pix": 110.00,
            "url": "https://example.com",
            "loja": "Amazon",
        }
        texto = formatar_oferta(produto)
        assert "no PIX" not in texto


class TestValidarProduto:
    """Testes para a função validar_produto."""

    def test_url_valida(self):
        """Testa URL válida."""
        produto = {"url": "https://www.amazon.com.br/produto/123"}
        result = validar_produto(produto)
        assert result["url_valido"] is True

    def test_url_vazia(self):
        """Testa URL vazia."""
        produto = {"url": ""}
        result = validar_produto(produto)
        assert result["url_valido"] is False

    def test_url_sem_protocolo(self):
        """Testa URL sem protocolo."""
        produto = {"url": "www.amazon.com.br/produto"}
        result = validar_produto(produto)
        assert result["url_valido"] is False

    def test_url_truncada(self):
        """Testa URL muito curta (truncada)."""
        produto = {"url": "https://amzn"}
        result = validar_produto(produto)
        assert result["url_valido"] is False

    def test_url_http(self):
        """Testa URL com HTTP."""
        produto = {"url": "http://www.amazon.com.br/produto/123"}
        result = validar_produto(produto)
        assert result["url_valido"] is True

    def test_imagem_data_uri(self):
        """Testa remoção de placeholder data:."""
        produto = {"imagem": "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="}
        result = validar_produto(produto)
        assert result["imagem"] == ""

    def test_imagem_valida(self):
        """Testa imagem HTTP válida."""
        produto = {"imagem": "https://example.com/img.jpg"}
        result = validar_produto(produto)
        assert result["imagem"] == "https://example.com/img.jpg"

    def test_imagem_protocolo_relativo(self):
        """Testa conversão de // para https://."""
        produto = {"imagem": "//cdn.example.com/img.jpg"}
        result = validar_produto(produto)
        assert result["imagem"] == "https://cdn.example.com/img.jpg"

    def test_imagem_vazia(self):
        """Testa imagem vazia."""
        produto = {"imagem": ""}
        result = validar_produto(produto)
        assert result["imagem"] == ""

    def test_produto_sem_url(self):
        """Testa produto sem campo URL."""
        produto = {"nome": "Teste"}
        result = validar_produto(produto)
        assert result["url_valido"] is False

    def test_produto_completo(self):
        """Testa validação de produto completo."""
        produto = {
            "nome": "Tênis Nike",
            "preco": 299.99,
            "url": "https://www.amazon.com.br/tenis-nike/p/123",
            "imagem": "https://m.media-amazon.com/images/I/img1.jpg",
            "loja": "Amazon",
        }
        result = validar_produto(produto)
        assert result["url_valido"] is True
        assert result["imagem"] == "https://m.media-amazon.com/images/I/img1.jpg"


class TestEnviarOferta:
    """Testes para a função enviar_oferta."""

    @pytest.mark.asyncio
    async def test_pular_produto_sem_link_e_imagem(self):
        """Testa que produto sem link e sem imagem não é enviado."""
        produto = {
            "nome": "Produto Sem Link",
            "preco": 99.99,
            "url": "",
            "imagem": "",
            "loja": "Amazon",
            "tipo": "nova",
        }
        resultado = await enviar_oferta(produto)
        assert resultado is False

    @pytest.mark.asyncio
    async def test_enviar_produto_com_link(self):
        """Testa que produto com link é enviado."""
        produto = {
            "nome": "Produto com Link",
            "preco": 199.99,
            "url": "https://www.amazon.com.br/produto/123",
            "imagem": "",
            "loja": "Amazon",
            "tipo": "nova",
        }
        with patch("scripts.send_telegram.enviar_mensagem", new_callable=AsyncMock, return_value=True), \
             patch("scripts.send_telegram.verificar_url", new_callable=AsyncMock, return_value=True):
            resultado = await enviar_oferta(produto)
            assert resultado is True

    @pytest.mark.asyncio
    async def test_enviar_produto_com_imagem(self):
        """Testa que produto com imagem é enviado."""
        produto = {
            "nome": "Produto com Imagem",
            "preco": 299.99,
            "url": "",
            "imagem": "https://example.com/img.jpg",
            "loja": "Amazon",
            "tipo": "nova",
        }
        with patch("scripts.send_telegram.enviar_foto", new_callable=AsyncMock, return_value=True):
            resultado = await enviar_oferta(produto)
            assert resultado is True

    @pytest.mark.asyncio
    async def test_pular_produto_url_invalida_sem_imagem(self):
        """Testa que produto com URL inválida e sem imagem não é enviado."""
        produto = {
            "nome": "Produto URL Inválida",
            "preco": 99.99,
            "url": "https://amzn",
            "imagem": "",
            "loja": "Amazon",
            "tipo": "nova",
        }
        resultado = await enviar_oferta(produto)
        assert resultado is False

    @pytest.mark.asyncio
    async def test_pular_produto_link_quebrado(self):
        """Testa que produto com link quebrado (HEAD 404) não é enviado."""
        produto = {
            "nome": "Produto Link Quebrado",
            "preco": 149.99,
            "url": "https://www.amazon.com.br/produto/quebrado",
            "imagem": "",
            "loja": "Amazon",
            "tipo": "nova",
        }
        with patch("scripts.send_telegram.verificar_url", new_callable=AsyncMock, return_value=False):
            resultado = await enviar_oferta(produto)
            assert resultado is False

    @pytest.mark.asyncio
    async def test_enviar_queda_com_link_quebrado(self):
        """Testa que queda de preço é enviada mesmo com link quebrado."""
        produto = {
            "nome": "Produto Queda",
            "preco": 99.99,
            "url": "https://www.amazon.com.br/produto/quebrado",
            "imagem": "",
            "loja": "Amazon",
            "tipo": "queda",
        }
        with patch("scripts.send_telegram.enviar_mensagem", new_callable=AsyncMock, return_value=True):
            resultado = await enviar_oferta(produto)
            assert resultado is True
