from tkinter import ttk


FUNDO = "#0F172A"
LATERAL = "#1E293B"
SUPERFICIE = "#273449"
TEXTO = "#F1F5F9"
SECUNDARIO = "#94A3B8"
DESTAQUE = "#3B82F6"
SUCESSO = "#22C55E"
ERRO = "#EF4444"
BORDA = "#334155"

PRIMARIO = dict(fg_color=DESTAQUE, hover_color="#60A5FA", text_color=FUNDO)
NEUTRO = dict(fg_color=SUPERFICIE, hover_color=BORDA, text_color=TEXTO)
PERIGO = dict(fg_color="#482831", hover_color="#62313C", text_color="#FCA5A5")
CAMPO = dict(fg_color=FUNDO, border_color=BORDA, text_color=TEXTO)


def estilizar_tabela(janela):
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    estilo.configure(
        "StudentHub.Treeview", background=LATERAL, fieldbackground=LATERAL,
        foreground=TEXTO, borderwidth=0, lightcolor=LATERAL, darkcolor=LATERAL,
        bordercolor=LATERAL, rowheight=42,
    )
    estilo.configure(
        "StudentHub.Treeview.Heading", background=SUPERFICIE, foreground=TEXTO,
        borderwidth=0, padding=(10, 12), font=("TkDefaultFont", 10, "bold"),
    )
    estilo.map("StudentHub.Treeview.Heading", background=[("active", SUPERFICIE)])
    estilo.map("StudentHub.Treeview", background=[("selected", "#1D4A81")],
               foreground=[("selected", TEXTO)])
