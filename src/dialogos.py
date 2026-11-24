import sqlite3

import customtkinter as ctk

from . import tema
from .validators import CURSOS, validar_aluno


class Dialogo(ctk.CTkToplevel):
    def __init__(self, janela, titulo):
        super().__init__(janela, fg_color=tema.LATERAL)
        self.withdraw()
        self.title(titulo)
        self.transient(janela)
        self.resizable(False, False)
        self.bind("<Escape>", lambda _evento: self.destroy())
        self.conteudo = ctk.CTkFrame(self, fg_color="transparent")
        self.conteudo.pack(fill="both", expand=True, padx=26, pady=22)
        ctk.CTkLabel(self.conteudo, text=titulo, text_color=tema.TEXTO,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")

    def mostrar(self, foco):
        self.update_idletasks()
        largura, altura = self.winfo_reqwidth(), self.winfo_reqheight()
        janela = self.master
        x = max(0, janela.winfo_rootx() + (janela.winfo_width() - largura) // 2)
        y = max(0, janela.winfo_rooty() + (janela.winfo_height() - altura) // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        foco.focus_set()


class FormularioAluno(Dialogo):
    def __init__(self, janela, gravar, aluno=None):
        super().__init__(janela, "Editar aluno" if aluno else "Novo aluno")
        self.gravar = gravar
        valores = aluno[1:] if aluno else ("", "", "", "")
        self.campos = []
        for rotulo, valor in zip(("Nome completo", "Idade", "Curso", "Nota (opcional)"), valores):
            ctk.CTkLabel(self.conteudo, text=rotulo, text_color=tema.SECUNDARIO).pack(
                anchor="w", pady=(10, 3)
            )
            texto = "" if valor is None else str(valor)
            if rotulo == "Curso":
                opcoes = list(CURSOS)
                if texto and texto not in opcoes:
                    opcoes.append(texto)
                campo = ctk.CTkComboBox(
                    self.conteudo, values=opcoes, state="readonly", width=360,
                    height=36, button_color=tema.BORDA, dropdown_fg_color=tema.SUPERFICIE,
                    dropdown_hover_color=tema.BORDA, dropdown_text_color=tema.TEXTO,
                    **tema.CAMPO,
                )
                campo.set(texto)
            else:
                campo = ctk.CTkEntry(self.conteudo, width=360, height=36, **tema.CAMPO)
                if texto:
                    campo.insert(0, texto)
            campo.pack(fill="x")
            self.campos.append(campo)

        self.erro = ctk.CTkLabel(self.conteudo, text="", text_color=tema.ERRO,
                                 justify="left", wraplength=360, height=38)
        self.erro.pack(anchor="w", pady=(5, 0))
        acoes = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        acoes.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(acoes, text="Salvar", command=self.salvar, height=36,
                      **tema.PRIMARIO).pack(side="right")
        ctk.CTkButton(acoes, text="Cancelar", command=self.destroy, width=94,
                      height=36, **tema.NEUTRO).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _evento: self.salvar())
        self.mostrar(self.campos[0])

    def salvar(self):
        try:
            aluno = validar_aluno(*(campo.get() for campo in self.campos))
            self.gravar(aluno)
        except ValueError as erro:
            self.erro.configure(text=str(erro))
        except sqlite3.Error:
            self.erro.configure(text="Não foi possível salvar. Tente novamente.")
        else:
            self.destroy()


class ConfirmacaoExclusao(Dialogo):
    def __init__(self, janela, nome, excluir):
        super().__init__(janela, "Excluir aluno")
        ctk.CTkLabel(
            self.conteudo, text=f"Excluir o cadastro de {nome}? Esta ação é permanente.",
            text_color=tema.SECUNDARIO, justify="left", wraplength=340,
        ).pack(anchor="w", pady=(8, 20))
        acoes = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        acoes.pack(fill="x")
        ctk.CTkButton(acoes, text="Excluir aluno", height=36, **tema.PERIGO,
                      command=lambda: self.confirmar(excluir)).pack(side="right")
        cancelar = ctk.CTkButton(acoes, text="Cancelar", command=self.destroy,
                                 width=94, height=36, **tema.NEUTRO)
        cancelar.pack(side="right", padx=(0, 8))
        self.mostrar(cancelar)

    def confirmar(self, excluir):
        self.destroy()
        excluir()
