"""Testes para o módulo scraper_procorrer."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from scripts.scraper_procorrer import ProcorrerScraper


@pytest.fixture
def scraper():
    """Cria instância do scraper para testes."""
    return ProcorrerScraper()


class TestProcorrerScraperInit:
    """Testes de inicialização do ProcorrerScraper."""

    def test_nome_loja(self, scraper):
        """Testa nome da loja."""
        assert scraper.nome_loja == "Procorrer"

    def test_emoji(self, scraper):
        """Testa emoji da loja."""
        assert scraper.emoji == "👟"

    def test_dominio(self, scraper):
        """Testa domínio da loja."""
        assert scraper.dominio == "procorrer.com.br"

    def test_base_url(self, scraper):
        """Testa URL base."""
        assert scraper.base_url == "https://www.procorrer.com.br"


class TestParseItem:
    """Testes para o método _parse_item."""

    def test_parse_item_basico(self, scraper):
        """Testa parse de item básico."""
        html = """
        <div class="product-card">
            <a href="/tenis-nike-air-max">
                <img src="https://example.com/img.jpg" />
                <span>Tênis Nike Air Max 90</span>
                <span>R$ 399,99</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert "Nike" in produto["nome"]
        assert produto["preco"] == 399.99
        assert "procorrer.com.br" in produto["url"]

    def test_parse_item_com_desconto(self, scraper):
        """Testa parse de item com desconto."""
        html = """
        <div class="product-card">
            <a href="/tenis-asics">
                <img src="https://example.com/img.jpg" />
                <span>Tênis ASICS Gel-Nimbus</span>
                <span>R$ 599,99</span>
                <span>R$ 799,99</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["preco"] == 599.99
        assert produto["preco_antigo"] == 799.99

    def test_parse_item_sem_preco(self, scraper):
        """Testa parse de item sem preço retorna None."""
        html = """
        <div class="product-card">
            <a href="/produto">
                <span>Produto Sem Preço</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_sem_nome(self, scraper):
        """Testa parse de item sem nome retorna None."""
        html = """
        <div class="product-card">
            <a href="/produto">
                <span>R$ 199,99</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_vazio(self, scraper):
        """Testa parse de item vazio retorna None."""
        html = '<div class="product-card"></div>'
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is None

    def test_parse_item_url_relativa(self, scraper):
        """Testa que URL relativa é convertida para absoluta."""
        html = """
        <div class="product-card">
            <a href="/tenis-procorrer">
                <span>Tênis Procorrer</span>
                <span>R$ 299,99</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert produto["url"].startswith("https://www.procorrer.com.br")

    def test_parse_item_imagem(self, scraper):
        """Testa extração de imagem."""
        html = """
        <div class="product-card">
            <a href="/tenis">
                <img src="https://example.com/foto.jpg" />
                <span>Tênis Teste</span>
                <span>R$ 199,99</span>
            </a>
        </div>
        """
        item = BeautifulSoup(html, "lxml").select_one("div")
        produto = scraper._parse_item(item)
        assert produto is not None
        assert "foto.jpg" in produto["imagem"]


class TestBuscar:
    """Testes para o método buscar."""

    @patch.object(ProcorrerScraper, '_parse_item')
    def test_buscar_retorna_lista(self, mock_parse, scraper):
        """Testa que buscar retorna uma lista."""
        mock_parse.return_value = None
        with patch('scripts.scraper_procorrer.BrowserManager') as mock_mgr:
            mock_page = MagicMock()
            mock_page.content.return_value = "<html></html>"
            mock_mgr.get.return_value.new_page.return_value = mock_page
            resultado = scraper.buscar("tênis")
            assert isinstance(resultado, list)

    def test_buscar_com_max_preco(self, scraper):
        """Testa busca com filtro de preço máximo."""
        with patch('scripts.scraper_procorrer.BrowserManager') as mock_mgr:
            mock_page = MagicMock()
            mock_page.content.return_value = "<html></html>"
            mock_mgr.get.return_value.new_page.return_value = mock_page
            resultado = scraper.buscar("tênis", max_preco=200.0)
            assert isinstance(resultado, list)


class TestConveniencia:
    """Testes para a função de conveniência."""

    def test_buscar_produtos(self):
        """Testa função de conveniência buscar_produtos."""
        from scripts.scraper_procorrer import buscar_produtos
        with patch.object(ProcorrerScraper, 'buscar', return_value=[]) as mock:
            resultado = buscar_produtos("tênis corrida")
            assert isinstance(resultado, list)
            mock.assert_called_once_with("tênis corrida", None)
