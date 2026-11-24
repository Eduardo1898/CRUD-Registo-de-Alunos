from statistics import mean
from unicodedata import combining, normalize

from .validators import validar_nota


def chave(texto):
    texto = normalize("NFD", " ".join(texto.casefold().split()))
    return "".join(letra for letra in texto if not combining(letra))


def filtrar_alunos(alunos, pesquisa):
    termo = chave(pesquisa)
    return [aluno for aluno in alunos if termo in chave(aluno[1])]


def calcular_indicadores(alunos):
    notas = []
    cursos = set()
    for _, _, _, curso, nota in alunos:
        if curso and curso.strip():
            cursos.add(chave(curso))
        if nota is None:
            continue
        if isinstance(nota, str):
            # A versão legada podia gravar notas com vírgula como texto.
            try:
                nota = validar_nota(nota)
            except ValueError:
                continue
        if isinstance(nota, (float, int)) and 0 <= nota <= 10:
            notas.append(nota)
    return len(alunos), mean(notas) if notas else None, len(cursos)
