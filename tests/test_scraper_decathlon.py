"""Testes para o módulo scraper_decathlon."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from scripts.scraper_decathlon import DecathlonScraper


@pytest.fixture
def scraper():
    """Cria instância do scraper para testes."""
    return DecathlonScraper()


DECATHLON_HTML_ITEM = """
<div class="product-card">
    <a href="/p/tênis-nike-air-max-90/12345">
        <img src="https://contents.mediadecathlon.com/p123/teste.jpg" />
        <span class="brand">Nike</span>
        <span>Tênis Nike Air Max 90 Masculino</span>
        <span>R$ 399,99</span>
    </a>
</div>
"""

DECATHLON_HTML_COM_DESCONTO = """
<div class="product-card">
    <a href="/p/tenis-asics/67890">
        <img src="https://contents.mediadecathlon.com/p456/teste2.jpg" />
        <span class="brand">ASICS</span>
        <span>Tênis ASICS Gel-Kayano</span>
        <span>R$ 499,99</span>
        <span>R$ 699,99</span>
    </a>
</div>
"""

DECATHLON_HTML_SEM_PRECO = """
<div class="product-card">
    <a href="/p/produto/99999">
        <span class="brand">Teste</span>
        <span>Produto Sem Preço</span>
    </a>
</div>
"""


class TestDecathlonScraperInit:
    """Testes de inicialização."""

    def test_nome_loja(self, scraper):
        assert scraper.nome_loja == "Decathlon"

    def test_emoji(self, scraper):
        assert scraper.emoji == "🔵"

    def test_dominio(self, scraper):
        assert scraper.dominio == "decathlon.com.br"


class TestParseItem:
    """Testes para _parse_item."""

    def test_parse_item_basico(self, scraper):
        item = BeautifulSoup(DECATHLON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert "Nike" in produto["nome"]
        assert produto["preco"] == 399.99
        assert "decathlon.com.br" in produto["url"]

    def test_parse_item_com_desconto(self, scraper):
        item = BeautifulSoup(DECATHLON_HTML_COM_DESCONTO, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["preco"] == 499.99
        assert produto["preco_antigo"] == 699.99

    def test_parse_item_sem_preco(self, scraper):
        item = BeautifulSoup(DECATHLON_HTML_SEM_PRECO, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_vazio(self, scraper):
        html = '<div class="product-card"></div>'
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_url_absoluta(self, scraper):
        item = BeautifulSoup(DECATHLON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["url"].startswith("https://www.decathlon.com.br")

    def test_parse_item_loja(self, scraper):
        item = BeautifulSoup(DECATHLON_HTML_ITEM, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto["loja"] == "Decathlon"


class TestBuscar:
    """Testes para o método buscar."""

    @patch("scripts.scraper_decathlon.BrowserManager")
    def test_buscar_retorna_lista(self, mock_mgr, scraper):
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"
        mock_mgr.get.return_value.new_page.return_value = mock_page

        resultado = scraper.buscar("tênis corrida")
        assert isinstance(resultado, list)

    @patch("scripts.scraper_decathlon.BrowserManager")
    def test_buscar_erro_retorna_vazio(self, mock_mgr, scraper):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("browser error")
        mock_mgr.get.return_value.new_page.return_value = mock_page
        resultado = scraper.buscar("teste")
        assert resultado == []


class TestConveniencia:
    """Testes para a função de conveniência."""

    def test_buscar_produtos(self):
        from scripts.scraper_decathlon import buscar_produtos
        with patch.object(DecathlonScraper, "buscar", return_value=[]) as mock:
            resultado = buscar_produtos("tênis corrida")
            assert isinstance(resultado, list)
            mock.assert_called_once_with("tênis corrida", None)
