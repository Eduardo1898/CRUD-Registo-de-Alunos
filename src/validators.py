from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from unicodedata import decimal


CURSOS = (
    "Análise e Desenvolvimento de Sistemas",
    "Ciência da Computação",
    "Engenharia de Software",
)


@dataclass(frozen=True)
class DadosAluno:
    nome: str
    idade: int
    curso: str
    nota: float | None


def apenas_numeros(texto):
    return not texto or texto.isdecimal()


def validar_aluno(nome, idade, curso, nota):
    nome = " ".join(nome.split())
    if not nome or not any(caractere.isalpha() for caractere in nome):
        raise ValueError("Informe um nome que contenha letras.")

    idade = idade.strip()
    if not idade.isdecimal():
        raise ValueError("Informe uma idade inteira positiva.")
    digitos = "".join(str(decimal(digito)) for digito in idade).lstrip("0")
    if not digitos or len(digitos) > 19 or int(digitos) > 2**63 - 1:
        raise ValueError("Informe uma idade inteira positiva dentro do limite do SQLite.")

    idade = int(digitos)

    curso = " ".join(curso.split())
    if not curso:
        raise ValueError("Informe o curso do aluno.")

    return DadosAluno(nome, idade, curso, validar_nota(nota))


def validar_nota(nota):
    nota = nota.strip()
    if not nota:
        return None
    if not re.fullmatch(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)", nota):
        raise ValueError("Informe uma nota de 0 a 10 ou deixe o campo vazio.")
    try:
        valor = Decimal(nota.replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("Informe uma nota válida.") from erro
    if not 0 <= valor <= 10:
        raise ValueError("Informe uma nota de 0 a 10 ou deixe o campo vazio.")
    return float(valor)
