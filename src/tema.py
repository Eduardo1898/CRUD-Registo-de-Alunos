from tkinter import font, ttk

import customtkinter as ctk


FUNDO = "#0F172A"
LATERAL = "#1E293B"
SUPERFICIE = "#273449"
TEXTO = "#F1F5F9"
SECUNDARIO = "#B5C3D5"
DESTAQUE = "#3B82F6"
AZUL_CLARO = "#93C5FD"
AMETISTA = "#C4B5FD"
SUCESSO = "#22C55E"
ERRO = "#EF4444"
ERRO_TEXTO = "#FCA5A5"
BORDA = "#40516B"
LINHA_ALTERNADA = "#233148"

# O tom mais escuro mantém o contraste do texto branco nos botões azuis.
PRIMARIO = dict(fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF")
NEUTRO = dict(fg_color=SUPERFICIE, hover_color=BORDA, text_color=TEXTO)
PERIGO = dict(fg_color="#482831", hover_color="#62313C", text_color=ERRO_TEXTO)
CAMPO = dict(fg_color=FUNDO, border_color=BORDA, text_color=TEXTO)


def fonte(tamanho=14, peso="normal"):
    return ctk.CTkFont(size=tamanho, weight=peso)


def estilizar_tabela(janela):
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    fonte_sistema = font.nametofont("TkDefaultFont", root=janela).actual("family")
    estilo.configure(
        "StudentHub.Treeview", background=LATERAL, fieldbackground=LATERAL,
        foreground=TEXTO, borderwidth=0, lightcolor=LATERAL, darkcolor=LATERAL,
        bordercolor=LATERAL, rowheight=46, font=(fonte_sistema, 11),
    )
    estilo.configure(
        "StudentHub.Treeview.Heading", background=SUPERFICIE, foreground=TEXTO,
        borderwidth=0, padding=(8, 13), font=(fonte_sistema, 11, "bold"),
    )
    estilo.map("StudentHub.Treeview.Heading", background=[("active", SUPERFICIE)])
    estilo.map("StudentHub.Treeview", background=[("selected", "#1E4D92")],
               foreground=[("selected", "#FFFFFF")])
