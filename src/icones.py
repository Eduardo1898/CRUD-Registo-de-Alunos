from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw


# Coordenadas em uma grade de 24 unidades, com traço uniforme.
TRACOS = {
    "educacao": (((2, 9), (12, 4), (22, 9), (12, 14), (2, 9)),
                 ((6, 11), (6, 17), (12, 20), (18, 17), (18, 11)), ((22, 9), (22, 16))),
    "alunos": (((3, 20), (3, 18), (5, 15), (13, 15), (15, 18), (15, 20)),
               ((16, 5), (19, 6), (20, 9), (19, 12), (17, 13)),
               ((18, 15), (20, 16), (22, 18), (22, 20))),
    "media": (((3, 3), (3, 20), (22, 20)),
              ((7, 15), (11, 10), (15, 12), (21, 5)), ((16, 5), (21, 5), (21, 10))),
    "cursos": (((12, 5), (8, 3), (3, 3), (3, 18), (8, 18), (12, 20), (16, 18),
                (21, 18), (21, 3), (16, 3), (12, 5), (12, 20)),),
    "pesquisa": (((15, 15), (21, 21)),),
    "adicionar": (((12, 5), (12, 19)), ((5, 12), (19, 12))),
    "editar": (((4, 16), (16, 4), (20, 8), (8, 20), (3, 21), (4, 16)),
               ((14, 6), (18, 10))),
    "excluir": (((3, 6), (21, 6)), ((9, 6), (9, 3), (15, 3), (15, 6)),
                ((5, 6), (6, 21), (18, 21), (19, 6)), ((10, 10), (10, 17)), ((14, 10), (14, 17))),
    "salvar": (((4, 12), (9, 17), (20, 6)),),
    "banco": (((4, 6), (4, 18)), ((20, 6), (20, 18))),
}
ELIPSES = {
    "alunos": ((5, 4, 13, 12),),
    "pesquisa": ((3, 3, 16, 16),),
}


@lru_cache(maxsize=None)
def _desenhar(nome, cor):
    escala = 5
    imagem = Image.new("RGBA", (24 * escala, 24 * escala))
    desenho = ImageDraw.Draw(imagem)
    largura = 2 * escala
    for traco in TRACOS[nome]:
        pontos = [(x * escala, y * escala) for x, y in traco]
        desenho.line(pontos, fill=cor, width=largura, joint="curve")
    for caixa in ELIPSES.get(nome, ()):
        desenho.ellipse(tuple(ponto * escala for ponto in caixa), outline=cor, width=largura)
    if nome == "banco":
        desenho.ellipse((20, 15, 100, 45), outline=cor, width=largura)
        for y in (50, 75):
            desenho.arc((20, y, 100, y + 30), 0, 180, fill=cor, width=largura)
    return imagem


def icone(nome, cor, tamanho=18):
    imagem = _desenhar(nome, cor)
    return ctk.CTkImage(dark_image=imagem, light_image=imagem, size=(tamanho, tamanho))
