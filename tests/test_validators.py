import unittest

from src.validators import DadosAluno, validar_aluno


class ValidacaoTest(unittest.TestCase):
    def test_normaliza_espacos_e_aceita_curso_legado(self):
        aluno = validar_aluno("  Aluna  Fictícia ", " 020 ", "  Curso  anterior ", " 8,5 ")
        self.assertEqual(aluno, DadosAluno("Aluna Fictícia", 20, "Curso anterior", 8.5))

    def test_nota_opcional_e_limites_inclusivos(self):
        for texto, esperado in [(" ", None), ("0", 0.0), ("10", 10.0), ("8.5", 8.5)]:
            with self.subTest(nota=texto):
                self.assertEqual(validar_aluno("Aluno", "20", "Curso", texto).nota, esperado)

    def test_rejeita_entradas_invalidas(self):
        casos = [
            ("   ", "20", "Curso", ""),
            ("123", "20", "Curso", ""),
            ("Aluno", "0", "Curso", ""),
            ("Aluno", "-1", "Curso", ""),
            ("Aluno", "20.5", "Curso", ""),
            ("Aluno", "²", "Curso", ""),
            ("Aluno", "9223372036854775808", "Curso", ""),
            ("Aluno", "20", " ", ""),
        ]
        casos.extend(("Aluno", "20", "Curso", nota) for nota in (
            "-0,1", "10,00000000000000001", "NaN", "Infinity", "1_0", "1,2,3", "texto",
        ))
        for dados in casos:
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                validar_aluno(*dados)
