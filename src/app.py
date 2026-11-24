import argparse
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from .database import BancoAlunos, ErroMigracao
from .validators import CURSOS, apenas_numeros, validar_aluno


class Aplicacao:
    def __init__(self, janela, banco):
        self.banco = banco
        janela.title("Sistema de Cadastro de Alunos (CRUD)")
        janela.geometry("700x550")
        janela.resizable(False, False)

        estilo = ttk.Style(janela)
        estilo.theme_use("clam")

        frame_campos = ttk.LabelFrame(
            janela, text=" Dados do Aluno ", padding=10
        )
        frame_campos.pack(fill="x", padx=15, pady=10)

        self.lbl_id_val = tk.Label(
            frame_campos, text="", font=("Arial", 10, "bold"), fg="blue"
        )

        lbl_nome = tk.Label(frame_campos, text="Nome:", font=("Arial", 10))
        lbl_nome.grid(row=1, column=0, sticky="w", pady=5)
        self.entry_nome = ttk.Entry(frame_campos, width=50)
        self.entry_nome.grid(row=1, column=1, columnspan=3, sticky="w", pady=5)

        lbl_idade = tk.Label(frame_campos, text="Idade:", font=("Arial", 10))
        lbl_idade.grid(row=2, column=0, sticky="w", pady=5)
        valida_num = janela.register(apenas_numeros)
        self.entry_idade = ttk.Entry(frame_campos, width=10, validate="key", validatecommand=(valida_num, "%P"))
        self.entry_idade.grid(row=2, column=1, sticky="w", pady=5)

        lbl_curso = tk.Label(frame_campos, text="Curso:", font=("Arial", 10))
        lbl_curso.grid(row=2, column=2, sticky="w", padx=(20, 5), pady=5)
        self.entry_curso = ttk.Combobox(frame_campos, values=CURSOS, width=38, state="readonly")
        self.entry_curso.grid(row=2, column=3, sticky="w", pady=5)

        lbl_nota = tk.Label(frame_campos, text="Nota:", font=("Arial", 10))
        lbl_nota.grid(row=3, column=0, sticky="w", pady=5)
        self.entry_nota = ttk.Entry(frame_campos, width=10)
        self.entry_nota.grid(row=3, column=1, sticky="w", pady=5)

        frame_botoes = tk.Frame(janela)
        frame_botoes.pack(fill="x", padx=15, pady=10)

        btn_salvar = ttk.Button(
            frame_botoes, text="Salvar / Atualizar", command=self.salvar_aluno
        )
        btn_salvar.pack(side="left", padx=5)

        btn_deletar = ttk.Button(frame_botoes, text="Deletar", command=self.deletar_aluno)
        btn_deletar.pack(side="left", padx=5)

        btn_limpar = ttk.Button(
            frame_botoes, text="Limpar Campos", command=self.limpar_campos
        )
        btn_limpar.pack(side="left", padx=5)

        frame_tabela = ttk.LabelFrame(
            janela, text=" Alunos Cadastrados ", padding=5
        )
        frame_tabela.pack(fill="both", expand=True, padx=15, pady=10)

        colunas = ("id", "nome", "idade", "curso", "nota")
        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("idade", text="Idade")
        self.tabela.heading("curso", text="Curso")
        self.tabela.heading("nota", text="Nota")

        self.tabela.column("nota", width=70, anchor="center")
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=250)
        self.tabela.column("idade", width=70, anchor="center")
        self.tabela.column("curso", width=200)

        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tabela.bind("<<TreeviewSelect>>", self.selecionar_aluno)

        self.atualizar_tabela()

    def limpar_campos(self):
        self.entry_nome.delete(0, tk.END)
        self.entry_idade.delete(0, tk.END)
        self.entry_curso.set("")
        self.lbl_id_val.config(text="")
        self.entry_nota.delete(0, tk.END)

    def atualizar_tabela(self):
        try:
            dados = self.banco.listar()
        except sqlite3.Error:
            messagebox.showerror("Erro", "Não foi possível consultar os alunos.")
            return

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
        for id_aluno, nome, idade, curso, nota in dados:
            self.tabela.insert("", tk.END, values=(
                id_aluno, nome, "" if idade is None else idade,
                "" if curso is None else curso, "" if nota is None else nota,
            ))

    def salvar_aluno(self):
        try:
            aluno = validar_aluno(
                self.entry_nome.get(), self.entry_idade.get(),
                self.entry_curso.get(), self.entry_nota.get(),
            )
        except ValueError as erro:
            messagebox.showwarning("Aviso", str(erro))
            return

        id_aluno = self.lbl_id_val.cget("text")
        try:
            if id_aluno == "":
                self.banco.cadastrar(aluno)
                mensagem = "Aluno cadastrado com sucesso!"
            elif self.banco.atualizar(id_aluno, aluno):
                mensagem = "Dados do aluno atualizados!"
            else:
                self._registro_ausente()
                return
        except sqlite3.Error:
            messagebox.showerror("Erro", "Não foi possível salvar os dados do aluno.")
            return

        messagebox.showinfo("Sucesso", mensagem)
        self.limpar_campos()
        self.atualizar_tabela()

    def deletar_aluno(self):
        id_aluno = self.lbl_id_val.cget("text")
        if id_aluno == "":
            messagebox.showwarning("Aviso", "Selecione um aluno na tabela para deletar!")
            return
        if not messagebox.askyesno("Confirmação", "Tem certeza que deseja deletar este aluno?"):
            return

        try:
            excluido = self.banco.excluir(id_aluno)
        except sqlite3.Error:
            messagebox.showerror("Erro", "Não foi possível excluir o aluno.")
            return
        if not excluido:
            self._registro_ausente()
            return
        self.limpar_campos()
        self.atualizar_tabela()

    def _registro_ausente(self):
        messagebox.showwarning("Aviso", "O aluno selecionado já não está cadastrado.")
        self.limpar_campos()
        self.atualizar_tabela()

    def selecionar_aluno(self, _evento):
        selecionados = self.tabela.selection()
        if not selecionados:
            return

        self.limpar_campos()
        valores = self.tabela.item(selecionados[0], "values")
        self.lbl_id_val.config(text=valores[0])
        self.entry_nome.insert(0, valores[1])
        self.entry_idade.insert(0, valores[2])
        self.entry_curso.set(valores[3])
        self.entry_nota.insert(0, valores[4])


def main():
    parser = argparse.ArgumentParser(description="Sistema de Cadastro de Alunos")
    parser.add_argument("--banco-legado", help="Caminho do banco antigo a importar")
    argumentos = parser.parse_args()
    janela = tk.Tk()
    try:
        banco = BancoAlunos(legado=argumentos.banco_legado)
    except (sqlite3.Error, OSError, ErroMigracao) as erro:
        janela.withdraw()
        detalhe = str(erro) if isinstance(erro, ErroMigracao) else "Verifique o arquivo e as permissões."
        messagebox.showerror("Erro", f"Não foi possível preparar o banco. {detalhe}")
        janela.destroy()
        return 1

    Aplicacao(janela, banco)
    janela.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
