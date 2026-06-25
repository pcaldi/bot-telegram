"""Testes para o módulo commands."""

import pytest
import scripts.commands as cmds
from scripts.commands import _handle_add, _handle_remove, _handle_list


@pytest.fixture(autouse=True)
def reset_custom():
    """Reset custom products before each test."""
    cmds._custom_products = []
    yield
    cmds._custom_products = []


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
