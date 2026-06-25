"""Gerenciamento do banco de dados SQLite.

Fornece a classe Database para persistência de ofertas, histórico de preços
e controle de ofertas enviadas ao Telegram.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger("bot-ofertas")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "ofertas.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ofertas (
    produto_id TEXT PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL,
    preco_atual REAL,
    preco_antigo REAL,
    loja TEXT NOT NULL,
    url TEXT,
    imagem TEXT,
    categoria TEXT,
    primeira_vista TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_vista TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historico_precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id TEXT NOT NULL,
    preco REAL NOT NULL,
    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES ofertas(produto_id)
);

CREATE TABLE IF NOT EXISTS ofertas_enviadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    preco_enviado REAL,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES ofertas(produto_id)
);

CREATE INDEX IF NOT EXISTS idx_historico_produto ON historico_precos(produto_id);
CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_precos(data_coleta);
CREATE INDEX IF NOT EXISTS idx_enviadas_produto ON ofertas_enviadas(produto_id);
"""


class Database:
    """Gerencia persistência de ofertas e histórico de preços."""

    def __init__(self, db_path: Optional[str] = None):
        """Inicializa conexão com o banco SQLite.

        Args:
            db_path: Caminho do banco. Usa o padrão se None. ":memory:" para banco em memória.
        """
        self.db_path = db_path or DB_PATH
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._criar_tabelas()

    def _criar_tabelas(self):
        """Cria as tabelas do schema."""
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self):
        """Fecha a conexão com o banco."""
        if self.conn:
            self.conn.close()

    def salvar_oferta(self, produto: dict) -> bool:
        """Salva ou atualiza uma oferta no banco.

        Args:
            produto: Dict com produto_id, nome, preco_atual, loja, etc.

        Returns:
            True se foi inserido, False se atualizado.
        """
        pid = produto.get("produto_id")
        if not pid:
            return False

        now = datetime.now().isoformat()
        existing = self.buscar_oferta(pid)

        if existing:
            self.conn.execute(
                """UPDATE ofertas
                   SET preco_atual=?, preco_antigo=?, nome=?, url=?, imagem=?,
                       categoria=?, ultima_vista=?
                   WHERE produto_id=?""",
                (
                    produto.get("preco_atual", existing["preco_atual"]),
                    produto.get("preco_antigo", existing.get("preco_antigo")),
                    produto.get("nome", existing["nome"]),
                    produto.get("url", existing.get("url")),
                    produto.get("imagem", existing.get("imagem")),
                    produto.get("categoria", existing.get("categoria")),
                    now,
                    pid,
                ),
            )
            self.conn.commit()
            return False
        else:
            self.conn.execute(
                """INSERT INTO ofertas
                   (produto_id, nome, preco_atual, preco_antigo, loja, url, imagem,
                    categoria, primeira_vista, ultima_vista)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pid,
                    produto.get("nome", ""),
                    produto.get("preco_atual"),
                    produto.get("preco_antigo"),
                    produto.get("loja", ""),
                    produto.get("url"),
                    produto.get("imagem"),
                    produto.get("categoria"),
                    now,
                    now,
                ),
            )
            self.conn.commit()
            return True

    def buscar_oferta(self, produto_id: str) -> Optional[dict]:
        """Busca uma oferta pelo ID.

        Args:
            produto_id: ID do produto.

        Returns:
            Dict com dados da oferta, ou None se não encontrar.
        """
        row = self.conn.execute(
            "SELECT * FROM ofertas WHERE produto_id=?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def atualizar_preco(self, produto_id: str, preco: float) -> bool:
        """Atualiza o preço de uma oferta e registra no histórico.

        Args:
            produto_id: ID do produto.
            preco: Novo preço.

        Returns:
            True se houve queda de preço.
        """
        oferta = self.buscar_oferta(produto_id)
        if not oferta:
            return False

        preco_antigo = oferta.get("preco_atual")
        self.conn.execute(
            "UPDATE ofertas SET preco_atual=?, preco_antigo=?, ultima_vista=? WHERE produto_id=?",
            (preco, preco_antigo, datetime.now().isoformat(), produto_id),
        )
        self.conn.commit()

        self.salvar_historico(produto_id, preco)

        return preco < preco_antigo if preco_antigo else False

    def salvar_historico(self, produto_id: str, preco: float):
        """Registra preço no histórico.

        Args:
            produto_id: ID do produto.
            preco: Preço coletado.
        """
        self.conn.execute(
            "INSERT INTO historico_precos (produto_id, preco) VALUES (?, ?)",
            (produto_id, preco),
        )
        self.conn.commit()

    def buscar_historico(self, produto_id: str, dias: Optional[int] = None) -> list:
        """Busca histórico de preços de um produto.

        Args:
            produto_id: ID do produto.
            dias: Filtrar últimos N dias. None = todo histórico.

        Returns:
            Lista de dicts com preco e data_coleta.
        """
        if dias:
            cutoff = (datetime.now() - timedelta(days=dias)).isoformat()
            rows = self.conn.execute(
                "SELECT preco, data_coleta FROM historico_precos "
                "WHERE produto_id=? AND data_coleta>=? ORDER BY data_coleta",
                (produto_id, cutoff),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT preco, data_coleta FROM historico_precos "
                "WHERE produto_id=? ORDER BY data_coleta",
                (produto_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def buscar_menor_preco(self, produto_id: str, dias: Optional[int] = None) -> Optional[float]:
        """Busca o menor preço registrado de um produto.

        Args:
            produto_id: ID do produto.
            dias: Filtrar últimos N dias. None = todo histórico.

        Returns:
            Menor preço, ou None se não houver histórico.
        """
        historico = self.buscar_historico(produto_id, dias)
        if not historico:
            return None
        return min(h["preco"] for h in historico)

    def buscar_por_loja(self, loja: str) -> list:
        """Busca todas as ofertas de uma loja.

        Args:
            loja: Nome da loja.

        Returns:
            Lista de ofertas da loja.
        """
        rows = self.conn.execute(
            "SELECT * FROM ofertas WHERE loja=? ORDER BY ultima_vista DESC",
            (loja,),
        ).fetchall()
        return [dict(r) for r in rows]

    def registrar_envio(self, produto_id: str, tipo: str, preco: float):
        """Registra envio de oferta ao Telegram.

        Args:
            produto_id: ID do produto.
            tipo: Tipo da oferta (nova/queda).
            preco: Preço enviado.
        """
        self.conn.execute(
            "INSERT INTO ofertas_enviadas (produto_id, tipo, preco_enviado) VALUES (?, ?, ?)",
            (produto_id, tipo, preco),
        )
        self.conn.commit()

    def buscar_enviados_recentemente(self, horas: int = 24) -> list:
        """Busca ofertas enviadas nas últimas N horas.

        Args:
            horas: Número de horas para buscar.

        Returns:
            Lista de ofertas enviadas.
        """
        cutoff = (datetime.now() - timedelta(hours=horas)).isoformat()
        rows = self.conn.execute(
            "SELECT * FROM ofertas_enviadas WHERE data_envio>=? ORDER BY data_envio DESC",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def atualizar_vista(self, produto_id: str):
        """Atualiza a data da última visualização de uma oferta.

        Args:
            produto_id: ID do produto.
        """
        self.conn.execute(
            "UPDATE ofertas SET ultima_vista=? WHERE produto_id=?",
            (datetime.now().isoformat(), produto_id),
        )
        self.conn.commit()

    def cleanup_historico(self, dias: int = 90):
        """Remove registros de histórico antigos.

        Args:
            dias: Manter apenas os últimos N dias.
        """
        cutoff = (datetime.now() - timedelta(days=dias)).isoformat()
        cursor = self.conn.execute(
            "DELETE FROM historico_precos WHERE data_coleta<?", (cutoff,)
        )
        removidos = cursor.rowcount
        self.conn.commit()
        if removidos > 0:
            log.info("Cleanup histórico: %d registros removidos (>%d dias)", removidos, dias)
        return removidos

    def stats(self) -> dict:
        """Retorna estatísticas do banco.

        Returns:
            Dict com contagens de ofertas, histórico e envios.
        """
        ofertas = self.conn.execute("SELECT COUNT(*) FROM ofertas").fetchone()[0]
        historico = self.conn.execute("SELECT COUNT(*) FROM historico_precos").fetchone()[0]
        enviadas = self.conn.execute("SELECT COUNT(*) FROM ofertas_enviadas").fetchone()[0]
        lojas = self.conn.execute(
            "SELECT DISTINCT loja FROM ofertas WHERE loja IS NOT NULL"
        ).fetchall()
        return {
            "ofertas": ofertas,
            "historico": historico,
            "enviadas": enviadas,
            "lojas": [r[0] for r in lojas],
        }
