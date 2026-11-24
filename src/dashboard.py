import textwrap

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from . import tema
from .painel import REFERENCIA, formatar_numero


class Dashboard(ctk.CTkScrollableFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color=tema.FUNDO, corner_radius=0,
                         scrollbar_button_color=tema.BORDA)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

    def atualizar(self, resumo):
        for widget in self.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self, text="Desempenho acadêmico", font=tema.fonte(32, "bold"),
                     text_color=tema.TEXTO).grid(row=0, column=0, columnspan=2, sticky="w")
        ctk.CTkLabel(
            self, text=f"Nota {REFERENCIA} como referência demonstrativa de desempenho.",
            font=tema.fonte(), text_color=tema.SECUNDARIO,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 15))

        faixa = ctk.CTkFrame(self, fg_color="transparent")
        faixa.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 6), pady=(0, 15))
        percentual = formatar_numero(resumo.percentual, 1)
        if resumo.percentual is not None:
            percentual += "%"
        indicadores = (
            ("Média geral", formatar_numero(resumo.media), tema.SUCESSO),
            ("Alunos avaliados", str(resumo.avaliados), tema.AZUL_CLARO),
            (f"Avaliados com nota ≥ {REFERENCIA}", percentual, tema.AMETISTA),
        )
        for coluna, (titulo, valor, cor) in enumerate(indicadores):
            faixa.grid_columnconfigure(coluna, weight=1, uniform="indicador")
            card = ctk.CTkFrame(faixa, fg_color=tema.LATERAL, border_width=1, border_color=tema.BORDA)
            card.grid(row=0, column=coluna, sticky="ew", padx=(0, 10 if coluna < 2 else 0))
            ctk.CTkLabel(card, text=titulo, text_color=tema.SECUNDARIO,
                         font=tema.fonte(13)).pack(anchor="w", padx=13, pady=(8, 0))
            ctk.CTkLabel(card, text=valor, text_color=cor,
                         font=tema.fonte(29, "bold")).pack(anchor="w", padx=13, pady=(0, 6))

        altura = max(235, 42 * len(resumo.cursos) + 55)
        eixos = self._grafico("Alunos por curso", 3, 0, altura, margem=(0, 10))
        _barras(eixos, [(curso.nome, curso.total) for curso in resumo.cursos],
                tema.DESTAQUE, "Nenhum aluno cadastrado")
        eixos.xaxis.set_major_locator(MaxNLocator(integer=True))

        eixos = self._grafico("Distribuição de desempenho", 3, 1, altura)
        _rosca(eixos, resumo)

        eixos = self._grafico("Média das notas por curso", 4, 0, altura, colunas=2)
        medias = [(curso.nome, curso.media) for curso in resumo.cursos if curso.media is not None]
        _barras(eixos, medias, tema.AMETISTA, "Nenhum curso com notas preenchidas", notas=True)

    def _grafico(self, titulo, linha, coluna, altura, *, colunas=1, margem=(0, 6)):
        cartao = ctk.CTkFrame(self, fg_color=tema.LATERAL, border_width=1, border_color=tema.BORDA)
        cartao.grid(row=linha, column=coluna, columnspan=colunas, sticky="nsew",
                    padx=margem, pady=(0, 12))
        ctk.CTkLabel(cartao, text=titulo, text_color=tema.TEXTO,
                     font=tema.fonte(16, "bold")).pack(anchor="w", padx=15, pady=(10, 0))
        figura = Figure(figsize=(2.2, altura / 100), dpi=100, facecolor=tema.LATERAL,
                        layout="constrained")
        canvas = FigureCanvasTkAgg(figura, master=cartao)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=7, pady=(0, 6))
        return figura.add_subplot()


def _eixos_escuros(eixos):
    eixos.set_facecolor(tema.LATERAL)
    eixos.tick_params(axis="both", colors=tema.SECUNDARIO, length=0, labelsize=9)
    for borda in eixos.spines.values():
        borda.set_visible(False)


def _vazio(eixos, mensagem):
    eixos.set_axis_off()
    eixos.text(0.5, 0.5, mensagem, color=tema.SECUNDARIO, ha="center",
               va="center", transform=eixos.transAxes)


def _barras(eixos, dados, cor, mensagem_vazia, *, notas=False):
    _eixos_escuros(eixos)
    if not dados:
        _vazio(eixos, mensagem_vazia)
        return
    nomes, valores = zip(*dados)
    indices = range(len(nomes))
    eixos.barh(indices, valores, color=cor, height=0.55)
    eixos.set_yticks(indices, [textwrap.fill(nome, width=23) for nome in nomes])
    eixos.invert_yaxis()
    eixos.set_axisbelow(True)
    eixos.grid(axis="x", color=tema.BORDA, alpha=0.45)
    if notas:
        eixos.set_xlim(0, 10)
        eixos.set_xticks(range(0, 11, 2))
    else:
        eixos.set_xlim(0, max(valores) * 1.1)


def _rosca(eixos, resumo):
    if not resumo.total:
        _vazio(eixos, "Nenhum aluno cadastrado")
        return
    rotulos = (f"Nota ≥ {REFERENCIA}", f"Nota < {REFERENCIA}", "Sem nota")
    cores = (tema.SUCESSO, tema.AMETISTA, tema.SECUNDARIO)
    fatias, _ = eixos.pie(
        resumo.distribuicao, colors=cores, startangle=90,
        wedgeprops={"width": 0.33, "edgecolor": tema.LATERAL},
    )
    eixos.text(0, 0, str(resumo.total), ha="center", va="center",
               fontsize=16, color=tema.TEXTO)
    eixos.legend(fatias, [f"{rotulo} · {total}" for rotulo, total in zip(rotulos, resumo.distribuicao)],
                 loc="upper center", bbox_to_anchor=(0.5, 0), frameon=False,
                 labelcolor=tema.SECUNDARIO, fontsize=8, ncols=1)
