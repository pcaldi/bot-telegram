"""Módulo core do bot de ofertas.

Contém classes base e utilitários compartilhados entre todos os scrapers.
"""

from scripts.core.base_scraper import BaseScraper
from scripts.core.price_parser import parse_preco, formatar_preco
from scripts.core.database import Database

__all__ = ["BaseScraper", "parse_preco", "formatar_preco", "Database"]
