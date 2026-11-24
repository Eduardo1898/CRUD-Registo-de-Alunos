from contextlib import ExitStack, closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src import app, database
from src.database import BancoAlunos, ErroMigracao


class EmpacotamentoTest(unittest.TestCase):
    def setUp(self):
        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.raiz = Path(diretorio.name)
        self.pasta_usuario = self.raiz / "Local" / "StudentHub"
        self.normal = self.pasta_usuario / "sistema_alunos.db"
        self.demo = self.pasta_usuario / "studenthub_demo.db"
        self.legado = self.raiz / "sistema_alunos.db"
        contextos = ExitStack()
        self.addCleanup(contextos.close)
        contextos.enter_context(patch.multiple(
            database, EMPACOTADO=True, RAIZ=self.raiz, BANCO_PADRAO=self.normal,
            BANCO_DEMO=self.demo, BANCOS_LEGADOS=(self.legado,),
        ))

    def _criar_legado(self, caminho):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(caminho)) as conexao, conexao:
            conexao.execute("CREATE TABLE alunos (id INTEGER PRIMARY KEY, nome TEXT, idade INTEGER, curso TEXT)")
            conexao.execute("INSERT INTO alunos VALUES (1, 'Aluno fictício', 22, 'Curso fictício')")

    def test_resolve_pasta_windows_e_preserva_o_caminho_do_codigo_fonte(self):
        with (
            patch("src.database.sys.platform", "win32"),
            patch.dict("src.database.os.environ", {"LOCALAPPDATA": str(self.pasta_usuario.parent)}),
        ):
            self.assertEqual(database.diretorio_dados(), self.pasta_usuario)
            with patch.object(database, "EMPACOTADO", False):
                self.assertEqual(database.diretorio_dados(), self.raiz / "data")

    def test_localappdata_relativo_usa_pasta_do_usuario(self):
        with (
            patch("src.database.sys.platform", "win32"),
            patch("src.database.Path.home", return_value=self.raiz),
            patch.dict("src.database.os.environ", {"LOCALAPPDATA": "."}),
        ):
            self.assertEqual(database.diretorio_dados(), self.raiz / "AppData" / "Local" / "StudentHub")

    def test_empacotado_so_importa_por_solicitacao_explicita(self):
        self._criar_legado(self.legado)
        original = self.legado.read_bytes()
        self.assertEqual(BancoAlunos().listar(), [])
        with self.assertRaises(ErroMigracao):
            BancoAlunos(legado=self.legado)
        self.normal.unlink()
        self.assertEqual(BancoAlunos(legado=self.legado).listar(),
                         [(1, "Aluno fictício", 22, "Curso fictício", None)])
        self.assertEqual(self.legado.read_bytes(), original)

    def test_banco_antigo_na_pasta_persistente_nao_e_migrado_silenciosamente(self):
        self._criar_legado(self.normal)
        original = self.normal.read_bytes()
        with self.assertRaises(ErroMigracao):
            BancoAlunos()
        self.assertEqual(self.normal.read_bytes(), original)

    def test_demo_empacotado_gera_apenas_o_banco_demonstrativo(self):
        with (
            patch("sys.argv", ["StudentHub.exe", "--demo"]),
            patch.object(app, "EMPACOTADO", True),
            patch.object(app.ctk, "CTk"),
            patch.object(app, "Aplicacao") as aplicacao,
        ):
            self.assertEqual(app.main(), 0)
            self.assertEqual(app.main(), 0)
        janela, banco = aplicacao.call_args.args
        self.assertEqual(banco.caminho, self.demo)
        self.assertEqual(len(banco.listar()), 50)
        janela.title.assert_called_with("StudentHub | Modo demonstrativo")
        self.assertFalse(self.normal.exists())
        with self.assertRaises(ErroMigracao):
            BancoAlunos(legado=self.demo)
        self.assertFalse(self.normal.exists())
