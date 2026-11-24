import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from src.exportacao import COLUNAS, exportar_alunos


class ExportacaoTest(unittest.TestCase):
    def setUp(self):
        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.raiz = Path(diretorio.name)
        self.alunos = [
            (1, "=1+1", 20, "+Curso fictício", 0),
            (2, "  @Aluno fictício", None, "-Curso fictício", "8,5"),
            (3, "Aluna fictícia", 22, "\tCurso fictício", None),
        ]

    def test_csv_protege_texto_e_preserva_notas_e_idades(self):
        arquivo = self.raiz / "alunos.csv"
        exportar_alunos(self.alunos, arquivo)
        with arquivo.open(encoding="utf-8-sig", newline="") as relatorio:
            linhas = list(csv.reader(relatorio, delimiter=";"))
        self.assertEqual(linhas, [
            list(COLUNAS),
            ["1", "'=1+1", "20", "'+Curso fictício", "0,0"],
            ["2", "'  @Aluno fictício", "", "'-Curso fictício", "8,5"],
            ["3", "Aluna fictícia", "22", "'\tCurso fictício", ""],
        ])

    def test_excel_tem_cabecalho_formatado_e_campos_textuais_sem_formulas(self):
        arquivo = self.raiz / "alunos.xlsx"
        exportar_alunos(self.alunos, arquivo)
        livro = load_workbook(arquivo)
        self.addCleanup(livro.close)
        planilha = livro["Alunos"]
        self.assertEqual(planilha.auto_filter.ref, "A1:E4")
        self.assertEqual(planilha.freeze_panes, "A2")
        self.assertTrue(planilha["A1"].font.bold)
        self.assertEqual(planilha["A1"].fill.patternType, "solid")
        self.assertGreaterEqual(planilha.column_dimensions["D"].width, 28)
        self.assertEqual((planilha["B2"].value, planilha["B2"].data_type), ("=1+1", "s"))
        self.assertEqual((planilha["D2"].value, planilha["D2"].data_type), ("+Curso fictício", "s"))
        self.assertEqual(planilha["E2"].value, 0)
        self.assertEqual((planilha["E3"].value, planilha["E3"].data_type), (8.5, "n"))
        self.assertIsNone(planilha["E4"].value)

    def test_excel_vazio_preserva_cabecalhos(self):
        arquivo = self.raiz / "alunos.xlsx"
        exportar_alunos([], arquivo)
        livro = load_workbook(arquivo)
        self.addCleanup(livro.close)
        planilha = livro["Alunos"]
        self.assertEqual(tuple(planilha.values), (COLUNAS,))
        self.assertEqual(planilha.auto_filter.ref, "A1:E1")

    def test_falha_na_gravacao_preserva_destino_e_limpa_temporario(self):
        arquivo = self.raiz / "alunos.xlsx"
        arquivo.write_bytes(b"relatorio anterior")
        with patch("src.exportacao._escrever_excel", side_effect=OSError), self.assertRaises(OSError):
            exportar_alunos(self.alunos, arquivo)
        self.assertEqual(arquivo.read_bytes(), b"relatorio anterior")
        self.assertEqual(list(self.raiz.iterdir()), [arquivo])
