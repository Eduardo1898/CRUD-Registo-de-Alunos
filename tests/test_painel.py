import unittest

from src.painel import (
    ABAIXO_REFERENCIA, NA_REFERENCIA, SEM_NOTA, calcular_indicadores, filtrar_alunos, resumir,
)


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


class DesempenhoTest(unittest.TestCase):
    def setUp(self):
        self.alunos = [
            (1, "Ágata Fictícia", 20, "Ciência", 0),
            (2, "Bruno Fictício", 21, "Ciencia", 4.999),
            (3, "Carla Fictícia", 22, "Ciência", 5),
            (4, "Daniel Fictício", 23, "Ciência", "7,0"),
            (5, "Eva Fictícia", 21, "História", 10),
            (6, "Fábio Fictício", 21, "História", None),
            (7, "Gina Fictícia", 21, None, "pendente"),
        ]

    def test_filtros_combinados_e_limites(self):
        def ids(pesquisa="", **filtros):
            return [aluno[0] for aluno in filtrar_alunos(self.alunos, pesquisa, **filtros)]

        self.assertEqual(ids("ficticio", curso="ciencia", faixa="7 a 10",
                             desempenho_selecionado=NA_REFERENCIA), [4])
        self.assertEqual(ids(faixa="0 a menos de 5"), [1, 2])
        self.assertEqual(ids(faixa="5 a menos de 7"), [3])
        self.assertEqual(ids(faixa="7 a 10"), [4, 5])
        self.assertEqual(ids(faixa=SEM_NOTA), [6, 7])
        self.assertEqual(ids(desempenho_selecionado=SEM_NOTA), [6, 7])
        self.assertEqual(ids(faixa=SEM_NOTA, desempenho_selecionado=ABAIXO_REFERENCIA), [])

    def test_indicadores_e_medias_por_curso(self):
        resumo = resumir(self.alunos)
        self.assertEqual((resumo.total, resumo.avaliados, resumo.distintos), (7, 5, 2))
        self.assertAlmostEqual(resumo.media, 26.999 / 5)
        self.assertEqual(resumo.percentual, 40)
        self.assertEqual(resumo.distribuicao, (2, 3, 2))
        self.assertEqual([(curso.nome, curso.total) for curso in resumo.cursos],
                         [("Ciência", 4), ("História", 2), ("Sem curso", 1)])
        self.assertEqual([curso.media for curso in resumo.cursos], [16.999 / 4, 10, None])

        for alunos, distribuicao in [((), (0, 0, 0)), (self.alunos[-2:], (0, 0, 2))]:
            with self.subTest(distribuicao=distribuicao):
                resumo = resumir(alunos)
                self.assertIsNone(resumo.media)
                self.assertIsNone(resumo.percentual)
                self.assertEqual(resumo.distribuicao, distribuicao)
