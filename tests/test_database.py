from contextlib import closing
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src import database
from src.database import BancoAlunos, ErroMigracao
from src.validators import DadosAluno


class BancoTest(unittest.TestCase):
    def setUp(self):
        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.raiz = Path(diretorio.name)
        self.destino = self.raiz / "data" / "alunos.db"
        self.legado = self.raiz / "sistema_alunos.db"
        self.aluno = DadosAluno("Aluno fictício", 20, "Curso fictício", None)

    def test_crud_e_identificadores_inexistentes(self):
        banco = BancoAlunos(self.destino)
        id_aluno = banco.cadastrar(self.aluno)
        self.assertEqual(banco.listar(), [(id_aluno, "Aluno fictício", 20, "Curso fictício", None)])

        edicao = DadosAluno("Aluno editado", 21, "Curso fictício", 8.5)
        self.assertTrue(banco.atualizar(id_aluno, edicao))
        self.assertEqual(BancoAlunos(self.destino).listar(), [
            (id_aluno, "Aluno editado", 21, "Curso fictício", 8.5),
        ])
        self.assertTrue(banco.excluir(id_aluno))
        self.assertFalse(banco.atualizar(id_aluno, edicao))
        self.assertFalse(banco.excluir(id_aluno))
        self.assertEqual(banco.listar(), [])

    def test_migracao_do_legado_preserva_wal_e_pode_ser_repetida(self):
        with closing(sqlite3.connect(self.legado)) as conexao:
            conexao.execute("PRAGMA journal_mode=WAL")
            with conexao:
                conexao.execute("""
                    CREATE TABLE alunos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                        idade INTEGER, curso TEXT
                    )
                """)
                conexao.execute(
                    "INSERT INTO alunos VALUES (?, ?, ?, ?)",
                    (17, "Registro anterior", 22, "Curso antigo"),
                )

            with (
                patch.object(database, "BANCO_PADRAO", self.destino),
                patch.object(database, "BANCOS_LEGADOS", (self.legado,)),
            ):
                banco = BancoAlunos()
                self.assertEqual(banco.listar(), [(17, "Registro anterior", 22, "Curso antigo", None)])
                self.assertGreater(banco.cadastrar(self.aluno), 17)
                self.assertEqual(BancoAlunos().listar(), banco.listar())

                with self.assertRaises(ErroMigracao):
                    BancoAlunos(legado=self.legado)

            colunas = conexao.execute("PRAGMA table_info(alunos)").fetchall()
            self.assertEqual([coluna[1] for coluna in colunas], ["id", "nome", "idade", "curso"])
            self.assertEqual(conexao.execute("SELECT id FROM alunos").fetchall(), [(17,)])

    def test_importacao_preserva_nota_de_banco_ja_migrado(self):
        origem = BancoAlunos(self.legado)
        origem.cadastrar(DadosAluno("Aluno fictício", 20, "Curso fictício", 0))
        banco = BancoAlunos(self.destino, legado=self.legado)
        self.assertEqual(banco.listar(), origem.listar())

    def test_importacao_invalida_nao_publica_destino(self):
        self.legado.write_bytes(b"conteudo invalido")
        with self.assertRaises(sqlite3.DatabaseError):
            BancoAlunos(self.destino, legado=self.legado)
        self.assertFalse(self.destino.exists())
        self.assertEqual(self.legado.read_bytes(), b"conteudo invalido")

    def test_dois_bancos_legados_exigem_escolha(self):
        segundo = self.raiz / "segundo.db"
        self.legado.touch()
        segundo.touch()
        with (
            patch.object(database, "BANCO_PADRAO", self.destino),
            patch.object(database, "BANCOS_LEGADOS", (self.legado, segundo)),
            self.assertRaises(ErroMigracao),
        ):
            BancoAlunos()
        self.assertFalse(self.destino.exists())

    def test_caminho_padrao_independe_do_diretorio_atual(self):
        self.assertEqual(database.BANCO_PADRAO, database.RAIZ / "data" / database.NOME_BANCO)
        self.addCleanup(os.chdir, Path.cwd())
        with (
            patch.object(database, "BANCO_PADRAO", self.destino),
            patch.object(database, "BANCOS_LEGADOS", ()),
        ):
            os.chdir(self.raiz)
            BancoAlunos().cadastrar(self.aluno)
            os.chdir(self.destino.parent)
            self.assertEqual(len(BancoAlunos().listar()), 1)

    def test_falha_de_gravacao_reverte_transacao(self):
        banco = BancoAlunos(self.destino)
        with closing(sqlite3.connect(self.destino)) as conexao:
            conexao.executescript("""
                CREATE TRIGGER impedir_cadastro AFTER INSERT ON alunos
                BEGIN
                    SELECT RAISE(FAIL, 'cadastro bloqueado');
                END;
            """)
        with self.assertRaises(sqlite3.IntegrityError):
            banco.cadastrar(self.aluno)
        self.assertEqual(banco.listar(), [])
