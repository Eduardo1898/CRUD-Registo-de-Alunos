import argparse
from functools import partial
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from . import tema
from .database import BancoAlunos, ErroMigracao
from .dialogos import ConfirmacaoExclusao, FormularioAluno
from .painel import calcular_indicadores, filtrar_alunos


class Aplicacao:
    def __init__(self, janela, banco):
        self.janela = janela
        self.banco = banco
        self.alunos = {}
        self.pesquisa = tk.StringVar(master=janela)
        janela.title("StudentHub | Gestão acadêmica")
        janela.geometry("1200x740")
        janela.minsize(900, 550)
        janela.configure(fg_color=tema.FUNDO)
        janela.grid_columnconfigure(1, weight=1)
        janela.grid_rowconfigure(0, weight=1)

        lateral = ctk.CTkFrame(janela, width=196, corner_radius=0, fg_color=tema.LATERAL)
        lateral.grid(row=0, column=0, sticky="nsew")
        lateral.grid_propagate(False)
        lateral.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lateral, text="StudentHub", text_color=tema.TEXTO,
                     font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=22, pady=(27, 0)
        )
        ctk.CTkLabel(lateral, text="Gestão acadêmica", text_color=tema.SECUNDARIO,
                     font=ctk.CTkFont(size=13)).grid(row=1, column=0, sticky="w", padx=23)
        ctk.CTkButton(
            lateral, text="Lista de alunos", anchor="w", height=42, **tema.NEUTRO,
            command=self.ir_para_lista,
        ).grid(row=2, column=0, sticky="ew", padx=15, pady=(35, 0))

        principal = ctk.CTkFrame(janela, fg_color="transparent")
        principal.grid(row=0, column=1, sticky="nsew", padx=26, pady=(24, 16))
        principal.grid_columnconfigure(0, weight=1)
        principal.grid_rowconfigure(2, weight=1)
        self._montar_cabecalho(principal)
        self._montar_indicadores(principal)
        self._montar_lista(principal)

        self.status = ctk.CTkLabel(principal, text="", anchor="w", text_color=tema.SECUNDARIO)
        self.status.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        self.pesquisa.trace_add("write", self._mostrar_lista)
        self.recarregar()

    def _montar_cabecalho(self, principal):
        cabecalho = ctk.CTkFrame(principal, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        cabecalho.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(cabecalho, text="Gestão de alunos", text_color=tema.TEXTO,
                     font=ctk.CTkFont(size=34, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(cabecalho, text="+ Novo aluno", height=40, width=122,
                      command=self.novo_aluno, **tema.PRIMARIO).grid(row=0, column=1)

    def _montar_indicadores(self, principal):
        faixa = ctk.CTkFrame(principal, fg_color="transparent")
        faixa.grid(row=1, column=0, sticky="ew", pady=(0, 19))
        self.indicadores = []
        titulos = ("Total de alunos", "Média geral das notas", "Cursos distintos")
        for coluna, titulo in enumerate(titulos):
            faixa.grid_columnconfigure(coluna, weight=1, uniform="indicador")
            card = ctk.CTkFrame(faixa, corner_radius=12, fg_color=tema.LATERAL,
                                border_width=1, border_color=tema.BORDA)
            card.grid(row=0, column=coluna, sticky="nsew", padx=(0, 12 if coluna < 2 else 0))
            ctk.CTkLabel(card, text=titulo, text_color=tema.SECUNDARIO,
                         font=ctk.CTkFont(size=13)).pack(anchor="w", padx=15, pady=(10, 0))
            valor = ctk.CTkLabel(card, text="—", text_color=tema.TEXTO,
                                  font=ctk.CTkFont(size=29, weight="bold"))
            valor.pack(anchor="w", padx=15, pady=(0, 10))
            self.indicadores.append(valor)

    def _montar_lista(self, principal):
        painel = ctk.CTkFrame(principal, corner_radius=12, fg_color=tema.LATERAL,
                              border_width=1, border_color=tema.BORDA)
        painel.grid(row=2, column=0, sticky="nsew")
        painel.grid_columnconfigure(0, weight=1)
        painel.grid_rowconfigure(2, weight=1)

        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 7))
        barra.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(barra, text="Buscar por nome", text_color=tema.SECUNDARIO).grid(
            row=0, column=1, sticky="e", padx=(10, 8)
        )
        self.campo_pesquisa = ctk.CTkEntry(
            barra, width=174, height=36, textvariable=self.pesquisa, **tema.CAMPO
        )
        self.campo_pesquisa.bind("<Escape>", self._limpar_pesquisa)
        self.campo_pesquisa.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(barra, text="Alunos cadastrados", text_color=tema.TEXTO,
                     font=ctk.CTkFont(size=19, weight="bold")).grid(row=0, column=0, sticky="w")

        controles = ctk.CTkFrame(painel, fg_color="transparent")
        controles.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.contagem = ctk.CTkLabel(controles, text="", text_color=tema.SECUNDARIO)
        self.contagem.pack(side="left")
        self.botao_excluir = ctk.CTkButton(controles, text="Excluir", width=78, height=32,
                                           command=self.pedir_exclusao, **tema.PERIGO)
        self.botao_excluir.pack(side="right")
        self.botao_editar = ctk.CTkButton(controles, text="Editar", width=78, height=32,
                                          command=self.editar_aluno, **tema.NEUTRO)
        self.botao_editar.pack(side="right", padx=(0, 8))

        quadro = ctk.CTkFrame(painel, fg_color=tema.LATERAL, corner_radius=0)
        quadro.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 13))
        quadro.grid_columnconfigure(0, weight=1)
        quadro.grid_rowconfigure(0, weight=1)
        tema.estilizar_tabela(self.janela)
        colunas = (("id", "ID", 56, False), ("nome", "Nome", 135, True),
                   ("idade", "Idade", 60, False), ("curso", "Curso", 252, True),
                   ("nota", "Nota", 60, False))
        self.tabela = ttk.Treeview(quadro, columns=[coluna[0] for coluna in colunas],
                                   style="StudentHub.Treeview", show="headings", selectmode="browse")
        self.tabela.grid(row=0, column=0, sticky="nsew")
        for coluna, titulo, largura, flexivel in colunas:
            alinhamento = "w" if flexivel else "center"
            self.tabela.heading(coluna, text=titulo, anchor=alinhamento)
            self.tabela.column(coluna, width=largura, minwidth=largura, stretch=flexivel,
                               anchor=alinhamento)
        self.tabela.tag_configure("alternada", background="#223047")
        rolagem = ctk.CTkScrollbar(quadro, command=self.tabela.yview, fg_color=tema.LATERAL,
                                   button_color=tema.BORDA)
        rolagem.grid(row=0, column=1, sticky="ns")
        self.tabela.configure(yscrollcommand=rolagem.set)
        self.tabela.bind("<<TreeviewSelect>>", self._atualizar_acoes)
        self.tabela.bind("<Return>", lambda _evento: self.editar_aluno())

    def _limpar_pesquisa(self, _evento=None):
        self.pesquisa.set("")

    def ir_para_lista(self):
        self._limpar_pesquisa()
        self.campo_pesquisa.focus_set()

    def recarregar(self, mensagem=None):
        try:
            self.alunos = {str(aluno[0]): aluno for aluno in self.banco.listar()}
        except sqlite3.Error:
            aviso = "Não foi possível atualizar a lista."
            self._feedback(f"{mensagem} {aviso}" if mensagem else aviso, tema.ERRO)
            return
        total, media, cursos = calcular_indicadores(self.alunos.values())
        valores = (total, "—" if media is None else f"{media:.2f}".replace(".", ","), cursos)
        for indicador, valor in zip(self.indicadores, valores):
            indicador.configure(text=str(valor))
        self._mostrar_lista()
        if mensagem:
            self._feedback(mensagem, tema.SUCESSO)

    def _mostrar_lista(self, *_):
        visiveis = filtrar_alunos(self.alunos.values(), self.pesquisa.get())
        self.tabela.delete(*self.tabela.get_children())
        for indice, (id_aluno, nome, idade, curso, nota) in enumerate(visiveis):
            exibicao = f"{nota:g}".replace(".", ",") if isinstance(nota, (float, int)) else nota
            self.tabela.insert("", "end", iid=str(id_aluno), tags=("alternada",) if indice % 2 else (),
                               values=(id_aluno, nome, idade if idade is not None else "—",
                                       curso or "—", exibicao if exibicao is not None else "—"))
        if visiveis:
            resumo = f"{len(visiveis)} de {len(self.alunos)} alunos"
        else:
            resumo = "Nenhum aluno encontrado" if self.pesquisa.get().strip() else "Nenhum aluno cadastrado"
        self.contagem.configure(text=resumo)
        self._atualizar_acoes()

    def _selecionado(self):
        selecao = self.tabela.selection()
        return self.alunos.get(selecao[0]) if selecao else None

    def _atualizar_acoes(self, _evento=None):
        estado = "normal" if self._selecionado() else "disabled"
        self.botao_editar.configure(state=estado)
        self.botao_excluir.configure(state=estado)

    def _feedback(self, mensagem, cor):
        self.status.configure(text=mensagem, text_color=cor)

    def novo_aluno(self):
        FormularioAluno(self.janela, self._cadastrar)

    def _cadastrar(self, dados):
        self.banco.cadastrar(dados)
        self._limpar_pesquisa()
        self.recarregar("Aluno cadastrado com sucesso.")

    def editar_aluno(self):
        aluno = self._selecionado()
        if aluno:
            FormularioAluno(self.janela, partial(self._atualizar, aluno[0]), aluno=aluno)

    def _atualizar(self, id_aluno, dados):
        if not self.banco.atualizar(id_aluno, dados):
            self.recarregar()
            raise ValueError("Este aluno já não está cadastrado.")
        self.recarregar("Cadastro atualizado com sucesso.")

    def pedir_exclusao(self):
        aluno = self._selecionado()
        if aluno:
            ConfirmacaoExclusao(self.janela, aluno[1], partial(self._excluir, aluno[0]))

    def _excluir(self, id_aluno):
        try:
            excluido = self.banco.excluir(id_aluno)
        except sqlite3.Error:
            self._feedback("Não foi possível excluir o aluno. Tente novamente.", tema.ERRO)
            return
        if excluido:
            self.recarregar("Aluno excluído com sucesso.")
        else:
            self.recarregar()
            self._feedback("Este aluno já não está cadastrado.", tema.ERRO)


def main():
    parser = argparse.ArgumentParser(description="StudentHub | Gestão acadêmica")
    parser.add_argument("--banco-legado", help="Caminho do banco antigo a importar")
    argumentos = parser.parse_args()
    ctk.set_appearance_mode("dark")
    janela = ctk.CTk()
    try:
        banco = BancoAlunos(legado=argumentos.banco_legado)
    except (sqlite3.Error, OSError, ErroMigracao) as erro:
        janela.withdraw()
        detalhe = str(erro) if isinstance(erro, ErroMigracao) else "Verifique o arquivo e as permissões."
        messagebox.showerror("Erro", f"Não foi possível preparar o banco. {detalhe}", parent=janela)
        janela.destroy()
        return 1

    Aplicacao(janela, banco)
    janela.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
