from contextlib import closing
import os
from pathlib import Path
import runpy
import sqlite3
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import messagebox
import unittest
from unittest.mock import patch


APP = Path(__file__).resolve().parents[1] / "trabalhoPythonCrud" / "app.py"


class CrudTest(unittest.TestCase):
    def setUp(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk requer um display: {error}")
        root.destroy()

        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(temp_dir.name)

    def abrir_app(self):
        with patch.object(tk.Tk, "mainloop", autospec=True) as mainloop:
            try:
                return runpy.run_path(str(APP), run_name="__main__")
            finally:
                if mainloop.called:
                    self.addCleanup(mainloop.call_args.args[0].destroy)

    def dados(self, consulta):
        with closing(sqlite3.connect("sistema_alunos.db")) as conexao:
            return conexao.execute(consulta).fetchall()

    def test_migracao_preserva_registros_e_pode_ser_repetida(self):
        with sqlite3.connect("sistema_alunos.db") as conexao:
            conexao.execute(
                "CREATE TABLE alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "nome TEXT NOT NULL, idade INTEGER, curso TEXT)"
            )
            conexao.execute(
                "INSERT INTO alunos (id, nome, idade, curso) VALUES (?, ?, ?, ?)",
                (17, "Registro anterior", 22, "Engenharia de Software"),
            )
        conexao.close()

        app = self.abrir_app()
        conexao, _ = app["conectar_banco"]()
        conexao.close()
        self.assertEqual(
            self.dados("SELECT id, nome, idade, curso, nota FROM alunos"),
            [(17, "Registro anterior", 22, "Engenharia de Software", None)],
        )
        colunas = self.dados("PRAGMA table_info(alunos)")
        self.assertEqual([coluna[1] for coluna in colunas].count("nota"), 1)

        tabela = app["tabela"]
        tabela.selection_set(tabela.get_children()[0])
        app["selecionar_aluno"](None)
        self.assertEqual(app["entry_nota"].get(), "")

    def test_cadastro_selecao_edicao_e_exclusao_em_banco_novo(self):
        app = self.abrir_app()
        curso = "Ciência da Computação"
        app["entry_nome"].insert(0, "Aluno fictício")
        app["entry_idade"].insert(0, "20")
        app["entry_curso"].set(curso)
        app["entry_nota"].insert(0, "8.5")

        with patch.object(messagebox, "showinfo"):
            app["salvar_aluno"]()
            self.assertEqual(self.dados("SELECT nota FROM alunos"), [(8.5,)])

            tabela = app["tabela"]
            item, = tabela.get_children()
            tabela.selection_set(item)
            app["selecionar_aluno"](None)
            self.assertEqual(app["entry_curso"].get(), curso)
            self.assertEqual(app["entry_nota"].get(), "8.5")

            app["entry_nota"].delete(0, tk.END)
            app["entry_nota"].insert(0, "9.5")
            app["salvar_aluno"]()
            self.assertEqual(self.dados("SELECT nota FROM alunos"), [(9.5,)])

        tabela.selection_set(tabela.get_children()[0])
        app["selecionar_aluno"](None)
        with patch.object(messagebox, "askyesno", return_value=True):
            app["deletar_aluno"]()
        self.assertEqual(self.dados("SELECT id FROM alunos"), [])

    def test_selecao_vazia_preserva_formulario(self):
        app = self.abrir_app()
        app["entry_nome"].insert(0, "Cadastro em andamento")

        app["selecionar_aluno"](None)

        self.assertEqual(app["entry_nome"].get(), "Cadastro em andamento")


if __name__ == "__main__":
    unittest.main()
