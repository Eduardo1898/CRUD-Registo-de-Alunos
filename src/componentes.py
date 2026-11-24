import customtkinter as ctk

from . import tema
from .icones import icone


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
