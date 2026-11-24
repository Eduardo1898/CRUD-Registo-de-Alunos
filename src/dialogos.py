import sqlite3

import customtkinter as ctk

from . import tema
from .icones import icone
from .validators import CURSOS, validar_aluno


class Dialogo(ctk.CTkToplevel):
    def __init__(self, janela, titulo, simbolo, *, destrutivo=False):
        super().__init__(janela, fg_color=tema.LATERAL)
        self.withdraw()
        self.title(titulo)
        self.transient(janela)
        self.resizable(False, False)
        self.bind("<Escape>", lambda _evento: self.destroy())
        self.conteudo = ctk.CTkFrame(self, fg_color="transparent")
        self.conteudo.pack(fill="both", expand=True, padx=26, pady=22)
        cabecalho = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 14))
        cor = tema.ERRO_TEXTO if destrutivo else tema.AZUL_CLARO
        fundo = tema.PERIGO["fg_color"] if destrutivo else "#203B60"
        ctk.CTkLabel(cabecalho, text="", image=icone(simbolo, cor, 22),
                     width=39, height=39, fg_color=fundo, corner_radius=9).pack(side="left")
        ctk.CTkLabel(cabecalho, text=titulo, text_color=tema.TEXTO,
                     font=tema.fonte(23, "bold")).pack(side="left", padx=(11, 0))

    def barra_acoes(self):
        ctk.CTkFrame(self.conteudo, height=1, fg_color=tema.BORDA).pack(fill="x", pady=(5, 13))
        acoes = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        acoes.pack(fill="x")
        return acoes

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
        titulo, simbolo = ("Editar aluno", "editar") if aluno else ("Novo aluno", "adicionar")
        super().__init__(janela, titulo, simbolo)
        self.gravar = gravar
        valores = aluno[1:] if aluno else ("", "", "", "")
        campos = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        campos.pack(fill="x")
        campos.grid_columnconfigure((0, 1), weight=1, uniform="campo")
        campos_por_indice = {}
        posicoes = ((0, 0, 2), (2, 0, 2), (4, 0, 1), (4, 1, 1))
        rotulos = ("Nome completo", "Idade", "Curso", "Nota (opcional)")
        for indice, (linha, coluna, largura) in zip((0, 2, 1, 3), posicoes):
            rotulo, valor = rotulos[indice], valores[indice]
            margem = ((0, 6), (6, 0))[coluna] if largura == 1 else 0
            ctk.CTkLabel(campos, text=rotulo, text_color=tema.SECUNDARIO,
                         font=tema.fonte(), height=21).grid(
                row=linha, column=coluna, sticky="w", padx=margem, pady=(4, 3),
            )
            texto = "" if valor is None else str(valor)
            if rotulo == "Curso":
                opcoes = list(CURSOS)
                if texto and texto not in opcoes:
                    opcoes.append(texto)
                campo = ctk.CTkComboBox(
                    campos, values=opcoes, state="readonly", width=390, height=40,
                    font=tema.fonte(), dropdown_font=tema.fonte(), button_color=tema.BORDA,
                    dropdown_fg_color=tema.SUPERFICIE, dropdown_hover_color=tema.BORDA,
                    dropdown_text_color=tema.TEXTO, **tema.CAMPO,
                )
                campo.set(texto)
            else:
                campo = ctk.CTkEntry(campos, width=140, height=40, font=tema.fonte(), **tema.CAMPO)
                if texto:
                    campo.insert(0, texto)
            campo.grid(row=linha + 1, column=coluna, columnspan=largura, sticky="ew",
                       padx=margem, pady=(0, 8))
            campos_por_indice[indice] = campo
        self.campos = [campos_por_indice[indice] for indice in range(len(rotulos))]

        self.erro = ctk.CTkLabel(self.conteudo, text="", text_color=tema.ERRO_TEXTO,
                                 font=tema.fonte(13), justify="left", wraplength=390, height=38)
        self.erro.pack(anchor="w")
        acoes = self.barra_acoes()
        ctk.CTkButton(
            acoes, text="Salvar", image=icone("salvar", "#FFFFFF", 16),
            command=self.salvar, height=39, font=tema.fonte(14, "bold"), **tema.PRIMARIO,
        ).pack(side="right")
        ctk.CTkButton(acoes, text="Cancelar", command=self.destroy, width=96, height=39,
                      font=tema.fonte(), **tema.NEUTRO).pack(side="right", padx=(0, 9))
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
        super().__init__(janela, "Excluir aluno", "excluir", destrutivo=True)
        ctk.CTkLabel(
            self.conteudo, text=f"Excluir o cadastro de {nome}? Esta ação é permanente.",
            text_color=tema.SECUNDARIO, font=tema.fonte(), justify="left", wraplength=350,
        ).pack(anchor="w", pady=(0, 14))
        acoes = self.barra_acoes()
        ctk.CTkButton(
            acoes, text="Excluir aluno", image=icone("excluir", tema.ERRO_TEXTO, 16),
            height=39, font=tema.fonte(14, "bold"), command=lambda: self.confirmar(excluir),
            **tema.PERIGO,
        ).pack(side="right")
        cancelar = ctk.CTkButton(acoes, text="Cancelar", command=self.destroy, width=96,
                                 height=39, font=tema.fonte(), **tema.NEUTRO)
        cancelar.pack(side="right", padx=(0, 9))
        self.mostrar(cancelar)

    def confirmar(self, excluir):
        self.destroy()
        excluir()
