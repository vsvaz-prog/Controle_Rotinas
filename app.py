from flask import Flask, render_template_string, request, redirect, url_for
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler   # ← ADICIONA ESSA LINHA
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar o Controle de Rotinas."

DATABASE_URL = os.environ.get("DATABASE_URL")
SETORES = ["PCP", "Produção", "Qualidade", "Desossa", "Miudos", "Expedição", "Compras", "RH", "Financeiro","Outros "]
PRIORIDADES = ["Baixa", "Média", "Alta"]


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
def get_conn():
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rotinas (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        setor TEXT NOT NULL,
        prioridade TEXT NOT NULL,
        status TEXT NOT NULL,
        data_criacao TEXT NOT NULL,
        prazo TEXT,
        fixa TEXT DEFAULT 'Não',
        frequencia TEXT DEFAULT '',
        ultima_geracao TEXT DEFAULT ''
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS controle_sistema (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        criado_em TEXT
    )
    """)

    conn.commit()

    try:
        cursor.execute("""
        ALTER TABLE rotinas 
        ADD COLUMN IF NOT EXISTS fixa TEXT DEFAULT 'Não'
        """)

        cursor.execute("""
        ALTER TABLE rotinas 
        ADD COLUMN IF NOT EXISTS frequencia TEXT DEFAULT ''
        """)

        cursor.execute("""
        ALTER TABLE rotinas 
        ADD COLUMN IF NOT EXISTS ultima_geracao TEXT DEFAULT ''
        """)

        cursor.execute("""
        ALTER TABLE rotinas
        ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id)
        """)

        cursor.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS usuario TEXT
        """)

        conn.commit()

    except Exception as e:
        print("Erro ao alterar tabela:", e)

    # Garante a constraint UNIQUE em usuarios.usuario (separado porque
    # ADD CONSTRAINT não tem IF NOT EXISTS no Postgres)
    try:
        cursor.execute("""
        ALTER TABLE usuarios
        ADD CONSTRAINT usuarios_usuario_key UNIQUE (usuario)
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()

    # Coluna "email" é da versão antiga e não é mais usada — remove a
    # obrigatoriedade dela para não travar novos cadastros
    try:
        cursor.execute("""
        ALTER TABLE usuarios
        ALTER COLUMN email DROP NOT NULL
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()

    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
class Usuario(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.nome = row["nome"]
        self.usuario = row["usuario"]


@login_manager.user_loader
def load_user(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return Usuario(row) if row else None


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
BASE_STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
    :root{
        --bg:#14181c;
        --painel:#1c2329;
        --painel-2:#212a31;
        --borda:#323d47;
        --borda-forte:#455261;
        --texto:#e7eaec;
        --texto-suave:#8b96a1;

        --ambar:#f5a623;
        --ambar-fundo:rgba(245,166,35,0.12);
        --verde:#2ecc71;
        --verde-fundo:rgba(46,204,113,0.12);
        --vermelho:#eb4d4b;
        --vermelho-fundo:rgba(235,77,75,0.14);
        --azul:#4fa3d1;
        --azul-fundo:rgba(79,163,209,0.12);
        --roxo:#9d7ee8;
        --roxo-fundo:rgba(157,126,232,0.14);

        --display:'Oswald', sans-serif;
        --corpo:'Inter', sans-serif;
        --mono:'IBM Plex Mono', monospace;
    }

    *{ box-sizing:border-box; }

    body{
        margin:0;
        font-family:var(--corpo);
        background:
            radial-gradient(ellipse at top, #1a2027 0%, var(--bg) 55%);
        color:var(--texto);
        padding:28px 20px 60px;
    }

    .container{
        max-width:1040px;
        margin:0 auto;
    }

    /* ---------- Cabeçalho tipo placa de painel ---------- */
    header{
        position:relative;
        background:var(--painel);
        border:1px solid var(--borda);
        border-radius:10px;
        padding:22px 26px;
        margin-bottom:26px;
        overflow:hidden;
    }

    header::before{
        content:"";
        position:absolute;
        top:0; left:0; right:0;
        height:3px;
        background:linear-gradient(90deg, var(--ambar) 0%, transparent 60%);
    }

    .rebite{
        position:absolute;
        width:7px; height:7px;
        border-radius:50%;
        background:radial-gradient(circle at 35% 30%, #5a6774, #232b32 70%);
        box-shadow:0 1px 1px rgba(0,0,0,0.6);
    }
    .rebite.tl{ top:10px; left:10px; }
    .rebite.tr{ top:10px; right:10px; }
    .rebite.bl{ bottom:10px; left:10px; }
    .rebite.br{ bottom:10px; right:10px; }

    header .eyebrow{
        font-family:var(--mono);
        font-size:0.72rem;
        letter-spacing:0.18em;
        text-transform:uppercase;
        color:var(--ambar);
        margin:0 0 6px;
    }

    header h1{
        font-family:var(--display);
        text-transform:uppercase;
        letter-spacing:0.03em;
        font-size:1.7rem;
        font-weight:600;
        margin:0 0 4px;
    }

    header p{
        color:var(--texto-suave);
        margin:0;
        font-size:0.88rem;
    }

    /* ---------- Dashboard: contadores de painel ---------- */
    .dashboard{
        display:grid;
        grid-template-columns:repeat(4, 1fr);
        gap:14px;
        margin-bottom:26px;
    }

    .card{
        background:var(--painel);
        border-radius:8px;
        padding:16px 18px;
        border:1px solid var(--borda);
        border-top:2px solid var(--borda-forte);
    }

    .card .rotulo{
        font-family:var(--mono);
        text-transform:uppercase;
        letter-spacing:0.1em;
        color:var(--texto-suave);
        font-size:0.68rem;
        margin-bottom:8px;
    }

    .card .valor{
        font-family:var(--mono);
        font-size:2rem;
        font-weight:600;
        line-height:1;
    }

    .card.total .valor{ color:var(--azul); }
    .card.concluidas .valor{ color:var(--verde); }
    .card.pendentes .valor{ color:var(--ambar); }
    .card.percentual .valor{ color:var(--roxo); }

    .barra-progresso{
        width:100%;
        height:6px;
        background:#0f1317;
        border:1px solid var(--borda);
        border-radius:4px;
        overflow:hidden;
        margin-top:10px;
    }

    .barra-progresso .preenchido{
        height:100%;
        background:repeating-linear-gradient(
            135deg,
            var(--roxo) 0px, var(--roxo) 6px,
            #8064c9 6px, #8064c9 12px
        );
    }

    /* ---------- Formulário: "ordem de serviço" ---------- */
    .form-card{
        background:var(--painel);
        border-radius:8px;
        border:1px solid var(--borda);
        margin-bottom:26px;
        overflow:hidden;
    }

    .form-card .titulo-painel{
        background:var(--painel-2);
        border-bottom:1px solid var(--borda);
        padding:10px 18px;
        font-family:var(--mono);
        font-size:0.72rem;
        letter-spacing:0.14em;
        text-transform:uppercase;
        color:var(--ambar);
    }

    .form-card .corpo-form{
        padding:18px;
    }

    .form-grid{
        display:grid;
        grid-template-columns:2fr 1fr 1fr 1fr auto;
        gap:10px;
        align-items:end;
    }

    .campo label{
        display:block;
        font-family:var(--mono);
        font-size:0.68rem;
        text-transform:uppercase;
        letter-spacing:0.06em;
        color:var(--texto-suave);
        margin-bottom:5px;
    }

    input, select{
        width:100%;
        padding:9px 10px;
        border:1px solid var(--borda);
        border-radius:5px;
        font-size:0.88rem;
        font-family:var(--corpo);
        background:#10151a;
        color:var(--texto);
    }

    input:focus, select:focus{
        outline:none;
        border-color:var(--ambar);
        box-shadow:0 0 0 2px var(--ambar-fundo);
    }

    button, .btn{
        padding:9px 18px;
        border:1px solid transparent;
        border-radius:5px;
        background:var(--ambar);
        color:#20160a;
        font-weight:700;
        font-family:var(--corpo);
        cursor:pointer;
        font-size:0.85rem;
        text-decoration:none;
        display:inline-block;
        text-align:center;
        transition:filter 0.15s ease;
    }

    button:hover, .btn:hover{ filter:brightness(1.1); }

    /* ---------- Lista de rotinas: quadro de estações ---------- */
    .lista .titulo-lista{
        font-family:var(--display);
        text-transform:uppercase;
        letter-spacing:0.05em;
        font-size:1.05rem;
        font-weight:600;
        margin-bottom:12px;
        color:var(--texto);
    }

    .rotina{
        background:var(--painel);
        border:1px solid var(--borda);
        border-left:4px solid var(--borda-forte);
        border-radius:6px;
        padding:13px 16px;
        margin-bottom:9px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        gap:12px;
        flex-wrap:wrap;
    }

    .rotina.status-feito{ border-left-color:var(--verde); opacity:0.72; }
    .rotina.status-pendente{ border-left-color:var(--ambar); }
    .rotina.status-atrasado{ border-left-color:var(--vermelho); }

    .rotina .info{ flex:1; min-width:200px; display:flex; align-items:flex-start; gap:10px; }

    /* luz estilo andon */
    .luz{
        width:11px; height:11px;
        border-radius:50%;
        margin-top:5px;
        flex-shrink:0;
        background:var(--texto-suave);
    }
    .luz.feito{ background:var(--verde); box-shadow:0 0 7px 2px rgba(46,204,113,0.65); }
    .luz.pendente{ background:var(--ambar); box-shadow:0 0 7px 2px rgba(245,166,35,0.55); }
    .luz.atrasado{
        background:var(--vermelho);
        box-shadow:0 0 7px 2px rgba(235,77,75,0.65);
        animation:pulsar 1.3s ease-in-out infinite;
    }
    @keyframes pulsar{ 0%,100%{opacity:1;} 50%{opacity:0.35;} }

    .rotina .nome{
        font-weight:600;
        font-size:0.98rem;
        margin-bottom:5px;
    }

    .rotina.status-feito .nome{ text-decoration:line-through; color:var(--texto-suave); }

    .meta{
        display:flex;
        gap:7px;
        flex-wrap:wrap;
        font-size:0.72rem;
    }

    .tag{
        padding:3px 9px;
        border-radius:4px;
        font-weight:600;
        font-family:var(--mono);
        border:1px solid transparent;
    }

    .tag.setor{ background:var(--azul-fundo); color:var(--azul); border-color:rgba(79,163,209,0.3); }

    .tag.prioridade-baixa{ background:var(--verde-fundo); color:var(--verde); border-color:rgba(46,204,113,0.3); }
    .tag.prioridade-média{ background:var(--ambar-fundo); color:var(--ambar); border-color:rgba(245,166,35,0.3); }
    .tag.prioridade-alta{ background:var(--vermelho-fundo); color:var(--vermelho); border-color:rgba(235,77,75,0.3); }

    .tag.status-feito{ background:var(--verde-fundo); color:var(--verde); border-color:rgba(46,204,113,0.3); }
    .tag.status-pendente{ background:var(--ambar-fundo); color:var(--ambar); border-color:rgba(245,166,35,0.3); }
    .tag.status-atrasado{ background:var(--vermelho-fundo); color:var(--vermelho); border-color:rgba(235,77,75,0.3); }

    .tag.fixa{ background:var(--roxo-fundo); color:var(--roxo); border-color:rgba(157,126,232,0.3); }

    .acoes{
        display:flex;
        gap:6px;
        flex-wrap:wrap;
    }

    .acoes a{
        padding:6px 11px;
        border-radius:5px;
        font-size:0.76rem;
        text-decoration:none;
        font-weight:600;
        border:1px solid transparent;
    }

    .acoes .concluir{ background:var(--verde-fundo); color:var(--verde); border-color:rgba(46,204,113,0.3); }
    .acoes .editar{ background:var(--azul-fundo); color:var(--azul); border-color:rgba(79,163,209,0.3); }
    .acoes .excluir{ background:var(--vermelho-fundo); color:var(--vermelho); border-color:rgba(235,77,75,0.3); }

    .vazio{
        text-align:center;
        color:var(--texto-suave);
        padding:34px 0;
        font-family:var(--mono);
        font-size:0.85rem;
        border:1px dashed var(--borda);
        border-radius:8px;
    }

    @media (max-width:700px){
        .dashboard{ grid-template-columns:repeat(2, 1fr); }
        .form-grid{ grid-template-columns:1fr; }
        body{ padding:16px; }
    }
</style>
"""

PAGINA_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Entrar · Controle de Rotinas</title>
""" + BASE_STYLE + """
</head>
<body>
<div class="container" style="max-width:420px;">

<header>
    <span class="rebite tl"></span><span class="rebite tr"></span>
    <span class="rebite bl"></span><span class="rebite br"></span>
    <p class="eyebrow">Painel · PCP</p>
    <h1>Entrar</h1>
    <p>Acesse seu painel de rotinas</p>
</header>

{% if erro %}
<div class="vazio" style="border-color:var(--vermelho); color:var(--vermelho); margin-bottom:16px;">{{ erro }}</div>
{% endif %}

<section class="form-card">
    <div class="titulo-painel">Login</div>
    <div class="corpo-form">
    <form method="POST">
        <div class="campo" style="margin-bottom:12px;">
            <label>Usuário</label>
            <input name="usuario" required autofocus>
        </div>
        <div class="campo" style="margin-bottom:16px;">
            <label>Senha</label>
            <input type="password" name="senha" required>
        </div>
        <button type="submit" style="width:100%;">Entrar</button>
    </form>
    </div>
</section>

<p style="text-align:center; color:var(--texto-suave); font-size:0.85rem;">
    Ainda não tem conta? <a href="/registrar" style="color:var(--ambar);">Criar conta</a>
</p>

</div>
</body>
</html>
"""

PAGINA_REGISTRAR = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Criar conta · Controle de Rotinas</title>
""" + BASE_STYLE + """
</head>
<body>
<div class="container" style="max-width:420px;">

<header>
    <span class="rebite tl"></span><span class="rebite tr"></span>
    <span class="rebite bl"></span><span class="rebite br"></span>
    <p class="eyebrow">Painel · PCP</p>
    <h1>Criar conta</h1>
    <p>Cada membro da equipe tem seu próprio painel</p>
</header>

{% if erro %}
<div class="vazio" style="border-color:var(--vermelho); color:var(--vermelho); margin-bottom:16px;">{{ erro }}</div>
{% endif %}

<section class="form-card">
    <div class="titulo-painel">Cadastro</div>
    <div class="corpo-form">
    <form method="POST">
        <div class="campo" style="margin-bottom:12px;">
            <label>Nome</label>
            <input name="nome" required autofocus>
        </div>
        <div class="campo" style="margin-bottom:12px;">
            <label>Usuário</label>
            <input name="usuario" required>
        </div>
        <div class="campo" style="margin-bottom:16px;">
            <label>Senha</label>
            <input type="password" name="senha" minlength="6" required>
        </div>
        <div class="campo" style="margin-bottom:16px;">
            <label>Código de convite</label>
            <input name="codigo_convite" required>
        </div>
        <button type="submit" style="width:100%;">Criar conta</button>
    </form>
    </div>
</section>

<p style="text-align:center; color:var(--texto-suave); font-size:0.85rem;">
    Já tem conta? <a href="/login" style="color:var(--ambar);">Entrar</a>
</p>

</div>
</body>
</html>
"""

PAGINA_TROCAR_SENHA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trocar senha · Controle de Rotinas</title>
""" + BASE_STYLE + """
</head>
<body>
<div class="container" style="max-width:420px;">

<header>
    <span class="rebite tl"></span><span class="rebite tr"></span>
    <span class="rebite bl"></span><span class="rebite br"></span>
    <p class="eyebrow">Painel · PCP</p>
    <h1>Trocar senha</h1>
    <p><a class="btn" style="background:transparent;color:var(--texto-suave);border:1px solid var(--borda);" href="/">← Voltar</a></p>
</header>

{% if erro %}
<div class="vazio" style="border-color:var(--vermelho); color:var(--vermelho); margin-bottom:16px;">{{ erro }}</div>
{% endif %}
{% if sucesso %}
<div class="vazio" style="border-color:var(--verde); color:var(--verde); margin-bottom:16px;">{{ sucesso }}</div>
{% endif %}

<section class="form-card">
    <div class="titulo-painel">Alterar senha</div>
    <div class="corpo-form">
    <form method="POST">
        <div class="campo" style="margin-bottom:12px;">
            <label>Senha atual</label>
            <input type="password" name="senha_atual" required autofocus>
        </div>
        <div class="campo" style="margin-bottom:12px;">
            <label>Nova senha</label>
            <input type="password" name="senha_nova" minlength="6" required>
        </div>
        <div class="campo" style="margin-bottom:16px;">
            <label>Confirmar nova senha</label>
            <input type="password" name="senha_confirma" minlength="6" required>
        </div>
        <button type="submit" style="width:100%;">Salvar nova senha</button>
    </form>
    </div>
</section>

</div>
</body>
</html>
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
    <span class="rebite tl"></span><span class="rebite tr"></span>
    <span class="rebite bl"></span><span class="rebite br"></span>
    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
        <div>
            <p class="eyebrow">Painel · PCP</p>
            <h1>Controle de Rotinas</h1>
            <p>Acompanhamento das rotinas por estação</p>
        </div>
        <div style="text-align:right; font-size:0.8rem; color:var(--texto-suave);">
            <div style="margin-bottom:6px;">👤 {{ current_user.nome }}</div>
            <a href="/trocar-senha" style="color:var(--texto-suave); font-size:0.78rem; margin-right:8px;">Trocar senha</a>
            <a class="btn" style="background:transparent;color:var(--texto-suave);border:1px solid var(--borda); padding:6px 12px; font-size:0.78rem;" href="/logout">Sair</a>
        </div>
    </div>
</header>

<section class="dashboard">
    <div class="card total">
        <div class="rotulo">Total de rotinas</div>
        <div class="valor">{{ total }}</div>
    </div>
    <div class="card concluidas">
        <div class="rotulo">Concluídas</div>
        <div class="valor">{{ concluidas }}</div>
    </div>
    <div class="card pendentes">
        <div class="rotulo">Pendentes</div>
        <div class="valor">{{ pendentes }}</div>
    </div>
    <div class="card percentual">
        <div class="rotulo">% Concluído</div>
        <div class="valor">{{ percentual }}%</div>
        <div class="barra-progresso">
            <div class="preenchido" style="width:{{ percentual }}%;"></div>
        </div>
    </div>
</section>

<section class="form-card">
    <div class="titulo-painel">+ Nova rotina</div>
    <div class="corpo-form">
    <form method="POST" action="/criar">
        <div class="form-grid">
<div class="campo">
    <label>Rotina</label>
    <input name="nome" placeholder="Ex: Enviar relatório de produção" required>
</div>

<div class="campo">
    <label>Rotina fixa?</label>
    <select name="fixa">
        <option value="Não">Não</option>
        <option value="Sim">Sim - todos os dias</option>
    </select>
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
        <option value="{{ p }}">{{ p }}</option>
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
    </div>
</section>

<section class="lista">
    <div class="titulo-lista">Rotinas</div>

    <form method="GET" action="/" class="form-grid" style="margin-bottom:16px; align-items:end;">
        <div class="campo">
            <label>Setor</label>
            <select name="setor" onchange="this.form.submit()">
                <option value="">Todos</option>
                {% for s in setores %}
                <option value="{{ s }}" {% if s==filtro_setor %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="campo">
            <label>Prioridade</label>
            <select name="prioridade" onchange="this.form.submit()">
                <option value="">Todas</option>
                {% for p in prioridades %}
                <option value="{{ p }}" {% if p==filtro_prioridade %}selected{% endif %}>{{ p }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="campo">
            <label>Status</label>
            <select name="status" onchange="this.form.submit()">
                <option value="">Todos</option>
                <option value="pendente" {% if filtro_status=='pendente' %}selected{% endif %}>Pendente</option>
                <option value="feito" {% if filtro_status=='feito' %}selected{% endif %}>Feito</option>
                <option value="atrasada" {% if filtro_status=='atrasada' %}selected{% endif %}>Atrasada</option>
            </select>
        </div>
        <div class="campo">
            <a class="btn" style="background:transparent;color:var(--texto-suave);border:1px solid var(--borda); display:block;" href="/">Limpar filtros</a>
        </div>
    </form>

    {% if not rotinas %}
        <div class="vazio">Nenhuma rotina encontrada.</div>
    {% endif %}

    {% for r in rotinas %}
    {% if r['status']=='Feito' %}
        {% set classe_status = 'status-feito' %}
        {% set classe_luz = 'feito' %}
    {% elif r['atrasada'] %}
        {% set classe_status = 'status-atrasado' %}
        {% set classe_luz = 'atrasado' %}
    {% else %}
        {% set classe_status = 'status-pendente' %}
        {% set classe_luz = 'pendente' %}
    {% endif %}
    <div class="rotina {{ classe_status }}">
        <div class="info">
            <span class="luz {{ classe_luz }}"></span>
            <div>
            <div class="nome">{{ r['nome'] }}</div>
            <div class="meta">
    <span class="tag setor">{{ r['setor'] }}</span>
    <span class="tag prioridade-{{ r['prioridade']|lower }}">{{ r['prioridade'] }}</span>

    {% if r['fixa']=='Sim' %}
        <span class="tag fixa">🔁 Fixa</span>
    {% endif %}

    {% if r['status']=='Feito' %}
        <span class="tag status-feito">Feito</span>
    {% elif r['atrasada'] %}
        <span class="tag status-atrasado">Atrasada</span>
    {% else %}
        <span class="tag status-pendente">Pendente</span>
    {% endif %}

    {% if r['prazo'] %}
       <span class="tag setor">
    📅 {{ r['prazo'][8:10] }}/{{ r['prazo'][5:7] }}/{{ r['prazo'][0:4] }}
</span>
    {% endif %}
</div>
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
<!-- RODAPÉ - CONTROLE DE ROTINAS -->
<footer style="
    margin-top: 40px;
    padding: 15px;
    text-align: right;
    color: #777;
    font-size: 13px;
">
    <hr>
    Controle de Rotinas v1.0<br>
    Desenvolvido por Valdeir Vaz<br>
    2026
    <hr>
</footer>
<!-- FIM RODAPÉ -->

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
    <span class="rebite tl"></span><span class="rebite tr"></span>
    <span class="rebite bl"></span><span class="rebite br"></span>
    <p class="eyebrow">Painel · PCP</p>
    <h1>Editar rotina</h1>
    <p><a class="btn" style="background:transparent;color:var(--texto-suave);border:1px solid var(--borda);" href="/">← Voltar</a></p>
</header>

<section class="form-card">
    <div class="titulo-painel">Editar</div>
    <div class="corpo-form">
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

        <div class="campo" style="margin-bottom:12px;">
            <label>Rotina fixa?</label>
            <select name="fixa">
                <option value="Não" {% if r['fixa']!='Sim' %}selected{% endif %}>Não</option>
                <option value="Sim" {% if r['fixa']=='Sim' %}selected{% endif %}>Sim - todos os dias</option>
            </select>
        </div>

        <div class="campo" style="margin-bottom:16px;">
            <label>Prazo</label>
            <input type="date" name="prazo" value="{{ r['prazo'] or '' }}">
        </div>

        <button type="submit">Salvar alterações</button>
    </form>
    </div>
</section>

</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Virada de dia (meia-noite)
# ---------------------------------------------------------------------------
def processar_virada_dia():
    """
    Regra da virada do dia:
    - Rotinas FIXAS: continuam sendo a MESMA linha, só voltam para
      'Pendente' (mesmo que tivessem sido concluídas no dia anterior,
      pois já é outro dia).
    - Rotinas NÃO FIXAS que foram concluídas: somem (são excluídas).
    - Rotinas NÃO FIXAS que NÃO foram concluídas: continuam do jeito
      que estão, sem nenhuma alteração.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # Fixas voltam para pendente todo dia
    cursor.execute("""
        UPDATE rotinas
        SET status='Pendente'
        WHERE fixa='Sim'
    """)

    # Não fixas concluídas somem
    cursor.execute("""
        DELETE FROM rotinas
        WHERE fixa='Não' AND status='Feito'
    """)

    conn.commit()
    conn.close()


def verificar_virada_dia():
    """
    Roda a virada do dia caso ainda não tenha sido feita hoje.
    Isso garante que, mesmo se o agendador não tiver disparado
    exatamente à meia-noite (ex: servidor reiniciando, hibernando),
    a regra é aplicada assim que alguém abrir o app no dia seguinte.
    """
    hoje = date.today().isoformat()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT valor FROM controle_sistema WHERE chave='ultima_virada'")
    row = cursor.fetchone()
    ultima = row["valor"] if row else None

    conn.close()

    if ultima != hoje:
        processar_virada_dia()

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO controle_sistema (chave, valor)
            VALUES ('ultima_virada', %s)
            ON CONFLICT (chave) DO UPDATE SET valor=%s
        """, (hoje, hoje))
        conn.commit()
        conn.close()


def iniciar_agendador():
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        verificar_virada_dia,
        trigger="cron",
        hour=0,
        minute=0,
        id="virada_de_dia",
        replace_existing=True,
    )
    scheduler.start()

iniciar_agendador()

# ---------------------------------------------------------------------------
# Rotas de autenticação
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip().lower()
        senha = request.form.get("senha", "")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row["senha_hash"], senha):
            login_user(Usuario(row))
            return redirect("/")

        erro = "Usuário ou senha inválidos."

    return render_template_string(PAGINA_LOGIN, erro=erro)


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if current_user.is_authenticated:
        return redirect("/")

    erro = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        usuario = request.form.get("usuario", "").strip().lower()
        senha = request.form.get("senha", "")
        codigo = request.form.get("codigo_convite", "").strip()

        codigo_esperado = os.environ.get("CODIGO_CONVITE", "")

        if not nome or not usuario or len(senha) < 6:
            erro = "Preencha nome, usuário e uma senha com pelo menos 6 caracteres."
        elif not codigo_esperado:
            erro = "Cadastro desativado: código de convite não configurado no servidor."
        elif codigo != codigo_esperado:
            erro = "Código de convite inválido."
        else:
            conn = get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuarios WHERE usuario=%s", (usuario,))
            if cursor.fetchone():
                erro = "Já existe uma conta com este usuário."
                conn.close()
            else:
                cursor.execute(
                    """
                    INSERT INTO usuarios (nome, usuario, senha_hash, criado_em)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (nome, usuario, generate_password_hash(senha),
                     datetime.now().strftime("%d/%m/%Y %H:%M"))
                )
                row = cursor.fetchone()
                conn.commit()
                conn.close()

                login_user(Usuario(row))
                return redirect("/")

    return render_template_string(PAGINA_REGISTRAR, erro=erro)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/trocar-senha", methods=["GET", "POST"])
@login_required
def trocar_senha():
    erro = None
    sucesso = None

    if request.method == "POST":
        senha_atual = request.form.get("senha_atual", "")
        senha_nova = request.form.get("senha_nova", "")
        senha_confirma = request.form.get("senha_confirma", "")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id=%s", (current_user.id,))
        row = cursor.fetchone()

        if not row or not check_password_hash(row["senha_hash"], senha_atual):
            erro = "Senha atual incorreta."
        elif len(senha_nova) < 6:
            erro = "A nova senha precisa ter pelo menos 6 caracteres."
        elif senha_nova != senha_confirma:
            erro = "As senhas não coincidem."
        else:
            cursor.execute(
                "UPDATE usuarios SET senha_hash=%s WHERE id=%s",
                (generate_password_hash(senha_nova), current_user.id)
            )
            conn.commit()
            sucesso = "Senha alterada com sucesso."

        conn.close()

    return render_template_string(PAGINA_TROCAR_SENHA, erro=erro, sucesso=sucesso)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def inicio():

    verificar_virada_dia()

    filtro_setor = request.args.get("setor", "")
    filtro_prioridade = request.args.get("prioridade", "")
    filtro_status = request.args.get("status", "")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM rotinas WHERE usuario_id=%s ORDER BY id DESC",
        (current_user.id,)
    )
    dados = cursor.fetchall()

    conn.close()

    hoje = date.today().isoformat()

    rotinas = []

    for r in dados:
        item = dict(r)

        item["atrasada"] = bool(
            item["status"] == "Pendente"
            and item["prazo"]
            and item["prazo"] < hoje
        )

        rotinas.append(item)


    total = len(rotinas)
    concluidas = sum(1 for r in rotinas if r["status"] == "Feito")
    pendentes = total - concluidas

    percentual = round((concluidas / total) * 100) if total else 0

    rotinas_exibidas = rotinas

    if filtro_setor:
        rotinas_exibidas = [r for r in rotinas_exibidas if r["setor"] == filtro_setor]

    if filtro_prioridade:
        rotinas_exibidas = [r for r in rotinas_exibidas if r["prioridade"] == filtro_prioridade]

    if filtro_status == "feito":
        rotinas_exibidas = [r for r in rotinas_exibidas if r["status"] == "Feito"]
    elif filtro_status == "atrasada":
        rotinas_exibidas = [r for r in rotinas_exibidas if r["atrasada"]]
    elif filtro_status == "pendente":
        rotinas_exibidas = [r for r in rotinas_exibidas if r["status"] == "Pendente" and not r["atrasada"]]


    return render_template_string(
        PAGINA_INICIO,
        rotinas=rotinas_exibidas,
        total=total,
        concluidas=concluidas,
        pendentes=pendentes,
        percentual=percentual,
        setores=SETORES,
        prioridades=PRIORIDADES,
        filtro_setor=filtro_setor,
        filtro_prioridade=filtro_prioridade,
        filtro_status=filtro_status,
    )


@app.route("/criar", methods=["POST"])
@login_required
def criar():

    nome = request.form["nome"].strip()
    setor = request.form.get("setor", SETORES[0])
    prioridade = request.form.get("prioridade", "Média")
    prazo = request.form.get("prazo") or None
    fixa = request.form.get("fixa", "Não")

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")


    if nome:

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO rotinas
            (nome, setor, prioridade, status, data_criacao, prazo, fixa, frequencia, ultima_geracao, usuario_id)

            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,

            (
                nome,
                setor,
                prioridade,
                "Pendente",
                agora,
                prazo,
                fixa,
                "Diária" if fixa == "Sim" else "",
                "",
                current_user.id
            )
        )

        conn.commit()
        conn.close()


    return redirect("/")



@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):

    conn = get_conn()
    cursor = conn.cursor()


    if request.method == "POST":

        nome = request.form["nome"].strip()
        setor = request.form.get("setor", SETORES[0])
        prioridade = request.form.get("prioridade", "Média")
        prazo = request.form.get("prazo") or None
        fixa = request.form.get("fixa", "Não")


        cursor.execute(
            """
            UPDATE rotinas
            SET nome=%s, setor=%s, prioridade=%s, prazo=%s, fixa=%s
            WHERE id=%s AND usuario_id=%s
            """,

            (
                nome,
                setor,
                prioridade,
                prazo,
                fixa,
                id,
                current_user.id
            )
        )


        conn.commit()
        conn.close()

        return redirect("/")



    cursor.execute(
        "SELECT * FROM rotinas WHERE id=%s AND usuario_id=%s",
        (id, current_user.id)
    )

    r = cursor.fetchone()

    conn.close()


    if r is None:
        return redirect("/")


    return render_template_string(
        PAGINA_EDITAR,
        r=dict(r),
        setores=SETORES,
        prioridades=PRIORIDADES
    )



@app.route("/excluir/<int:id>")
@login_required
def excluir(id):

    conn = get_conn()
    cursor = conn.cursor()


    cursor.execute(
        "DELETE FROM rotinas WHERE id=%s AND usuario_id=%s",
        (id, current_user.id)
    )


    conn.commit()
    conn.close()


    return redirect("/")



@app.route("/concluir/<int:id>")
@login_required
def concluir(id):

    conn = get_conn()
    cursor = conn.cursor()


    cursor.execute(
        "SELECT status FROM rotinas WHERE id=%s AND usuario_id=%s",
        (id, current_user.id)
    )


    row = cursor.fetchone()


    if row:

        novo = "Feito" if row["status"] == "Pendente" else "Pendente"


        cursor.execute(
            """
            UPDATE rotinas
            SET status=%s
            WHERE id=%s AND usuario_id=%s
            """,
            (novo, id, current_user.id)
        )


        conn.commit()


    conn.close()


    return redirect("/")



if __name__ == "__main__":



    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
