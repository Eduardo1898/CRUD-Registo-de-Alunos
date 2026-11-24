from contextlib import closing, contextmanager
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory


RAIZ = Path(__file__).resolve().parents[1]
NOME_BANCO = "sistema_alunos.db"
EMPACOTADO = getattr(sys, "frozen", False)


def diretorio_dados():
    if not EMPACOTADO:
        return RAIZ / "data"
    if sys.platform == "win32":
        variavel, padrao = "LOCALAPPDATA", Path.home() / "AppData" / "Local"
    else:
        variavel, padrao = "XDG_DATA_HOME", Path.home() / ".local" / "share"
    caminho = Path(os.environ.get(variavel, ""))
    return (caminho if caminho.is_absolute() else padrao) / "StudentHub"


BANCO_PADRAO = diretorio_dados() / NOME_BANCO
BANCO_DEMO = diretorio_dados() / "studenthub_demo.db"
ID_BANCO_DEMO = 0x5348444D  # SHDM
BANCOS_LEGADOS = (RAIZ / "trabalhoPythonCrud" / NOME_BANCO, RAIZ / NOME_BANCO)


class ErroMigracao(Exception):
    pass


class ErroBancoDemo(Exception):
    pass


class BancoAlunos:
    def __init__(self, caminho=None, *, legado=None):
        self.caminho = Path(caminho).resolve() if caminho is not None else BANCO_PADRAO
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

        if legado is not None:
            self._importar(Path(legado).resolve())
        elif not EMPACOTADO and caminho is None and not self.caminho.exists():
            fontes = [fonte for fonte in BANCOS_LEGADOS if fonte.is_file()]
            if len(fontes) > 1:
                raise ErroMigracao("Há dois bancos legados. Escolha a origem com --banco-legado.")
            if fontes:
                self._importar(fontes[0], automatico=True)

        somente_verificar = EMPACOTADO and self.caminho.exists()
        if somente_verificar:
            uri = self.caminho.as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as conexao:
                self._verificar_esquema_empacotado(conexao, uso_normal=caminho is None)
        else:
            with closing(sqlite3.connect(self.caminho)) as conexao:
                self._migrar_esquema(conexao)

    @classmethod
    def abrir_demo(cls):
        cls._verificar_demo()
        return cls(BANCO_DEMO)

    @classmethod
    def gerar_demo(cls, alunos):
        if BANCO_DEMO.exists() or BANCO_DEMO.is_symlink():
            cls._verificar_demo()
            return False

        BANCO_DEMO.parent.mkdir(parents=True, exist_ok=True)
        # Inicializa em um arquivo temporário e só publica depois do commit.
        with TemporaryDirectory(dir=BANCO_DEMO.parent) as pasta:
            copia = Path(pasta) / BANCO_DEMO.name
            banco = cls(copia)
            with banco._transacao() as conexao:
                conexao.execute("BEGIN IMMEDIATE")
                for aluno in alunos:
                    banco._inserir_aluno(conexao, aluno)
                conexao.execute(f"PRAGMA application_id = {ID_BANCO_DEMO}")
            try:
                BANCO_DEMO.hardlink_to(copia)
            except FileExistsError:
                cls._verificar_demo()
                return False
        return True

    @staticmethod
    def _verificar_demo():
        if BANCO_DEMO.is_symlink():
            raise ErroBancoDemo("O caminho do banco demonstrativo é um link. O arquivo foi preservado.")
        if not BANCO_DEMO.is_file():
            raise ErroBancoDemo("Banco demonstrativo indisponível. Execute python -m scripts.seed_demo.")
        for origem in (BANCO_PADRAO, *BANCOS_LEGADOS):
            if origem.exists() and BANCO_DEMO.samefile(origem):
                raise ErroBancoDemo("O banco demonstrativo aponta para um banco de uso normal.")
        with closing(sqlite3.connect(BANCO_DEMO.as_uri() + "?mode=ro", uri=True)) as conexao:
            (identificador,) = conexao.execute("PRAGMA application_id").fetchone()
        if identificador != ID_BANCO_DEMO:
            raise ErroBancoDemo("O arquivo existente não é um banco demonstrativo do StudentHub. Ele foi preservado.")

    def _importar(self, origem, *, automatico=False):
        if self.caminho.exists():
            if automatico:
                return
            raise ErroMigracao("O banco de destino já existe. A importação preservou ambos os arquivos.")
        if not origem.is_file():
            raise ErroMigracao("O arquivo de banco legado informado não existe.")

        # O backup do SQLite inclui transações já gravadas no WAL.
        with TemporaryDirectory(dir=self.caminho.parent) as diretorio:
            copia = Path(diretorio) / NOME_BANCO
            with closing(sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True)) as fonte:
                if EMPACOTADO and fonte.execute("PRAGMA application_id").fetchone()[0] == ID_BANCO_DEMO:
                    raise ErroMigracao("Use --demo para abrir dados demonstrativos.")
                with closing(sqlite3.connect(copia)) as destino:
                    fonte.backup(destino)
                    destino.execute("PRAGMA journal_mode=DELETE").fetchone()
                    self._migrar_esquema(destino, exigir_tabela=True)

            # Publica a cópia concluída sem substituir um banco criado em paralelo.
            try:
                self.caminho.hardlink_to(copia)
            except FileExistsError as erro:
                if not automatico:
                    raise ErroMigracao("O banco de destino já existe.") from erro

    @staticmethod
    def _verificar_esquema_empacotado(conexao, *, uso_normal):
        if uso_normal and conexao.execute("PRAGMA application_id").fetchone()[0] == ID_BANCO_DEMO:
            raise ErroMigracao("O arquivo indicado para uso normal é demonstrativo. Use --demo.")
        colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(alunos)")}
        if not {"id", "nome", "idade", "curso", "nota"} <= colunas:
            raise ErroMigracao(
                "O banco existente não tem o esquema esperado. Ele foi preservado. "
                "Para importar um banco legado, guarde-o separadamente e use --banco-legado."
            )

    @staticmethod
    def _migrar_esquema(conexao, *, exigir_tabela=False):
        with conexao:
            conexao.execute("BEGIN IMMEDIATE")
            colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(alunos)")}
            if not colunas and not exigir_tabela:
                conexao.execute("""
                    CREATE TABLE alunos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        idade INTEGER,
                        curso TEXT,
                        nota REAL
                    )
                """)
                return
            if not {"id", "nome", "idade", "curso"} <= colunas:
                raise ErroMigracao("O banco não contém uma tabela de alunos compatível.")
            if "nota" not in colunas:
                conexao.execute("ALTER TABLE alunos ADD COLUMN nota REAL")

    @contextmanager
    def _transacao(self):
        with closing(sqlite3.connect(self.caminho.as_uri() + "?mode=rw", uri=True)) as conexao:
            with conexao:
                yield conexao

    def listar(self):
        with self._transacao() as conexao:
            return conexao.execute(
                "SELECT id, nome, idade, curso, nota FROM alunos ORDER BY id"
            ).fetchall()

    @staticmethod
    def _inserir_aluno(conexao, aluno):
        cursor = conexao.execute(
            "INSERT INTO alunos (nome, idade, curso, nota) VALUES (?, ?, ?, ?)",
            (aluno.nome, aluno.idade, aluno.curso, aluno.nota),
        )
        return cursor.lastrowid

    def cadastrar(self, aluno):
        with self._transacao() as conexao:
            return self._inserir_aluno(conexao, aluno)

    def atualizar(self, id_aluno, aluno):
        with self._transacao() as conexao:
            cursor = conexao.execute(
                "UPDATE alunos SET nome=?, idade=?, curso=?, nota=? WHERE id=?",
                (aluno.nome, aluno.idade, aluno.curso, aluno.nota, id_aluno),
            )
            return cursor.rowcount == 1

    def excluir(self, id_aluno):
        with self._transacao() as conexao:
            cursor = conexao.execute("DELETE FROM alunos WHERE id=?", (id_aluno,))
            return cursor.rowcount == 1
