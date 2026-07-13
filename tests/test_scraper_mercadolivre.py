"""Testes para o módulo scraper_mercadolivre."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from scripts.scraper_mercadolivre import MercadoLivreScraper


@pytest.fixture
def scraper():
    """Cria instância do scraper para testes."""
    return MercadoLivreScraper()


class TestMercadoLivreScraperInit:
    """Testes de inicialização do MercadoLivreScraper."""

    def test_nome_loja(self, scraper):
        """Testa nome da loja."""
        assert scraper.nome_loja == "Mercado Livre"

    def test_emoji(self, scraper):
        """Testa emoji da loja."""
        assert scraper.emoji == "🟠"

    def test_dominio(self, scraper):
        """Testa domínio da loja."""
        assert scraper.dominio == "mercadolivre.com.br"


class TestParseItem:
    """Testes para o método _parse_item."""

    def test_parse_item_basico(self, scraper):
        """Testa parse de item básico."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("Tênis Nike Air Max", "https://produto.mercadolivre.com.br/MLB-123"),
            "span.andes-money-amount__fraction": _mock_element("599"),
            "span.andes-money-amount__cents": _mock_element("99"),
            "img.poly-component__picture": _mock_element(None, "https://http2.mlstatic.com/img.webp"),
            "span.poly-component__installments": _mock_element(None),
            "span.poly-component__shipping": _mock_element(None),
            "span.poly-component__discount": _mock_element(None),
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is not None
        assert "Nike" in produto["nome"]
        assert produto["preco"] == 599.99
        assert "mercadolivre.com.br" in produto["url"]
        assert "tag=pcaldi" in produto["url"]

    def test_parse_item_com_desconto(self, scraper):
        """Testa parse de item com desconto."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("Tênis com Desconto", "https://produto.mercadolivre.com.br/MLB-456"),
            "span.andes-money-amount__fraction": _mock_element("299"),
            "span.andes-money-amount__cents": _mock_element("99"),
            "img.poly-component__picture": _mock_element(None, "https://http2.mlstatic.com/img.webp"),
            "span.poly-component__installments": _mock_element(None),
            "span.poly-component__shipping": _mock_element(None),
            "span.poly-component__discount": _mock_element("20% OFF"),
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is not None
        assert produto["preco"] == 299.99
        assert produto["preco_antigo"] is not None

    def test_parse_item_sem_preco(self, scraper):
        """Testa parse de item sem preço retorna None."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("Produto Sem Preço", "https://produto.mercadolivre.com.br/MLB-789"),
            "span.andes-money-amount__fraction": None,
            "span.andes-money-amount__cents": None,
            "img.poly-component__picture": None,
            "span.poly-component__installments": None,
            "span.poly-component__shipping": None,
            "span.poly-component__discount": None,
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is None

    def test_parse_item_sem_nome(self, scraper):
        """Testa parse de item sem nome retorna None."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("", ""),
            "span.andes-money-amount__fraction": _mock_element("199"),
            "span.andes-money-amount__cents": _mock_element("99"),
            "img.poly-component__picture": _mock_element(None),
            "span.poly-component__installments": _mock_element(None),
            "span.poly-component__shipping": _mock_element(None),
            "span.poly-component__discount": _mock_element(None),
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is None

    def test_parse_item_vazio(self, scraper):
        """Testa parse de item vazio retorna None."""
        mock_item = MagicMock()
        mock_item.query_selector.return_value = None
        produto = scraper._parse_item(mock_item)
        assert produto is None

    def test_parse_item_com_parcelamento(self, scraper):
        """Testa extração de parcelamento."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("Produto Parcelado", "https://produto.mercadolivre.com.br/MLB-111"),
            "span.andes-money-amount__fraction": _mock_element("199"),
            "span.andes-money-amount__cents": _mock_element("99"),
            "img.poly-component__picture": _mock_element(None, "https://http2.mlstatic.com/img.webp"),
            "span.poly-component__installments": _mock_element("em 10x de R$19,99"),
            "span.poly-component__shipping": _mock_element(None),
            "span.poly-component__discount": _mock_element(None),
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is not None
        assert produto["parcelamento"] == "em 10x de R$19,99"

    def test_parse_item_frete_gratis(self, scraper):
        """Testa extração de frete grátis."""
        mock_item = MagicMock()
        mock_item.query_selector.side_effect = lambda sel: {
            "a.poly-component__title": _mock_element("Produto Frete", "https://produto.mercadolivre.com.br/MLB-222"),
            "span.andes-money-amount__fraction": _mock_element("99"),
            "span.andes-money-amount__cents": _mock_element("90"),
            "img.poly-component__picture": _mock_element(None, "https://http2.mlstatic.com/img.webp"),
            "span.poly-component__installments": _mock_element(None),
            "span.poly-component__shipping": _mock_element("Frete grátis"),
            "span.poly-component__discount": _mock_element(None),
        }.get(sel)
        produto = scraper._parse_item(mock_item)
        assert produto is not None
        assert produto["frete"] == "Frete grátis"


class TestBuscar:
    """Testes para o método buscar."""

    def test_buscar_retorna_lista(self, scraper):
        """Testa que buscar retorna uma lista."""
        with patch('scripts.scraper_mercadolivre.BrowserManager') as mock_mgr:
            mock_page = MagicMock()
            mock_page.query_selector_all.return_value = []
            mock_mgr.return_value.new_page.return_value = mock_page
            resultado = scraper.buscar("nike air max")
            assert isinstance(resultado, list)

    def test_buscar_com_max_preco(self, scraper):
        """Testa busca com filtro de preço máximo."""
        with patch('scripts.scraper_mercadolivre.BrowserManager') as mock_mgr:
            mock_page = MagicMock()
            mock_page.query_selector_all.return_value = []
            mock_mgr.return_value.new_page.return_value = mock_page
            resultado = scraper.buscar("nike air max", max_preco=200.0)
            assert isinstance(resultado, list)


class TestConveniencia:
    """Testes para a função de conveniência."""

    def test_buscar_produtos(self):
        """Testa função de conveniência buscar_produtos."""
        from scripts.scraper_mercadolivre import buscar_produtos
        with patch.object(MercadoLivreScraper, 'buscar', return_value=[]) as mock:
            resultado = buscar_produtos("nike air max")
            assert isinstance(resultado, list)
            mock.assert_called_once_with("nike air max", None)


def _mock_element(text=None, href=None):
    """Cria mock de elemento Playwright."""
    el = MagicMock()
    if text is not None:
        el.inner_text.return_value = text
    if href is not None:
        el.get_attribute.return_value = href
    return el
