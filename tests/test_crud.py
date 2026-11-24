from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import messagebox
import unittest
from unittest.mock import patch

from src.app import Aplicacao
from src.database import BancoAlunos


class CrudTest(unittest.TestCase):
    def setUp(self):
        try:
            janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"Tk requer um display: {erro}")
        self.addCleanup(janela.destroy)
        janela.withdraw()

        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.banco = BancoAlunos(Path(diretorio.name) / "alunos.db")
        self.app = Aplicacao(janela, self.banco)

    def selecionar_primeiro_aluno(self):
        tabela = self.app.tabela
        item, = tabela.get_children()
        tabela.selection_set(item)
        self.app.selecionar_aluno(None)

    def test_cadastro_selecao_edicao_e_exclusao_em_banco_novo(self):
        curso = "Ciência da Computação"
        self.app.entry_nome.insert(0, "Aluno fictício")
        self.app.entry_idade.insert(0, "20")
        self.app.entry_curso.set(curso)
        self.app.entry_nota.insert(0, "8.5")

        def verificar_gravacao_ao_exibir_sucesso(_titulo, _mensagem):
            self.assertEqual(self.banco.listar()[0][-1], nota_esperada)

        nota_esperada = 8.5
        with patch.object(messagebox, "showinfo", side_effect=verificar_gravacao_ao_exibir_sucesso):
            self.app.salvar_aluno()
            self.selecionar_primeiro_aluno()
            self.assertEqual(self.app.entry_curso.get(), curso)
            self.assertEqual(self.app.entry_nota.get(), "8.5")

            self.app.entry_nota.delete(0, tk.END)
            nota_esperada = None
            self.app.salvar_aluno()
            self.selecionar_primeiro_aluno()
            self.assertEqual(self.app.entry_nota.get(), "")

        with patch.object(messagebox, "askyesno", return_value=True):
            self.app.deletar_aluno()
        self.assertEqual(self.banco.listar(), [])

    def test_selecao_vazia_preserva_formulario(self):
        self.app.entry_nome.insert(0, "Cadastro em andamento")
        self.app.selecionar_aluno(None)
        self.assertEqual(self.app.entry_nome.get(), "Cadastro em andamento")
