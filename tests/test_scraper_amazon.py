"""Testes para o módulo scraper_amazon."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from scripts.scraper_amazon import AmazonScraper


@pytest.fixture
def scraper():
    """Cria instância do scraper para testes."""
    return AmazonScraper()


AMAZON_HTML_ITEM = """
<div data-component-type="s-search-result">
    <a href="/dp/B09/teste/ref=sr_1_1">
        <h2><span>Fone Bluetooth JBL Tune 510BT</span></h2>
    </a>
    <img class="s-image" src="https://m.media-amazon.com/images/I/61Teste.jpg" />
    <span class="a-price-whole">199<span class="a-price-decimal">,</span></span>
    <span class="a-price-fraction">99</span>
</div>
"""

AMAZON_HTML_COM_DESCONTO = """
<div data-component-type="s-search-result">
    <a href="/dp/B09/teste2">
        <h2><span>Mouse Gamer Logitech G203</span></h2>
    </a>
    <img class="s-image" src="https://m.media-amazon.com/images/I/71Teste.jpg" />
    <span class="a-price-whole">129<span class="a-price-decimal">,</span></span>
    <span class="a-price-fraction">99</span>
    <span class="a-price a-text-price">R$ 199,99</span>
</div>
"""

AMAZON_HTML_SEM_PRECO = """
<div data-component-type="s-search-result">
    <a href="/dp/B09/teste3">
        <h2><span>Produto Sem Preco</span></h2>
    </a>
</div>
"""

AMAZON_HTML_GREY_PIXEL = """
<div data-component-type="s-search-result">
    <a href="/dp/B09/teste4">
        <h2><span>Produto com Placeholder</span></h2>
    </a>
    <img class="s-image"
         src="https://m.media-amazon.com/images/G/32/grey-pixel.gif"
         srcset="https://m.media-amazon.com/images/I/81Real.jpg 1x" />
    <span class="a-price-whole">89<span class="a-price-decimal">,</span></span>
    <span class="a-price-fraction">90</span>
</div>
"""


class TestAmazonScraperInit:
    """Testes de inicialização."""

    def test_nome_loja(self, scraper):
        assert scraper.nome_loja == "Amazon"

    def test_emoji(self, scraper):
        assert scraper.emoji == "🟡"

    def test_dominio(self, scraper):
        assert scraper.dominio == "amazon.com.br"


class TestParseItem:
    """Testes para _parse_item."""

    def test_parse_item_basico(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert "JBL" in produto["nome"]
        assert produto["preco"] == 199.99
        assert "amazon.com.br" in produto["url"]

    def test_parse_item_com_desconto(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_COM_DESCONTO, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["preco"] == 129.99
        assert produto["preco_antigo"] == 199.99

    def test_parse_item_sem_preco(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_SEM_PRECO, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_grey_pixel_fallback_srcset(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_GREY_PIXEL, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert "81Real.jpg" in produto["imagem"]

    def test_parse_item_vazio(self, scraper):
        html = '<div data-component-type="s-search-result"></div>'
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_url_absoluta(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["url"].startswith("https://www.amazon.com.br")

    def test_parse_item_loja(self, scraper):
        item = BeautifulSoup(AMAZON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto["loja"] == "Amazon"


class TestBuscar:
    """Testes para o método buscar."""

    @patch("scripts.scraper_amazon.cloudscraper")
    def test_buscar_retorna_lista(self, mock_cs, scraper):
        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_cs.create_scraper.return_value.get.return_value = mock_resp

        resultado = scraper.buscar("fone bluetooth")
        assert isinstance(resultado, list)

    def test_buscar_erro_retorne_vazio(self, scraper):
        scraper.scraper = MagicMock()
        scraper.scraper.get.side_effect = Exception("timeout")
        resultado = scraper.buscar("teste")
        assert resultado == []

    @patch("scripts.scraper_amazon.cloudscraper")
    def test_buscar_com_max_preco(self, mock_cs, scraper):
        mock_resp = MagicMock()
        mock_resp.text = AMAZON_HTML_ITEM
        mock_resp.raise_for_status = MagicMock()
        mock_cs.create_scraper.return_value.get.return_value = mock_resp

        resultado = scraper.buscar("teste", max_preco=100.0)
        assert isinstance(resultado, list)


class TestConveniencia:
    """Testes para a função de conveniência."""

    def test_buscar_produtos(self):
        from scripts.scraper_amazon import buscar_produtos
        with patch.object(AmazonScraper, "buscar", return_value=[]) as mock:
            resultado = buscar_produtos("fone bluetooth")
            assert isinstance(resultado, list)
            mock.assert_called_once_with("fone bluetooth", None)
