from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime, date

app = Flask(__name__)

DB = "rotinas.db"
SETORES = ["PCP";", "Produção", "Qualidade", "Manutenção", "Logística"]
PRIORIDADES = ["Baixa", "Média", "Alta"]


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rotinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        setor TEXT NOT NULL,
        prioridade TEXT NOT NULL,
        status TEXT NOT NULL,
        data_criacao TEXT NOT NULL,
        prazo TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
BASE_STYLE = """
<style>
    :root{
        --bg:#f4f6fb;
        --card:#ffffff;
        --texto:#1f2937;
        --texto-suave:#6b7280;
        --azul:#4f46e5;
        --azul-claro:#eef2ff;
        --verde:#16a34a;
        --verde-claro:#ecfdf5;
        --vermelho:#dc2626;
        --vermelho-claro:#fef2f2;
        --laranja:#d97706;
        --laranja-claro:#fffbeb;
        --borda:#e5e7eb;
        --sombra: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    }

    *{ box-sizing:border-box; }

    body{
        margin:0;
        font-family:'Segoe UI', Arial, sans-serif;
        background:var(--bg);
        color:var(--texto);
        padding:24px;
    }

    .container{
        max-width:1000px;
        margin:0 auto;
    }

    header h1{
        font-size:1.6rem;
        margin-bottom:4px;
    }

    header p{
        color:var(--texto-suave);
        margin-top:0;
        margin-bottom:24px;
    }

    /* Dashboard */
    .dashboard{
        display:grid;
        grid-template-columns:repeat(4, 1fr);
        gap:16px;
        margin-bottom:28px;
    }

    .card{
        background:var(--card);
        border-radius:14px;
        padding:18px;
        box-shadow:var(--sombra);
        border:1px solid var(--borda);
    }

    .card .valor{
        font-size:1.7rem;
        font-weight:700;
    }

    .card .rotulo{
        color:var(--texto-suave);
        font-size:0.85rem;
        margin-top:4px;
    }

    .card.total .valor{ color:var(--azul); }
    .card.concluidas .valor{ color:var(--verde); }
    .card.pendentes .valor{ color:var(--laranja); }
    .card.percentual .valor{ color:#7c3aed; }

    .barra-progresso{
        width:100%;
        height:8px;
        background:var(--borda);
        border-radius:6px;
        overflow:hidden;
        margin-top:10px;
    }

    .barra-progresso .preenchido{
        height:100%;
        background:var(--verde);
        border-radius:6px;
    }

    /* Formulário */
    .form-card{
        background:var(--card);
        border-radius:14px;
        padding:20px;
        box-shadow:var(--sombra);
        border:1px solid var(--borda);
        margin-bottom:28px;
    }

    .form-card h2{
        margin-top:0;
        font-size:1.1rem;
    }

    .form-grid{
        display:grid;
        grid-template-columns:2fr 1fr 1fr 1fr auto;
        gap:10px;
        align-items:end;
    }

    .campo label{
        display:block;
        font-size:0.8rem;
        color:var(--texto-suave);
        margin-bottom:4px;
    }

    input, select{
        width:100%;
        padding:9px 10px;
        border:1px solid var(--borda);
        border-radius:8px;
        font-size:0.9rem;
        background:#fff;
        color:var(--texto);
    }

    button, .btn{
        padding:9px 16px;
        border:none;
        border-radius:8px;
        background:var(--azul);
        color:#fff;
        font-weight:600;
        cursor:pointer;
        font-size:0.9rem;
        text-decoration:none;
        display:inline-block;
        text-align:center;
    }

    button:hover, .btn:hover{ opacity:0.9; }

    /* Lista de rotinas */
    .lista h2{
        font-size:1.1rem;
        margin-bottom:12px;
    }

    .rotina{
        background:var(--card);
        border:1px solid var(--borda);
        border-radius:12px;
        padding:14px 16px;
        margin-bottom:10px;
        box-shadow:var(--sombra);
        display:flex;
        justify-content:space-between;
        align-items:center;
        gap:12px;
        flex-wrap:wrap;
    }

    .rotina.feita{ opacity:0.7; }

    .rotina .info{ flex:1; min-width:200px; }

    .rotina .nome{
        font-weight:600;
        font-size:1rem;
        margin-bottom:4px;
    }

    .rotina.feita .nome{ text-decoration:line-through; }

    .meta{
        display:flex;
        gap:8px;
        flex-wrap:wrap;
        font-size:0.78rem;
    }

    .tag{
        padding:3px 9px;
        border-radius:999px;
        font-weight:600;
    }

    .tag.setor{ background:var(--azul-claro); color:var(--azul); }

    .tag.prioridade-baixa{ background:var(--verde-claro); color:var(--verde); }
    .tag.prioridade-média{ background:var(--laranja-claro); color:var(--laranja); }
    .tag.prioridade-alta{ background:var(--vermelho-claro); color:var(--vermelho); }

    .tag.status-feito{ background:var(--verde-claro); color:var(--verde); }
    .tag.status-pendente{ background:var(--laranja-claro); color:var(--laranja); }
    .tag.status-atrasado{ background:var(--vermelho-claro); color:var(--vermelho); }

    .acoes{
        display:flex;
        gap:6px;
        flex-wrap:wrap;
    }

    .acoes a{
        padding:6px 10px;
        border-radius:7px;
        font-size:0.8rem;
        text-decoration:none;
        font-weight:600;
    }

    .acoes .concluir{ background:var(--verde-claro); color:var(--verde); }
    .acoes .editar{ background:var(--azul-claro); color:var(--azul); }
    .acoes .excluir{ background:var(--vermelho-claro); color:var(--vermelho); }

    .vazio{
        text-align:center;
        color:var(--texto-suave);
        padding:30px 0;
    }

    @media (max-width:700px){
        .dashboard{ grid-template-columns:repeat(2, 1fr); }
        .form-grid{ grid-template-columns:1fr; }
        body{ padding:14px; }
    }
</style>
"""

PAGINA_INICIO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Controle de Rotinas</title>
""" + BASE_STYLE + """
</head>
<body>
<div class="container">

<header>
    <h1>📋 Controle de Rotinas</h1>
    <p>Acompanhamento das rotinas do setor</p>
</header>

<section class="dashboard">
    <div class="card total">
        <div class="valor">{{ total }}</div>
        <div class="rotulo">📊 Total de rotinas</div>
    </div>
    <div class="card concluidas">
        <div class="valor">{{ concluidas }}</div>
        <div class="rotulo">✅ Concluídas</div>
    </div>
    <div class="card pendentes">
        <div class="valor">{{ pendentes }}</div>
        <div class="rotulo">⏳ Pendentes</div>
    </div>
    <div class="card percentual">
        <div class="valor">{{ percentual }}%</div>
        <div class="rotulo">📈 Percentual concluído</div>
        <div class="barra-progresso">
            <div class="preenchido" style="width:{{ percentual }}%;"></div>
        </div>
    </div>
</section>

<section class="form-card">
    <h2>➕ Nova rotina</h2>
    <form method="POST" action="/criar">
        <div class="form-grid">
            <div class="campo">
                <label>Rotina</label>
                <input name="nome" placeholder="Ex: Enviar relatório de produção" required>
            </div>
            <div class="campo">
                <label>Setor</label>
                <select name="setor">
                    {% for s in setores %}
                    <option value="{{ s }}">{{ s }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="campo">
                <label>Prioridade</label>
                <select name="prioridade">
                    {% for p in prioridades %}
                    <option value="{{ p }}" {% if p=="Média" %}selected{% endif %}>{{ p }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="campo">
                <label>Prazo</label>
                <input type="date" name="prazo">
            </div>
            <div class="campo">
                <button type="submit">Adicionar</button>
            </div>
        </div>
    </form>
</section>

<section class="lista">
    <h2>Rotinas</h2>

    {% if not rotinas %}
        <div class="vazio">Nenhuma rotina cadastrada ainda.</div>
    {% endif %}

    {% for r in rotinas %}
    <div class="rotina {% if r['status']=='Feito' %}feita{% endif %}">
        <div class="info">
            <div class="nome">{{ r['nome'] }}</div>
            <div class="meta">
                <span class="tag setor">{{ r['setor'] }}</span>
                <span class="tag prioridade-{{ r['prioridade']|lower }}">{{ r['prioridade'] }}</span>

                {% if r['status']=='Feito' %}
                    <span class="tag status-feito">✅ Feito</span>
                {% elif r['atrasada'] %}
                    <span class="tag status-atrasado">🔴 Atrasada</span>
                {% else %}
                    <span class="tag status-pendente">⏳ Pendente</span>
                {% endif %}

                <span class="tag setor">🕒 criada em {{ r['data_criacao'] }}</span>

                {% if r['prazo'] %}
                <span class="tag setor">📅 prazo {{ r['prazo'] }}</span>
                {% endif %}
            </div>
        </div>
        <div class="acoes">
            <a class="concluir" href="/concluir/{{ r['id'] }}">
                {% if r['status']=='Feito' %}↩ Reabrir{% else %}✔ Concluir{% endif %}
            </a>
            <a class="editar" href="/editar/{{ r['id'] }}">✎ Editar</a>
            <a class="excluir" href="/excluir/{{ r['id'] }}" onclick="return confirm('Excluir esta rotina?');">🗑 Excluir</a>
        </div>
    </div>
    {% endfor %}
</section>

</div>
</body>
</html>
"""

PAGINA_EDITAR = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Editar rotina</title>
""" + BASE_STYLE + """
</head>
<body>
<div class="container">

<header>
    <h1>✎ Editar rotina</h1>
    <p><a class="btn" style="background:var(--texto-suave);" href="/">← Voltar</a></p>
</header>

<section class="form-card">
    <form method="POST">
        <div class="campo" style="margin-bottom:12px;">
            <label>Rotina</label>
            <input name="nome" value="{{ r['nome'] }}" required>
        </div>

        <div class="campo" style="margin-bottom:12px;">
            <label>Setor</label>
            <select name="setor">
                {% for s in setores %}
                <option value="{{ s }}" {% if s==r['setor'] %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="campo" style="margin-bottom:12px;">
            <label>Prioridade</label>
            <select name="prioridade">
                {% for p in prioridades %}
                <option value="{{ p }}" {% if p==r['prioridade'] %}selected{% endif %}>{{ p }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="campo" style="margin-bottom:16px;">
            <label>Prazo</label>
            <input type="date" name="prazo" value="{{ r['prazo'] or '' }}">
        </div>

        <button type="submit">Salvar alterações</button>
    </form>
</section>

</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.route("/")
def inicio():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rotinas ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()

    hoje = date.today().isoformat()

    rotinas = []
    for r in dados:
        item = dict(r)
        item["atrasada"] = bool(
            item["status"] == "Pendente" and item["prazo"] and item["prazo"] < hoje
        )
        rotinas.append(item)

    total = len(rotinas)
    concluidas = sum(1 for r in rotinas if r["status"] == "Feito")
    pendentes = total - concluidas
    percentual = round((concluidas / total) * 100) if total else 0

    return render_template_string(
        PAGINA_INICIO,
        rotinas=rotinas,
        total=total,
        concluidas=concluidas,
        pendentes=pendentes,
        percentual=percentual,
        setores=SETORES,
        prioridades=PRIORIDADES,
    )


@app.route("/criar", methods=["POST"])
def criar():
    nome = request.form["nome"].strip()
    setor = request.form.get("setor", SETORES[0])
    prioridade = request.form.get("prioridade", "Média")
    prazo = request.form.get("prazo") or None
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    if nome:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO rotinas(nome, setor, prioridade, status, data_criacao, prazo)
               VALUES (?,?,?,?,?,?)""",
            (nome, setor, prioridade, "Pendente", agora, prazo),
        )
        conn.commit()
        conn.close()

    return redirect("/")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_conn()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"].strip()
        setor = request.form.get("setor", SETORES[0])
        prioridade = request.form.get("prioridade", "Média")
        prazo = request.form.get("prazo") or None

        cursor.execute(
            """UPDATE rotinas SET nome=?, setor=?, prioridade=?, prazo=? WHERE id=?""",
            (nome, setor, prioridade, prazo, id),
        )
        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT * FROM rotinas WHERE id=?", (id,))
    r = cursor.fetchone()
    conn.close()

    if r is None:
        return redirect("/")

    return render_template_string(
        PAGINA_EDITAR, r=dict(r), setores=SETORES, prioridades=PRIORIDADES
    )


@app.route("/excluir/<int:id>")
def excluir(id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rotinas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/concluir/<int:id>")
def concluir(id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM rotinas WHERE id=?", (id,))
    row = cursor.fetchone()

    if row:
        novo = "Feito" if row["status"] == "Pendente" else "Pendente"
        cursor.execute("UPDATE rotinas SET status=? WHERE id=?", (novo, id))
        conn.commit()

    conn.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
