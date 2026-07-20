from flask import Flask, render_template_string, request, redirect
import sqlite3

app = Flask(__name__)

# Criar banco
def banco():
    conn = sqlite3.connect("rotinas.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rotinas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

banco()


# Página HTML
pagina = """
<!DOCTYPE html>
<html>
<head>
<title>Controle de Rotinas</title>

<style>
body{
    font-family: Arial;
    margin:40px;
}

.feita{
    color:green;
}

.pendente{
    color:red;
}

button{
    padding:8px;
}
</style>

</head>

<body>

<h1>📋 Controle de Rotinas</h1>


<form method="POST">

<input name="rotina" 
placeholder="Digite uma nova rotina"
size="40">

<button>
Adicionar
</button>

</form>


<hr>


<h2>Rotinas</h2>


{% for r in rotinas %}

<p>

<b>{{r[1]}}</b>

-

{% if r[2]=="Feito" %}

<span class="feita">
✅ Feito
</span>

{% else %}

<span class="pendente">
⏳ Pendente
</span>

{% endif %}


<a href="/alterar/{{r[0]}}">
[Alterar]
</a>


</p>

{% endfor %}


</body>
</html>
"""


@app.route("/", methods=["GET","POST"])
def inicio():

    conn=sqlite3.connect("rotinas.db")
    cursor=conn.cursor()


    if request.method=="POST":

        nome=request.form["rotina"]

        cursor.execute(
        "INSERT INTO rotinas(nome,status) VALUES (?,?)",
        (nome,"Pendente")
        )

        conn.commit()


    cursor.execute(
    "SELECT * FROM rotinas"
    )

    dados=cursor.fetchall()

    conn.close()


    return render_template_string(
        pagina,
        rotinas=dados
    )



@app.route("/alterar/<int:id>")
def alterar(id):

    conn=sqlite3.connect("rotinas.db")
    cursor=conn.cursor()


    cursor.execute(
    "SELECT status FROM rotinas WHERE id=?",
    (id,)
    )

    status=cursor.fetchone()[0]


    novo="Feito" if status=="Pendente" else "Pendente"


    cursor.execute(
    "UPDATE rotinas SET status=? WHERE id=?",
    (novo,id)
    )


    conn.commit()
    conn.close()


    return redirect("/")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)