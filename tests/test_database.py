"""Testes para o módulo database."""

import pytest
from scripts.core.database import Database


@pytest.fixture
def db():
    """Cria banco em memória para testes."""
    database = Database(":memory:")
    yield database
    database.close()


class TestSalvarOferta:
    """Testes para salvar_oferta."""

    def test_inserir_nova(self, db):
        """Testa inserção de nova oferta."""
        produto = {
            "produto_id": "test1",
            "nome": "Produto Teste",
            "preco_atual": 199.99,
            "loja": "Amazon",
        }
        resultado = db.salvar_oferta(produto)
        assert resultado is True

    def test_atualizar_existente(self, db):
        """Testa atualização de oferta existente."""
        produto = {
            "produto_id": "test1",
            "nome": "Produto Teste",
            "preco_atual": 199.99,
            "loja": "Amazon",
        }
        db.salvar_oferta(produto)
        produto["preco_atual"] = 179.99
        resultado = db.salvar_oferta(produto)
        assert resultado is False

    def test_sem_produto_id(self, db):
        """Testa inserção sem ID retorna False."""
        resultado = db.salvar_oferta({"nome": "Produto"})
        assert resultado is False


class TestBuscarOferta:
    """Testes para buscar_oferta."""

    def test_encontrar(self, db):
        """Testa busca de oferta existente."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto Teste",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        oferta = db.buscar_oferta("test1")
        assert oferta is not None
        assert oferta["nome"] == "Produto Teste"
        assert oferta["preco_atual"] == 199.99

    def test_nao_encontrar(self, db):
        """Testa busca de oferta inexistente."""
        oferta = db.buscar_oferta("inexistente")
        assert oferta is None


class TestAtualizarPreco:
    """Testes para atualizar_preco."""

    def test_queda_preco(self, db):
        """Testa detecção de queda de preço."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        resultado = db.atualizar_preco("test1", 179.99)
        assert resultado is True

    def test_sem_queda(self, db):
        """Testa quando preço não cai."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        resultado = db.atualizar_preco("test1", 209.99)
        assert resultado is False

    def testProduto_inexistente(self, db):
        """Testa atualização de produto inexistente."""
        resultado = db.atualizar_preco("inexistente", 100.00)
        assert resultado is False


class TestAtualizarVista:
    """Testes para atualizar_vista."""

    def test_atualizar_vista(self, db):
        """Testa atualização da última visualização."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        oferta_antes = db.buscar_oferta("test1")
        db.atualizar_vista("test1")
        oferta_depois = db.buscar_oferta("test1")
        assert oferta_depois["ultima_vista"] >= oferta_antes["ultima_vista"]


class TestHistoricoPrecos:
    """Testes para salvar_historico e buscar_historico."""

    def test_salvar_e_buscar(self, db):
        """Testa salvar e buscar histórico."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        db.salvar_historico("test1", 199.99)
        db.salvar_historico("test1", 189.99)
        db.salvar_historico("test1", 179.99)
        historico = db.buscar_historico("test1")
        assert len(historico) == 3
        assert historico[0]["preco"] == 199.99

    def test_historico_com_filtro_dias(self, db):
        """Testa busca de histórico filtrando por dias."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        db.salvar_historico("test1", 199.99)
        historico = db.buscar_historico("test1", dias=1)
        assert len(historico) >= 1


class TestMenorPreco:
    """Testes para buscar_menor_preco."""

    def test_menor_preco(self, db):
        """Testa busca do menor preço."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        db.salvar_historico("test1", 199.99)
        db.salvar_historico("test1", 179.99)
        db.salvar_historico("test1", 189.99)
        menor = db.buscar_menor_preco("test1")
        assert menor == 179.99

    def test_sem_historico(self, db):
        """Testa menor preço sem histórico."""
        menor = db.buscar_menor_preco("inexistente")
        assert menor is None


class TestBuscarPorLoja:
    """Testes para buscar_por_loja."""

    def test_buscar_por_loja(self, db):
        """Testa busca de ofertas por loja."""
        db.salvar_oferta({"produto_id": "p1", "nome": "P1", "preco_atual": 100, "loja": "Amazon"})
        db.salvar_oferta({"produto_id": "p2", "nome": "P2", "preco_atual": 200, "loja": "Growth"})
        db.salvar_oferta({"produto_id": "p3", "nome": "P3", "preco_atual": 300, "loja": "Amazon"})
        ofertas = db.buscar_por_loja("Amazon")
        assert len(ofertas) == 2


class TestRegistrarEnvio:
    """Testes para registrar_envio."""

    def test_registrar(self, db):
        """Testa registro de envio."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 199.99,
            "loja": "Amazon",
        })
        db.registrar_envio("test1", "nova", 199.99)
        enviados = db.buscar_enviados_recentemente()
        assert len(enviados) == 1
        assert enviados[0]["tipo"] == "nova"


class TestStats:
    """Testes para stats."""

    def test_stats(self, db):
        """Testa retorno de estatísticas."""
        db.salvar_oferta({"produto_id": "p1", "nome": "P1", "preco_atual": 100, "loja": "Amazon"})
        db.salvar_oferta({"produto_id": "p2", "nome": "P2", "preco_atual": 200, "loja": "Growth"})
        db.salvar_historico("p1", 100)
        stats = db.stats()
        assert stats["ofertas"] == 2
        assert stats["historico"] == 1
        assert "Amazon" in stats["lojas"]
        assert "Growth" in stats["lojas"]


class TestCleanup:
    """Testes para cleanup_historico."""

    def test_cleanup(self, db):
        """Testa limpeza de histórico antigo."""
        db.salvar_oferta({
            "produto_id": "test1",
            "nome": "Produto",
            "preco_atual": 100,
            "loja": "Amazon",
        })
        db.salvar_historico("test1", 100)
        removidos = db.cleanup_historico(dias=0)
        assert removidos >= 0
