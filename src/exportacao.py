from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .painel import nota_numerica


COLUNAS = ("ID", "Nome", "Idade", "Curso", "Nota")


def _texto_csv(valor):
    if isinstance(valor, str):
        inicio = valor.lstrip().lstrip("\ufeff").lstrip()
        if valor.startswith(("\t", "\r", "\n")) or inicio.startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠")):
            return "'" + valor
    return valor


def exportar_alunos(alunos, caminho):
    caminho = Path(caminho)
    extensao = caminho.suffix.lower()
    if extensao not in (".csv", ".xlsx"):
        raise ValueError("Selecione um arquivo CSV ou Excel (.xlsx).")

    linhas = [(id_aluno, nome, idade, curso, nota_numerica(nota))
              for id_aluno, nome, idade, curso, nota in alunos]
    dados = pd.DataFrame(linhas, columns=COLUNAS, dtype=object).astype({"Nota": "Float64"})
    # Escreve ao lado do destino para preservar o arquivo anterior caso a gravação falhe.
    with NamedTemporaryFile(dir=caminho.parent, suffix=extensao, delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        if extensao == ".csv":
            for coluna in ("Nome", "Idade", "Curso"):
                dados[coluna] = pd.Series((_texto_csv(valor) for valor in dados[coluna]), dtype=object)
            dados.to_csv(temporario, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        else:
            _escrever_excel(dados, temporario)
        temporario.replace(caminho)
    finally:
        temporario.unlink(missing_ok=True)


def _escrever_excel(dados, caminho):
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        dados.to_excel(escritor, sheet_name="Alunos", index=False)
        planilha = escritor.sheets["Alunos"]
        planilha.freeze_panes = "A2"
        planilha.auto_filter.ref = planilha.dimensions
        planilha.row_dimensions[1].height = 27
        for celula in planilha[1]:
            celula.fill = PatternFill("solid", fgColor="1E3A5F")
            celula.font = Font(color="FFFFFF", bold=True)
            celula.alignment = Alignment(vertical="center")
        for coluna in (2, 3, 4):
            # Força campos textuais a permanecerem texto, inclusive se começarem com "=".
            for (celula,) in planilha.iter_rows(min_row=2, min_col=coluna, max_col=coluna):
                if isinstance(celula.value, str):
                    celula.data_type = "s"
        for (celula,) in planilha.iter_rows(min_row=2, min_col=5, max_col=5):
            celula.number_format = "0.00"
        for indice, minimo in enumerate((10, 24, 12, 28, 12), start=1):
            letra = get_column_letter(indice)
            comprimento = max(len(str(celula.value or "")) for celula in planilha[letra])
            planilha.column_dimensions[letra].width = max(minimo, min(60, comprimento + 4))
