from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import patch

import customtkinter as ctk

from src import tema
from src.app import Aplicacao
from src.database import BancoAlunos
from src.dialogos import ConfirmacaoExclusao, FormularioAluno
from src.validators import CURSOS, DadosAluno


class CrudTest(unittest.TestCase):
    def setUp(self):
        ctk.set_appearance_mode("dark")
        try:
            self.janela = ctk.CTk()
        except tk.TclError as erro:
            self.skipTest(f"Tk requer um display: {erro}")
        self.addCleanup(self.fechar_janela)

        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.banco = BancoAlunos(Path(diretorio.name) / "alunos.db")
        self.app = Aplicacao(self.janela, self.banco)
        self.janela.update()

    def fechar_janela(self):
        for filho in self.janela.winfo_children():
            if isinstance(filho, ctk.CTkToplevel):
                filho.destroy()
        self.janela.update()
        for tarefa in self.janela.tk.call("after", "info"):
            self.janela.after_cancel(tarefa)
        self.janela.destroy()

    def modal(self, tipo):
        dialogo, = (filho for filho in self.janela.winfo_children() if isinstance(filho, tipo))
        self.assertEqual(self.janela.grab_current(), dialogo)
        return dialogo

    def selecionar(self, id_aluno):
        self.app.tabela.selection_set(str(id_aluno))
        self.janela.update()

    def test_cadastro_edicao_e_exclusao_usam_modais(self):
        self.app.novo_aluno()
        formulario = self.modal(FormularioAluno)
        formulario.salvar()
        self.assertIn("nome", formulario.erro.cget("text"))
        self.assertEqual(self.banco.listar(), [])

        nome, idade, curso, nota = formulario.campos
        nome.insert(0, "Aluno fictício")
        idade.insert(0, "20")
        curso.set(CURSOS[0])
        nota.insert(0, "8,5")
        formulario.salvar()
        id_aluno, *dados = self.banco.listar()[0]
        self.assertEqual(dados, ["Aluno fictício", 20, CURSOS[0], 8.5])
        self.assertEqual(self.app.status.cget("text_color"), tema.SUCESSO)

        self.selecionar(id_aluno)
        self.app.editar_aluno()
        formulario = self.modal(FormularioAluno)
        self.assertEqual(formulario.campos[2].get(), CURSOS[0])
        formulario.campos[3].delete(0, "end")
        formulario.salvar()
        self.assertIsNone(self.banco.listar()[0][-1])
        self.assertEqual(self.app.indicadores[1].cget("text"), "—")

        self.selecionar(id_aluno)
        self.app.pedir_exclusao()
        self.modal(ConfirmacaoExclusao).destroy()
        self.assertEqual(len(self.banco.listar()), 1)
        self.app.pedir_exclusao()
        dialogo = self.modal(ConfirmacaoExclusao)
        acoes = dialogo.conteudo.winfo_children()[-1]
        botao = next(botao for botao in acoes.winfo_children()
                     if botao.cget("text") == "Excluir aluno")
        botao.invoke()
        self.assertEqual(self.banco.listar(), [])
        self.assertEqual(self.app.indicadores[0].cget("text"), "0")

    def test_pesquisa_atualiza_tabela_e_mantem_indicadores_gerais(self):
        id_aluno = self.banco.cadastrar(DadosAluno("Ágata Fictícia", 20, CURSOS[0], 0))
        outro = self.banco.cadastrar(DadosAluno("Bruno Fictício", 21, CURSOS[1], 8))
        self.app.recarregar()
        self.selecionar(outro)
        self.assertEqual(self.app.botao_editar.cget("state"), "normal")
        self.app.campo_pesquisa.insert(0, "AGATA")
        self.assertEqual(self.app.tabela.get_children(), (str(id_aluno),))
        self.assertEqual(self.app.botao_editar.cget("state"), "disabled")
        self.assertEqual([card.cget("text") for card in self.app.indicadores], ["2", "4,00", "2"])
        self.app.ir_para_lista()
        self.assertEqual(len(self.app.tabela.get_children()), 2)

    def test_falha_de_gravacao_mantem_formulario_sem_sucesso(self):
        self.app.novo_aluno()
        formulario = self.modal(FormularioAluno)
        formulario.campos[0].insert(0, "Aluno fictício")
        formulario.campos[1].insert(0, "20")
        formulario.campos[2].set(CURSOS[0])
        with patch.object(self.banco, "cadastrar", side_effect=sqlite3.OperationalError):
            formulario.salvar()
        self.assertIn("Não foi possível salvar", formulario.erro.cget("text"))
        self.assertEqual(self.banco.listar(), [])
        self.assertEqual(self.app.status.cget("text"), "")
