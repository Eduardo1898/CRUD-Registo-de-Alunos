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

## Modo demonstrativo

No Windows PowerShell, execute estes comandos na raiz do repositório:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.seed_demo
.\.venv\Scripts\python.exe -m src.app --demo
```

Se o ambiente virtual já estiver criado e as dependências instaladas, execute apenas as duas últimas linhas. O script cria 50 alunos fictícios com uma seed fixa em `data/studenthub_demo.db`. Ao executá-lo novamente, os registros existentes no banco demonstrativo são preservados, inclusive as edições feitas no aplicativo.

A opção `--demo` identifica o modo na barra de título. Para abrir o banco de uso normal, execute o aplicativo sem essa opção. As futuras capturas de tela do projeto serão armazenadas em `docs/images/`.

## Filtros, relatórios e desempenho

Na lista de alunos, combine a pesquisa por nome com os filtros de curso, faixa de notas e desempenho. **Sem nota** inclui registros em branco ou notas legadas inválidas. **Limpar filtros** redefine os seletores e a pesquisa. Os três indicadores da lista acompanham todo o cadastro.

Em **Exportar**, escolha CSV ou Excel e selecione todos os alunos ou apenas os resultados atuais. As notas preenchidas são exportadas como números, com as ausentes em branco. O CSV usa UTF-8 com BOM, ponto e vírgula e vírgula decimal. O Excel inclui um cabeçalho fixo, filtros e colunas formatadas. Os arquivos são salvos no destino escolhido.

A página **Desempenho** mostra a média geral, a quantidade de alunos avaliados e o percentual de avaliados com nota igual ou superior a 7. Os gráficos apresentam a quantidade de alunos por curso, a distribuição de desempenho (incluindo alunos sem nota) e as médias por curso. A nota 7 é uma referência demonstrativa. Alunos sem nota válida ficam fora das médias e do denominador do percentual.

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

O workflow de GitHub Actions executa a suíte com Xvfb no Linux em pushes e pull requests, com Python 3.12 e 3.13.
