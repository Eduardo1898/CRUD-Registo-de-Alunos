import sqlite3
from tkinter import *
from tkinter import messagebox, ttk


def conectar_banco():
    conexao = sqlite3.connect("sistema_alunos.db")
    cursor = conexao.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER,
            curso TEXT
        )
    """
    )
    conexao.commit()
    return conexao, cursor


def limpar_campos():
    entry_nome.delete(0, END)
    entry_idade.delete(0, END)
    entry_curso.set("")
    lbl_id_val.config(text="")


def atualizar_tabela():
    for linha in tabela.get_children():
        tabela.delete(linha)

    con, cursor = conectar_banco()
    cursor.execute("SELECT * FROM alunos")
    dados = cursor.fetchall()

    for row in dados:
        tabela.insert("", END, values=row)

    con.close()


def apenas_numeros(texto):
    if texto == "" or texto.isdigit():
        return True
    return False

def salvar_aluno():
    nome = entry_nome.get()
    idade = entry_idade.get()
    curso = entry_curso.get()
    id_aluno = lbl_id_val.cget("text")

    if nome == "" or idade == "" or curso == "":
        messagebox.showwarning("Aviso", "Por favor, preencha todos os campos!")
        return

    con, cursor = conectar_banco()

    if id_aluno == "": 
        cursor.execute(
            "INSERT INTO alunos (nome, idade, curso) VALUES (?, ?, ?)",
            (nome, idade, curso),
        )
        messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")
    else: 
        cursor.execute(
            "UPDATE alunos SET nome=?, idade=?, curso=? WHERE id=?",
            (nome, idade, curso, id_aluno),
        )
        messagebox.showinfo("Sucesso", "Dados do aluno atualizados!")

    con.commit()
    con.close()
    limpar_campos()
    atualizar_tabela()


def deletar_aluno():
    id_aluno = lbl_id_val.cget("text")

    if id_aluno == "":
        messagebox.showwarning(
            "Aviso", "Selecione um aluno na tabela para deletar!"
        )
        return

    if messagebox.askyesno(
        "Confirmação", "Tem certeza que deseja deletar este aluno?"
    ):
        con, cursor = conectar_banco()
        cursor.execute("DELETE FROM alunos WHERE id=?", (id_aluno,))
        con.commit()
        con.close()
        limpar_campos()
        atualizar_tabela()


def selecionar_aluno(event):
    limpar_campos()
    item_selecionado = tabela.selection()[0]
    valores = tabela.item(item_selecionado, "values")

    lbl_id_val.config(text=valores[0])
    entry_nome.insert(0, valores[1])
    entry_idade.insert(0, valores[2])
    entry_curso.insert(0, valores[3])


janela = Tk()
janela.title("Sistema de Cadastro de Alunos (CRUD)")
janela.geometry("700x550")
janela.resizable(False, False)

estilo = ttk.Style()
estilo.theme_use("clam")

frame_campos = ttk.LabelFrame(
    janela, text=" Dados do Aluno ", padding=10
)
frame_campos.pack(fill="x", padx=15, pady=10)

lbl_id = Label(frame_campos, text="ID:", font=("Arial", 10))
lbl_id_val = Label(
    frame_campos, text="", font=("Arial", 10, "bold"), fg="blue"
)

lbl_nome = Label(frame_campos, text="Nome:", font=("Arial", 10))
lbl_nome.grid(row=1, column=0, sticky="w", pady=5)
entry_nome = ttk.Entry(frame_campos, width=50)
entry_nome.grid(row=1, column=1, columnspan=3, sticky="w", pady=5)

lbl_idade = Label(frame_campos, text="Idade:", font=("Arial", 10))
lbl_idade.grid(row=2, column=0, sticky="w", pady=5)
valida_num = janela.register(apenas_numeros)
entry_idade = ttk.Entry(frame_campos, width=10, validate = "key", validatecommand=(valida_num, "%P"))
entry_idade.grid(row=2, column=1, sticky="w", pady=5)

lbl_curso = Label(frame_campos, text="Curso:", font=("Arial", 10))
lbl_curso.grid(row=2, column=2, sticky="w", padx=(20, 5), pady=5)
opcoes_cursos = ["Análise e Desenvolvimento de Sistemas",
                 "Ciência da Computação",
                 "Engenharia de Software"]
entry_curso = ttk.Combobox(frame_campos, value=opcoes_cursos, width=38, state="readonly")
entry_curso.grid(row=2, column=3, sticky="w", pady=5)

frame_botoes = Frame(janela)
frame_botoes.pack(fill="x", padx=15, pady=10)

btn_salvar = ttk.Button(
    frame_botoes, text="Salvar / Atualizar", command=salvar_aluno
)
btn_salvar.pack(side="left", padx=5)

btn_deletar = ttk.Button(frame_botoes, text="Deletar", command=deletar_aluno)
btn_deletar.pack(side="left", padx=5)

btn_limpar = ttk.Button(
    frame_botoes, text="Limpar Campos", command=limpar_campos
)
btn_limpar.pack(side="left", padx=5)

frame_tabela = ttk.LabelFrame(
    janela, text=" Alunos Cadastrados ", padding=5
)
frame_tabela.pack(fill="both", expand=True, padx=15, pady=10)

colunas = ("id", "nome", "idade", "curso")
tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

tabela.heading("id", text="ID")
tabela.heading("nome", text="Nome")
tabela.heading("idade", text="Idade")
tabela.heading("curso", text="Curso")

tabela.column("id", width=50, anchor="center")
tabela.column("nome", width=250)
tabela.column("idade", width=70, anchor="center")
tabela.column("curso", width=200)

scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
tabela.configure(yscrollcommand=scroll.set)

tabela.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

tabela.bind("<<TreeviewSelect>>", selecionar_aluno)

atualizar_tabela()

janela.mainloop()