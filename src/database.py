from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory


RAIZ = Path(__file__).resolve().parents[1]
NOME_BANCO = "sistema_alunos.db"
BANCO_PADRAO = RAIZ / "data" / NOME_BANCO
BANCOS_LEGADOS = (RAIZ / "trabalhoPythonCrud" / NOME_BANCO, RAIZ / NOME_BANCO)


class ErroMigracao(Exception):
    pass


class BancoAlunos:
    def __init__(self, caminho=None, *, legado=None):
        self.caminho = Path(caminho).resolve() if caminho is not None else BANCO_PADRAO
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

        if legado is not None:
            self._importar(Path(legado).resolve())
        elif caminho is None and not self.caminho.exists():
            fontes = [fonte for fonte in BANCOS_LEGADOS if fonte.is_file()]
            if len(fontes) > 1:
                raise ErroMigracao("Há dois bancos legados. Escolha a origem com --banco-legado.")
            if fontes:
                self._importar(fontes[0], automatico=True)

        with closing(sqlite3.connect(self.caminho)) as conexao:
            self._migrar_esquema(conexao)

    def _importar(self, origem, *, automatico=False):
        if self.caminho.exists():
            if automatico:
                return
            raise ErroMigracao("O banco em data já existe. A importação preservou ambos os arquivos.")
        if not origem.is_file():
            raise ErroMigracao("O arquivo de banco legado informado não existe.")

        # O backup do SQLite inclui transações já gravadas no WAL.
        with TemporaryDirectory(dir=self.caminho.parent) as diretorio:
            copia = Path(diretorio) / NOME_BANCO
            with closing(sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True)) as fonte:
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

    def cadastrar(self, aluno):
        with self._transacao() as conexao:
            cursor = conexao.execute(
                "INSERT INTO alunos (nome, idade, curso, nota) VALUES (?, ?, ?, ?)",
                (aluno.nome, aluno.idade, aluno.curso, aluno.nota),
            )
            return cursor.lastrowid

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
