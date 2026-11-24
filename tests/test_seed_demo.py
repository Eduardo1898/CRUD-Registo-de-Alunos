from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.seed_demo import alunos_ficticios, main
from src import app, database
from src.database import BancoAlunos, ErroBancoDemo
from src.validators import CURSOS, validar_aluno


class SeedDemoTest(unittest.TestCase):
    def setUp(self):
        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.pasta = Path(diretorio.name)
        self.demo = self.pasta / "data" / "studenthub_demo.db"
        self.principal = self.pasta / "data" / "sistema_alunos.db"
        self.legado = self.pasta / "sistema_alunos.db"
        self.perfil = validar_aluno("Aluno fictício externo", "22", CURSOS[0], "7")
        contextos = ExitStack()
        self.addCleanup(contextos.close)
        contextos.enter_context(patch.multiple(
            database, BANCO_DEMO=self.demo, BANCO_PADRAO=self.principal,
            BANCOS_LEGADOS=(self.legado,),
        ))
        contextos.enter_context(redirect_stdout(StringIO()))
        contextos.enter_context(redirect_stderr(StringIO()))

    def test_gera_50_alunos_validos_e_reproduziveis(self):
        self.assertEqual(main(), 0)
        dados = BancoAlunos.abrir_demo().listar()
        self.assertEqual(len(dados), 50)
        self.assertEqual(len({nome for _, nome, *_ in dados}), 50)
        self.assertEqual({curso for _, _, _, curso, _ in dados}, set(CURSOS))
        self.assertTrue(all(18 <= idade <= 35 for _, _, idade, _, _ in dados))
        notas = {nota for *_, nota in dados}
        self.assertIn(None, notas)
        self.assertGreater(len(notas), 10)
        self.assertTrue(all(0 <= nota <= 10 for nota in notas if nota is not None))
        self.assertFalse(self.principal.exists())

        with patch.object(database, "BANCO_DEMO", self.pasta / "reproducao.db"):
            self.assertEqual(main(), 0)
            self.assertEqual(BancoAlunos.abrir_demo().listar(), dados)

    def test_reexecucao_preserva_edicoes_e_bancos_de_uso_normal(self):
        for caminho in (self.principal, self.legado):
            BancoAlunos(caminho).cadastrar(self.perfil)
        originais = {caminho: caminho.read_bytes() for caminho in (self.principal, self.legado)}

        self.assertEqual(main(), 0)
        banco_demo = BancoAlunos.abrir_demo()
        banco_demo.atualizar(1, self.perfil)
        demonstracao_editada = banco_demo.listar()

        self.assertEqual(main(), 0)
        self.assertEqual(banco_demo.listar(), demonstracao_editada)
        self.assertEqual(len(demonstracao_editada), 50)
        for caminho, original in originais.items():
            self.assertEqual(caminho.read_bytes(), original)

    def test_recusa_banco_preexistente_sem_identificacao(self):
        BancoAlunos(self.demo).cadastrar(self.perfil)
        original = self.demo.read_bytes()
        self.assertEqual(main(), 1)
        with self.assertRaises(ErroBancoDemo):
            BancoAlunos.abrir_demo()
        self.assertEqual(self.demo.read_bytes(), original)

    def test_recusa_link_para_banco_principal(self):
        BancoAlunos(self.principal).cadastrar(self.perfil)
        original = self.principal.read_bytes()
        self.demo.hardlink_to(self.principal)
        self.assertEqual(main(), 1)
        with self.assertRaises(ErroBancoDemo):
            BancoAlunos.abrir_demo()
        self.assertEqual(self.principal.read_bytes(), original)

    def test_falha_de_geracao_nao_publica_banco_parcial(self):
        def dados_incompletos():
            yield next(alunos_ficticios())
            raise RuntimeError("Falha simulada")

        with self.assertRaises(RuntimeError):
            BancoAlunos.gerar_demo(dados_incompletos())
        self.assertFalse(self.demo.exists())
        self.assertEqual(list(self.demo.parent.iterdir()), [])
        self.assertEqual(main(), 0)
        self.assertEqual(len(BancoAlunos.abrir_demo().listar()), 50)

    def test_app_seleciona_demo_sem_criar_banco_principal(self):
        self.assertEqual(main(), 0)
        with (
            patch("sys.argv", ["studenthub", "--demo"]),
            patch.object(app.ctk, "CTk"),
            patch.object(app, "Aplicacao") as aplicacao,
        ):
            self.assertEqual(app.main(), 0)
        janela, banco = aplicacao.call_args.args
        self.assertEqual(banco.caminho, self.demo)
        janela.title.assert_called_with("StudentHub | Modo demonstrativo")
        self.assertFalse(self.principal.exists())

    def test_demo_ausente_nao_cria_banco_nem_recorre_ao_principal(self):
        with (
            patch("sys.argv", ["studenthub", "--demo"]),
            patch.object(app.ctk, "CTk"),
            patch.object(app.messagebox, "showerror") as erro,
            patch.object(app, "Aplicacao") as aplicacao,
        ):
            self.assertEqual(app.main(), 1)
        erro.assert_called_once()
        aplicacao.assert_not_called()
        self.assertFalse(self.demo.exists())
        self.assertFalse(self.principal.exists())
