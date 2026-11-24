import unittest

from src.painel import calcular_indicadores, filtrar_alunos


class PainelTest(unittest.TestCase):
    def test_media_considera_zero_e_notas_legadas_validas(self):
        alunos = [
            (1, "Ágata Fictícia", 20, "Ciência da Computação", 0),
            (2, "Bruno Fictício", 21, " ciencia da computacao ", "9,0"),
            (3, "Carla Fictícia", 22, "Curso fictício", None),
            (4, "Daniel Fictício", 23, None, "pendente"),
            (5, "Eva Fictícia", 21, "", 11),
        ]
        self.assertEqual(calcular_indicadores(alunos), (5, 4.5, 2))
        self.assertEqual(calcular_indicadores(alunos[2:]), (3, None, 1))
        self.assertEqual(calcular_indicadores([]), (0, None, 0))

    def test_busca_parcial_por_nome_sem_acentos(self):
        alunos = [
            (1, "Ágata Fictícia", 20, "Curso fictício", 9),
            (2, "Bruno Fictício", 21, "Curso Ágata", None),
        ]
        self.assertEqual(filtrar_alunos(alunos, "  AGATA   FIC "), alunos[:1])
        self.assertEqual(filtrar_alunos(alunos, "   "), alunos)
        self.assertEqual(filtrar_alunos(alunos, "Carla"), [])
