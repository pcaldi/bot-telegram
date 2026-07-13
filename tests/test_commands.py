"""Testes para o módulo commands."""

import pytest
import asyncio
import concurrent.futures
from unittest.mock import patch, MagicMock, AsyncMock
import scripts.commands as cmds
from scripts.commands import (
    _handle_add, _handle_remove, _handle_list, _handle_status,
    _handle_search, _handle_category, _run_scrapers_sync,
    CATEGORY_COMMANDS,
)


def _run_async(coro):
    """Executa coroutine em event loop isolado (evita conflito com Playwright)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def reset_custom():
    """Reset custom products before each test."""
    cmds._custom_products = []
    yield
    cmds._custom_products = []


def _mock_loop_with_results(produtos):
    """Cria um mock de event loop que retorna produtos no run_in_executor."""
    mock_loop = AsyncMock()
    mock_loop.run_in_executor = AsyncMock(return_value=produtos)
    return mock_loop


class TestHandleAdd:
    """Testes para o comando /add."""

    def test_add_basico(self):
        """Testa adição básica de produto."""
        resultado = _handle_add("air fryer 500")
        assert "Adicionado" in resultado
        assert "Air Fryer" in resultado

    def test_add_preco_default(self):
        """Testa adição com preço padrão."""
        resultado = _handle_add("notebook dell")
        assert "Adicionado" in resultado
        assert "500" in resultado

    def test_add_com_preco(self):
        """Testa adição com preço específico."""
        resultado = _handle_add("mouse gamer 200")
        assert "Adicionado" in resultado
        assert "200" in resultado

    def test_add_duplicado(self):
        """Testa adição de produto duplicado."""
        _handle_add("air fryer 500")
        resultado = _handle_add("air fryer 500")
        assert "Já existe" in resultado

    def test_add_vazio(self):
        """Testa adição sem argumentos."""
        resultado = _handle_add("")
        assert "Uso:" in resultado


class TestHandleRemove:
    """Testes para o comando /remove."""

    def test_remove_por_indice(self):
        """Testa remoção por índice."""
        _handle_add("produto 1")
        _handle_add("produto 2")
        resultado = _handle_remove("1")
        assert "Removido" in resultado

    def test_remove_invalido(self):
        """Testa remoção com índice inválido."""
        resultado = _handle_remove("999")
        assert "inválido" in resultado

    def test_remove_nao_encontrado(self):
        """Testa remoção de produto inexistente."""
        resultado = _handle_remove("produto_inexistente")
        assert "Não encontrado" in resultado

    def test_remove_vazio(self):
        """Testa remoção sem argumentos."""
        resultado = _handle_remove("")
        assert "Uso:" in resultado


class TestHandleList:
    """Testes para o comando /list."""

    def test_list_vazio(self):
        """Testa listagem vazia."""
        resultado = _handle_list()
        assert "Nenhum produto" in resultado

    def test_list_com_produtos(self):
        """Testa listagem com produtos."""
        _handle_add("air fryer 500")
        _handle_add("notebook dell 800")
        resultado = _handle_list()
        assert "1." in resultado
        assert "2." in resultado

    def test_list_titulo(self):
        """Testa se listagem tem título."""
        _handle_add("produto teste")
        resultado = _handle_list()
        assert "Produtos monitorados" in resultado


class TestHandleStatus:
    """Testes para o comando /status."""

    def test_status_retorna_estatisticas(self):
        """Testa que /status retorna estatísticas."""
        resultado = _handle_status()
        assert "Status do Bot" in resultado

    def test_status_mostra_produtos_custom(self):
        """Testa que /status mostra produtos custom."""
        _handle_add("produto teste")
        resultado = _handle_status()
        assert "Produtos custom" in resultado


class TestRunScrapersSync:
    """Testes para _run_scrapers_sync."""

    def test_busca_com_mock(self):
        """Testa que scrapers são chamados corretamente."""
        mock_scraper = MagicMock()
        mock_scraper.buscar.return_value = [
            {"nome": "Produto Teste", "preco": 99.9, "url": "https://example.com", "loja": "Amazon"}
        ]
        with patch("scripts.commands._get_scrapers") as mock_get:
            mock_get.return_value = ({"Amazon": lambda: mock_scraper}, lambda *a, **k: {})
            result = _run_scrapers_sync(["teste"], ["Amazon"], 3)
            mock_scraper.buscar.assert_called_once_with("teste", None)
            assert len(result) == 1
            assert result[0]["nome"] == "Produto Teste"

    def test_busca_loja_inexistente(self):
        """Testa busca com loja que não existe no mapa."""
        result = _run_scrapers_sync(["teste"], ["LojaFantasma"], 3)
        assert result == []


class TestHandleSearch:
    """Testes para o comando /search."""

    def test_search_vazio(self):
        """Testa /search sem argumentos."""
        mock_send = AsyncMock()
        with patch("scripts.commands._send_message", mock_send):
            _run_async(_handle_search("token", 123, ""))
            mock_send.assert_called_once()
            assert "Uso:" in mock_send.call_args[0][2]

    def test_search_com_resultados(self):
        """Testa /search com resultados."""
        produtos = [{"nome": "Nike Air", "preco": 299.9, "url": "https://example.com", "loja": "Amazon"}]
        mock_send = AsyncMock()
        mock_loop = _mock_loop_with_results(produtos)
        with patch("scripts.commands._send_message", mock_send), \
             patch("scripts.commands._run_scrapers_sync", return_value=produtos), \
             patch("scripts.commands.asyncio.get_running_loop", return_value=mock_loop):
            _run_async(_handle_search("token", 123, "nike air max"))
            assert mock_send.call_count >= 3

    def test_search_com_loja(self):
        """Testa /search com filtro de loja."""
        mock_send = AsyncMock()
        mock_loop = _mock_loop_with_results([])
        with patch("scripts.commands._send_message", mock_send), \
             patch("scripts.commands._run_scrapers_sync", return_value=[]), \
             patch("scripts.commands.asyncio.get_running_loop", return_value=mock_loop):
            _run_async(_handle_search("token", 123, "nike amazon"))
            mock_send.assert_called()
            first_call_text = mock_send.call_args_list[0][0][2]
            assert "Amazon" in first_call_text


class TestHandleCategory:
    """Testes para comandos de categoria."""

    def test_categoria_corrida(self):
        """Testa comando /corrida."""
        mock_send = AsyncMock()
        mock_loop = _mock_loop_with_results([])
        with patch("scripts.commands._send_message", mock_send), \
             patch("scripts.commands._run_scrapers_sync", return_value=[]), \
             patch("scripts.commands.asyncio.get_running_loop", return_value=mock_loop):
            _run_async(_handle_category("token", 123, "/corrida"))
            mock_send.assert_called()
            first_text = mock_send.call_args_list[0][0][2]
            assert "corrida" in first_text.lower()

    def test_categoria_com_resultados(self):
        """Testa categoria com resultados encontrados."""
        produtos = [
            {"nome": "Tênis Corrida", "preco": 350.0, "url": "https://example.com", "loja": "Amazon"},
            {"nome": "Tênis Running", "preco": 280.0, "url": "https://example2.com", "loja": "Decathlon"},
        ]
        mock_send = AsyncMock()
        mock_loop = _mock_loop_with_results(produtos)
        with patch("scripts.commands._send_message", mock_send), \
             patch("scripts.commands._run_scrapers_sync", return_value=produtos), \
             patch("scripts.commands.asyncio.get_running_loop", return_value=mock_loop):
            _run_async(_handle_category("token", 123, "/corrida"))
            assert mock_send.call_count >= 3


class TestCategoryCommands:
    """Testes para o mapeamento CATEGORY_COMMANDS."""

    def test_corrida_existe(self):
        """Testa que /corrida está mapeado."""
        assert "/corrida" in CATEGORY_COMMANDS
        assert "termos" in CATEGORY_COMMANDS["/corrida"]
        assert "lojas" in CATEGORY_COMMANDS["/corrida"]

    def test_suplementos_existe(self):
        """Testa que /suplementos está mapeado."""
        assert "/suplementos" in CATEGORY_COMMANDS
        assert len(CATEGORY_COMMANDS["/suplementos"]["termos"]) > 0

    def test_eletronicos_existe(self):
        """Testa que /eletronicos está mapeado."""
        assert "/eletronicos" in CATEGORY_COMMANDS
