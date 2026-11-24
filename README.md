# StudentHub

Sistema desktop de gestão acadêmica para cadastrar, consultar, atualizar e excluir alunos. A interface em português usa CustomTkinter e SQLite.

A pesquisa filtra a tabela por nome, sem distinção de maiúsculas ou acentos. Os indicadores mostram o total de alunos, a média das notas válidas preenchidas e os cursos distintos de todo o cadastro. A nota é opcional e aceita valores de 0 a 10, com vírgula ou ponto decimal.

## Instalação e execução

Use Python 3.10 ou mais recente com Tkinter e um ambiente gráfico. No Linux, instale o pacote `python3-tk` se o Tkinter estiver ausente. Na raiz do projeto, crie e ative um ambiente virtual:

```sh
python -m venv .venv
source .venv/bin/activate
```

No Windows PowerShell, ative com `.venv\Scripts\Activate.ps1`. Em seguida, instale as dependências e inicie o StudentHub:

```sh
python -m pip install -r requirements.txt
python -m src.app
```

## Banco de dados e migração

O SQLite local fica em `data/sistema_alunos.db`, com caminho calculado a partir do código. A pasta é criada na primeira execução e fica fora do Git.

Se você já usa a versão anterior, feche-a e guarde uma cópia do banco fora do repositório **antes de trocar de branch ou atualizar**, pois o banco deixou de ser versionado. A versão anterior guardava o arquivo no diretório de execução. Procure por `sistema_alunos.db` na raiz do projeto, na antiga pasta `trabalhoPythonCrud/` ou no diretório de onde você executava a aplicação.

Na primeira execução, se ainda não houver banco em `data/`, o aplicativo procura o legado na raiz e na antiga pasta. Se existirem dois bancos nessas localizações ou se a cópia estiver em outro lugar, indique o arquivo desejado na primeira execução:

```sh
python -m src.app --banco-legado "/caminho/para/sistema_alunos.db"
```

A migração usa uma cópia consistente do SQLite, preserva o arquivo de origem e adiciona a coluna `nota` quando ausente. Os registros antigos ficam com nota vazia nesse caso. Se o destino já existir, a importação explícita é recusada para preservar os dados. Se precisar importar outro banco, primeiro feche a aplicação e guarde o destino existente em outro local.

## Testes

Na raiz do projeto, execute:

```sh
python -m unittest discover -s tests -v
```

Os testes usam bancos temporários. Os testes de banco e validação executam sem interface gráfica. Os testes de interface são pulados quando não há display. No Linux com Xvfb instalado, é possível executar a suíte completa em um display virtual:

```sh
xvfb-run -a python -m unittest discover -s tests -v
```
