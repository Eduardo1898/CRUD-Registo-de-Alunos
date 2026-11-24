import customtkinter as ctk

from . import tema
from .icones import icone
from .painel import (ABAIXO_REFERENCIA, FAIXAS, NA_REFERENCIA, SEM_NOTA, TODAS_FAIXAS,
                     TODOS_DESEMPENHOS, cursos_disponiveis, filtrar_alunos)


class CampoPesquisa(ctk.CTkFrame):
    def __init__(self, pai, pesquisa, limpar):
        super().__init__(pai, fg_color=tema.FUNDO, border_width=1, border_color=tema.BORDA)
        lupa = ctk.CTkLabel(self, text="", image=icone("pesquisa", tema.SECUNDARIO))
        lupa.pack(side="left", padx=(12, 5))
        self.entrada = ctk.CTkEntry(
            self, width=228, height=42, textvariable=pesquisa, border_width=0,
            fg_color=tema.FUNDO, text_color=tema.TEXTO, font=tema.fonte(),
        )
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=1)
        self.entrada.bind("<Escape>", limpar)
        self.placeholder = ctk.CTkLabel(
            self, text="Pesquisar por nome", fg_color=tema.FUNDO,
            text_color=tema.SECUNDARIO, font=tema.fonte(),
        )
        self.placeholder.bind("<Button-1>", lambda _evento: self.entrada.focus_set())
        lupa.bind("<Button-1>", lambda _evento: self.entrada.focus_set())

        em_foco = False

        def atualizar_placeholder(*_):
            if pesquisa.get() or em_foco:
                self.placeholder.place_forget()
            else:
                self.placeholder.place(x=39, rely=0.5, anchor="w")

        def ao_focar(_evento):
            nonlocal em_foco
            em_foco = True
            self.configure(border_color=tema.DESTAQUE)
            self.placeholder.place_forget()

        def ao_sair(_evento):
            nonlocal em_foco
            em_foco = False
            self.configure(border_color=tema.BORDA)
            atualizar_placeholder()

        self.entrada.bind("<FocusIn>", ao_focar)
        self.entrada.bind("<FocusOut>", ao_sair)
        pesquisa.trace_add("write", atualizar_placeholder)
        atualizar_placeholder()


class FiltrosAlunos(ctk.CTkFrame):
    def __init__(self, pai, atualizar, limpar):
        super().__init__(pai, fg_color="transparent")
        self.opcoes_curso = {}
        self.sel_curso = self._seletor(0, ["Todos os cursos"], atualizar)
        self.sel_faixa = self._seletor(1, [TODAS_FAIXAS, *FAIXAS, SEM_NOTA], atualizar)
        self.sel_desempenho = self._seletor(
            2, [TODOS_DESEMPENHOS, NA_REFERENCIA, ABAIXO_REFERENCIA, SEM_NOTA], atualizar
        )
        ctk.CTkButton(self, text="Limpar filtros", width=95, height=34,
                      command=limpar, **tema.NEUTRO).grid(row=0, column=3)

    def _seletor(self, coluna, valores, atualizar):
        self.grid_columnconfigure(coluna, weight=3 if coluna == 0 else 2, uniform="filtro")
        seletor = ctk.CTkComboBox(
            self, values=valores, state="readonly", width=120, height=34,
            font=tema.fonte(13), dropdown_font=tema.fonte(13), button_color=tema.BORDA,
            dropdown_fg_color=tema.SUPERFICIE, dropdown_hover_color=tema.BORDA,
            dropdown_text_color=tema.TEXTO, command=lambda _: atualizar(), **tema.CAMPO,
        )
        seletor.set(valores[0])
        seletor.grid(row=0, column=coluna, sticky="ew", padx=(0, 8))
        return seletor

    def atualizar_cursos(self, alunos):
        atual = self.opcoes_curso.get(self.sel_curso.get())
        self.opcoes_curso = {nome: codigo for codigo, nome in cursos_disponiveis(alunos).items()}
        neutro = "Todos os cursos"
        while neutro in self.opcoes_curso:
            neutro += " •"
        self.sel_curso.configure(values=[neutro, *self.opcoes_curso])
        self.sel_curso.set(next((nome for nome, codigo in self.opcoes_curso.items()
                                 if codigo == atual), neutro))

    def limpar(self):
        for seletor in (self.sel_curso, self.sel_faixa, self.sel_desempenho):
            seletor.set(seletor.cget("values")[0])

    def aplicar(self, alunos, pesquisa):
        return filtrar_alunos(
            alunos, pesquisa, curso=self.opcoes_curso.get(self.sel_curso.get()),
            faixa=self.sel_faixa.get(), desempenho_selecionado=self.sel_desempenho.get(),
        )
