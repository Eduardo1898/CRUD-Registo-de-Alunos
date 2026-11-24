import random
import sqlite3
import sys

from src.database import BancoAlunos, ErroBancoDemo, ErroMigracao
from src.validators import CURSOS, validar_aluno


SEED = 42
TOTAL_ALUNOS = 50
NOMES = (
    "Alda", "Amaro", "Anira", "Belina", "Cássio", "Dália", "Elian", "Flora",
    "Gael", "Íris", "Juno", "Lívio", "Maíra", "Nalu", "Otávio", "Tainá",
)
SOBRENOMES = (
    "Arco do Cedro", "Bruma do Sol", "Canto da Serra", "Fonte Azul",
    "Luar de Âmbar", "Nuvem do Vale", "Pedra Serena", "Vento de Abril",
)


def alunos_ficticios():
    sorteio = random.Random(SEED)
    nomes = sorteio.sample(
        [f"{nome} {sobrenome}" for nome in NOMES for sobrenome in SOBRENOMES],
        TOTAL_ALUNOS,
    )
    for indice, nome in enumerate(nomes):
        idade = sorteio.randint(18, 35)
        curso = CURSOS[indice % len(CURSOS)]
        nota = "" if indice % 7 == 0 else f"{sorteio.randint(0, 100) / 10:.1f}"
        yield validar_aluno(nome, str(idade), curso, nota)


def main():
    try:
        criado = BancoAlunos.gerar_demo(alunos_ficticios())
    except (ErroBancoDemo, ErroMigracao) as erro:
        print(erro, file=sys.stderr)
        return 1
    except (OSError, sqlite3.Error):
        print("Não foi possível preparar o banco demonstrativo. Verifique o arquivo e as permissões.",
              file=sys.stderr)
        return 1
    if criado:
        print(f"{TOTAL_ALUNOS} alunos fictícios cadastrados em data/studenthub_demo.db.")
    else:
        print("O banco demonstrativo já está pronto. Os registros existentes foram preservados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
