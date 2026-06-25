"""Classe abstrata base para todos os scrapers do bot de ofertas.

Fornece uma interface padrão e utilitários compartilhados para scrapers de diferentes lojas.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

log = logging.getLogger("bot-ofertas")


class BaseScraper(ABC):
    """Classe abstrata base para scrapers de e-commerce.

    Todos os scrapers devem herdar desta classe e implementar o método buscar().
    """

    def __init__(self, nome_loja: str, emoji: str, dominio: str):
        """Inicializa o scraper.

        Args:
            nome_loja: Nome da loja (ex: "Amazon", "Growth")
            emoji: Emoji representativo da loja (ex: "🟡")
            dominio: Domínio do site (ex: "amazon.com.br")
        """
        self.nome_loja = nome_loja
        self.emoji = emoji
        self.dominio = dominio
        self.log = logging.getLogger(f"bot-ofertas.{nome_loja.lower()}")

    @abstractmethod
    def buscar(self, termo: str, max_preco: Optional[float] = None) -> list:
        """Busca produtos na loja.

        Args:
            termo: Termo de busca (ex: "tênis nike")
            max_preco: Preço máximo para filtrar resultados

        Returns:
            Lista de dicionários com os produtos encontrados.
            Cada dicionário deve conter:
                - nome: Nome do produto
                - preco: Preço atual
                - preco_antigo: Preço anterior (opcional)
                - url: Link do produto
                - loja: Nome da loja
                - imagem: URL da imagem (opcional)
                - frete: Informação de frete (opcional)
        """
        pass

    def criar_produto(
        self,
        nome: str,
        preco: float,
        url: str,
        preco_antigo: Optional[float] = None,
        imagem: Optional[str] = None,
        frete: Optional[str] = None,
    ) -> dict:
        """Cria um dicionário de produto padronizado.

        Args:
            nome: Nome do produto
            preco: Preço atual
            url: Link do produto
            preco_antigo: Preço anterior (opcional)
            imagem: URL da imagem (opcional)
            frete: Informação de frete (opcional)

        Returns:
            Dicionário com os dados do produto
        """
        return {
            "nome": nome,
            "preco": preco,
            "preco_antigo": preco_antigo,
            "url": url,
            "loja": self.nome_loja,
            "imagem": imagem or "",
            "frete": frete or "Consulta",
        }

    def filtrar_por_preco(self, produtos: list, max_preco: Optional[float]) -> list:
        """Filtra produtos por preço máximo.

        Args:
            produtos: Lista de produtos
            max_preco: Preço máximo (None para não filtrar)

        Returns:
            Lista de produtos com preço <= max_preco
        """
        if max_preco is None:
            return produtos
        return [p for p in produtos if p.get("preco", 0) <= max_preco]

    def tratar_erro(self, mensagem: str, erro: Exception) -> None:
        """Registra erros de forma padronizada.

        Args:
            mensagem: Descrição do erro
            erro: Exceção capturada
        """
        self.log.warning("%s: %s", mensagem, erro)
