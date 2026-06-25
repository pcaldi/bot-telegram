"""Testes para o módulo price_parser."""

import pytest
from scripts.core.price_parser import (
    parse_preco,
    formatar_preco,
    calcular_desconto,
    calcular_economia,
)


class TestParsePreco:
    """Testes para a função parse_preco."""

    def test_parse_preco_basico(self):
        """Testa parse de preço básico."""
        assert parse_preco("R$ 199,99") == 199.99

    def test_parse_preco_ponto_milhar(self):
        """Testa parse de preço com ponto de milhar."""
        assert parse_preco("R$ 1.299,99") == 1299.99

    def test_parse_preco_sem_prefixo(self):
        """Testa parse de preço sem prefixo R$."""
        assert parse_preco("299,99") == 299.99

    def test_parse_preco_vazio(self):
        """Testa parse de string vazia."""
        assert parse_preco("") == 0.0

    def test_parse_preco_none(self):
        """Testa parse de None."""
        assert parse_preco(None) == 0.0

    def test_parse_preco_zero(self):
        """Testa parse de zero."""
        assert parse_preco("R$ 0,00") == 0.0

    def test_parse_preco_inteiro(self):
        """Testa parse de preço inteiro."""
        assert parse_preco("R$ 199") == 199.0

    def test_parse_preco_grande(self):
        """Testa parse de preço grande."""
        assert parse_preco("R$ 9.999,99") == 9999.99

    def test_parse_preco_texto_lixo(self):
        """Testa parse com texto inválido."""
        assert parse_preco("abc") == 0.0

    def test_parse_preco_float(self):
        """Testa parse de float."""
        assert parse_preco(199.99) == 199.99

    def test_parse_preco_int(self):
        """Testa parse de int."""
        assert parse_preco(199) == 199.0


class TestFormatarPreco:
    """Testes para a função formatar_preco."""

    def test_formatar_preco_basico(self):
        """Testa formatação básica."""
        assert formatar_preco(199.99) == "R$ 199,99"

    def test_formatar_preco_ponto_milhar(self):
        """Testa formatação com ponto de milhar."""
        assert formatar_preco(1299.99) == "R$ 1.299,99"

    def test_formatar_preco_zero(self):
        """Testa formatação de zero."""
        assert formatar_preco(0) == "R$ 0,00"

    def test_formatar_preco_grande(self):
        """Testa formatação de preço grande."""
        assert formatar_preco(9999.99) == "R$ 9.999,99"

    def test_formatar_preco_decimal(self):
        """Testa formatação com decimal."""
        assert formatar_preco(199.50) == "R$ 199,50"


class TestCalcularDesconto:
    """Testes para a função calcular_desconto."""

    def test_desconto_basico(self):
        """Testa cálculo de desconto básico."""
        assert calcular_desconto(349.99, 599.99) == 41

    def test_desconto_zero(self):
        """Testa desconto quando não há desconto."""
        assert calcular_desconto(100.00, 100.00) == 0

    def test_desconto_inverso(self):
        """Testa quando preço atual é maior que anterior."""
        assert calcular_desconto(150.00, 100.00) == 0

    def test_desconto_grande(self):
        """Testa desconto grande."""
        assert calcular_desconto(100.00, 500.00) == 80

    def test_desconto_pequeno(self):
        """Testa desconto pequeno (99/100 para evitar imprecisão de float)."""
        assert calcular_desconto(99.00, 100.00) == 1


class TestCalcularEconomia:
    """Testes para a função calcular_economia."""

    def test_economia_basica(self):
        """Testa cálculo de economia básica."""
        assert calcular_economia(349.99, 599.99) == 250.0

    def test_economia_zero(self):
        """Testa economia quando não há desconto."""
        assert calcular_economia(100.00, 100.00) == 0.0

    def test_economia_inversa(self):
        """Testa quando preço atual é maior que anterior."""
        assert calcular_economia(150.00, 100.00) == 0.0

    def test_economia_grande(self):
        """Testa economia grande."""
        assert calcular_economia(100.00, 500.00) == 400.0

    def test_economia_precisao(self):
        """Testa precisão do cálculo."""
        assert calcular_economia(33.33, 100.00) == 66.67
