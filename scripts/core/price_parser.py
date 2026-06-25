"""Funções para parse e formatação de preços.

Fornece utilitários para converter textos de preços em floats e formatar valores.
"""

import re
from typing import Optional


def parse_preco(texto: Optional[str]) -> float:
    """Converte um texto de preço em float.

    Suporta formatos brasileiros (1.299,99) e internacionais (1,299.99).

    Args:
        texto: Texto contendo o preço (ex: "R$ 1.299,99", "1299.99", "R$ 199")

    Returns:
        Preço como float, ou 0.0 se não conseguir converter

    Exemplos:
        >>> parse_preco("R$ 199,99")
        199.99
        >>> parse_preco("R$ 1.299,99")
        1299.99
        >>> parse_preco("299.99")
        299.99
        >>> parse_preco("")
        0.0
        >>> parse_preco(None)
        0.0
    """
    if not texto:
        return 0.0

    # Remove caracteres não numéricos, exceto vírgula e ponto
    texto = str(texto).strip()
    texto = re.sub(r'[^\d.,]', '', texto)

    if not texto:
        return 0.0

    # Se tem vírgula, assume formato brasileiro (1.299,99)
    if ',' in texto:
        # Remove pontos de milhar e substitui vírgula por ponto
        texto = texto.replace('.', '').replace(',', '.')
    # Se tem ponto mas é só um, verifica se é decimal ou milhar
    elif '.' in texto:
        partes = texto.split('.')
        # Se tem mais de 2 partes, são pontos de milhar
        if len(partes) > 2:
            texto = ''.join(partes)
        # Se a parte decimal tem mais de 2 dígitos, provavelmente é milhar
        elif len(partes[-1]) > 2:
            texto = texto.replace('.', '')

    try:
        return float(texto)
    except (ValueError, TypeError):
        return 0.0


def formatar_preco(valor: float) -> str:
    """Formata um float como preço brasileiro.

    Args:
        valor: Valor a ser formatado

    Returns:
        Preço formatado (ex: "R$ 1.299,99")

    Exemplos:
        >>> formatar_preco(199.99)
        'R$ 199,99'
        >>> formatar_preco(1299.99)
        'R$ 1.299,99'
        >>> formatar_preco(0)
        'R$ 0,00'
    """
    texto = f"{valor:,.2f}"
    # Troca vírgula por X, ponto por vírgula, X por ponto (formato BR)
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def calcular_desconto(preco_atual: float, preco_antigo: float) -> Optional[int]:
    """Calcula o percentual de desconto.

    Args:
        preco_atual: Preço atual do produto
        preco_antigo: Preço anterior do produto

    Returns:
        Percentual de desconto (0-100), ou None se não houver desconto

    Exemplos:
        >>> calcular_desconto(349.99, 599.99)
        41
        >>> calcular_desconto(100.00, 100.00)
        0
        >>> calcular_desconto(100.00, 50.00)
        0
    """
    if preco_antigo <= 0 or preco_atual >= preco_antigo:
        return 0
    return int((1 - preco_atual / preco_antigo) * 100)


def calcular_economia(preco_atual: float, preco_antigo: float) -> float:
    """Calcula o valor economizado.

    Args:
        preco_atual: Preço atual do produto
        preco_antigo: Preço anterior do produto

    Returns:
        Valor economizado em reais

    Exemplos:
        >>> calcular_economia(349.99, 599.99)
        250.0
        >>> calcular_economia(100.00, 100.00)
        0.0
    """
    if preco_antigo <= preco_atual:
        return 0.0
    return round(preco_antigo - preco_atual, 2)
