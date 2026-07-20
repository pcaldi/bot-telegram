"""Testes para o módulo scraper_growth."""

import pytest
from unittest.mock import MagicMock, patch
from scripts.scraper_growth import GrowthScraper


@pytest.fixture
def scraper():
    """Cria instância do scraper para testes."""
    return GrowthScraper()


class TestGrowthScraperInit:
    """Testes de inicialização."""

    def test_nome_loja(self, scraper):
        assert scraper.nome_loja == "Growth"

    def test_emoji(self, scraper):
        assert scraper.emoji == "💪"

    def test_dominio(self, scraper):
        assert scraper.dominio == "gsuplementos.com.br"

    def test_base_url(self, scraper):
        assert scraper.base_url == "https://www.gsuplementos.com.br"

    def test_known_products(self, scraper):
        assert "whey protein concentrado 1kg" in scraper.known_products
        assert "creatina monohidratada 250g" in scraper.known_products


class TestBuscar:
    """Testes para o método buscar."""

    @patch("scripts.scraper_growth.BrowserManager")
    def test_buscar_retorna_lista(self, mock_mgr, scraper):
        mock_page = MagicMock()
        mock_page.context.new_page.return_value = mock_page
        mock_mgr.get.return_value.new_page.return_value = mock_page

        with patch.object(scraper, "_scrape", return_value=[]):
            resultado = scraper.buscar("whey protein")
            assert isinstance(resultado, list)

    @patch("scripts.scraper_growth.BrowserManager")
    def test_buscar_erro_retorna_vazio(self, mock_mgr, scraper):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("browser error")
        mock_mgr.get.return_value.new_page.return_value = mock_page
        resultado = scraper.buscar("teste")
        assert resultado == []


class TestConveniencia:
    """Testes para a função de conveniência."""

    def test_buscar_produtos_sem_context(self):
        from scripts.scraper_growth import buscar_produtos
        with patch.object(GrowthScraper, "buscar", return_value=[]) as mock:
            resultado = buscar_produtos("whey protein")
            assert isinstance(resultado, list)
            mock.assert_called_once_with("whey protein", None)

    def test_buscar_produtos_com_context(self):
        from scripts.scraper_growth import buscar_produtos
        mock_ctx = MagicMock()
        with patch.object(GrowthScraper, "_scrape", return_value=[]) as mock:
            resultado = buscar_produtos("whey protein", context=mock_ctx)
            assert isinstance(resultado, list)
