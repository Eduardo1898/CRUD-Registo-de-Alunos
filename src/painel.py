from dataclasses import dataclass, field
from statistics import mean
from unicodedata import combining, normalize

from .validators import validar_nota


REFERENCIA = 7
TODAS_FAIXAS = "Todas as notas"
SEM_NOTA = "Sem nota"
TODOS_DESEMPENHOS = "Desempenho"
NA_REFERENCIA = f"Nota ≥ {REFERENCIA}"
ABAIXO_REFERENCIA = f"Nota < {REFERENCIA}"
FAIXAS = {
    "0 a menos de 5": (0, 5),
    "5 a menos de 7": (5, REFERENCIA),
    f"{REFERENCIA} a 10": (REFERENCIA, 11),
}


def chave(texto):
    texto = normalize("NFD", " ".join(texto.casefold().split()))
    return "".join(letra for letra in texto if not combining(letra))


def nota_numerica(nota):
    # Bancos legados podiam gravar notas com vírgula como texto.
    if isinstance(nota, str):
        try:
            nota = validar_nota(nota)
        except ValueError:
            return None
    return nota if isinstance(nota, (float, int)) and 0 <= nota <= 10 else None


def desempenho(nota):
    if nota is None:
        return SEM_NOTA
    return NA_REFERENCIA if nota >= REFERENCIA else ABAIXO_REFERENCIA


def filtrar_alunos(alunos, pesquisa="", *, curso=None, faixa=TODAS_FAIXAS,
                   desempenho_selecionado=TODOS_DESEMPENHOS):
    termo = chave(pesquisa)
    limites = FAIXAS.get(faixa)
    selecionados = []
    for aluno in alunos:
        _, nome, _, curso_aluno, valor = aluno
        if termo not in chave(nome) or (curso is not None and chave(curso_aluno or "") != curso):
            continue
        nota = nota_numerica(valor)
        if desempenho_selecionado != TODOS_DESEMPENHOS and desempenho(nota) != desempenho_selecionado:
            continue
        if faixa == SEM_NOTA and nota is not None:
            continue
        if limites:
            inicio, fim = limites
            if nota is None or not inicio <= nota < fim:
                continue
        selecionados.append(aluno)
    return selecionados


def cursos_disponiveis(alunos):
    cursos = {}
    for _, _, _, curso, _ in alunos:
        if curso and (identificador := chave(curso)):
            cursos.setdefault(identificador, " ".join(curso.split()))
    return dict(sorted(cursos.items()))


@dataclass
class Curso:
    nome: str
    total: int = 0
    notas: list = field(default_factory=list)

    @property
    def media(self):
        return mean(self.notas) if self.notas else None


@dataclass
class Resumo:
    total: int
    media: float | None
    cursos: list
    distintos: int
    avaliados: int
    na_referencia: int

    @property
    def percentual(self):
        return 100 * self.na_referencia / self.avaliados if self.avaliados else None

    @property
    def distribuicao(self):
        return self.na_referencia, self.avaliados - self.na_referencia, self.total - self.avaliados


def resumir(alunos):
    grupos = {}
    notas = []
    total = 0
    for _, _, _, curso, valor in alunos:
        total += 1
        identificador = chave(curso or "")
        grupo = grupos.setdefault(identificador, Curso(" ".join(curso.split()) if identificador else "Sem curso"))
        grupo.total += 1
        nota = nota_numerica(valor)
        if nota is not None:
            grupo.notas.append(nota)
            notas.append(nota)

    cursos = [grupos[codigo] for codigo in sorted(grupos, key=lambda codigo: (not codigo, codigo))]
    return Resumo(total, mean(notas) if notas else None, cursos,
                  len(grupos) - int("" in grupos), len(notas), sum(nota >= REFERENCIA for nota in notas))


def calcular_indicadores(alunos):
    resumo = resumir(alunos)
    return resumo.total, resumo.media, resumo.distintos


def formatar_numero(valor, casas=2):
    return "—" if valor is None else f"{valor:.{casas}f}".replace(".", ",")
