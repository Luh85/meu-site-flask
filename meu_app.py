from flask import Flask, request, redirect, session, render_template_string
import json, os, random

app = Flask(__name__)
app.secret_key = 'segredo'

USUARIOS_FILE = 'usuarios.json'
SAQUES_FILE = 'saques.json'
ADMIN_EMAILS = ['tattoozen18@gmail.com', 'paudoce176@gmail.com']

# Inicializa os arquivos se não existirem
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(SAQUES_FILE):
    with open(SAQUES_FILE, 'w') as f:
        json.dump([], f)

# Funções auxiliares
def carregar_usuarios():
    with open(USUARIOS_FILE, 'r') as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, 'w') as f:
        json.dump(usuarios, f)

def carregar_saques():
    with open(SAQUES_FILE, 'r') as f:
        return json.load(f)

def salvar_saques(saques):
    with open(SAQUES_FILE, 'w') as f:
        json.dump(saques, f)

# Rotas
@app.route('/')
def index():
    return render_template_string('''
        <h2>Login</h2>
        <form method="post" action="/login">
            Email: <input type="email" name="email" required><br>
            Senha: <input type="password" name="senha" required><br>
            <input type="submit" value="Entrar">
        </form>
        <br>
        <h2>Cadastrar</h2>
        <form method="post" action="/cadastro">
            Email: <input type="email" name="email" required><br>
            Senha: <input type="password" name="senha" required><br>
            <input type="submit" value="Cadastrar">
        </form>
    ''')

@app.route('/cadastro', methods=['POST'])
def cadastro():
    email = request.form['email']
    senha = request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios:
        return 'Email já cadastrado. <a href="/">Voltar</a>'
    usuarios[email] = {'senha': senha, 'saldo': 0.0}
    salvar_usuarios(usuarios)
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios and usuarios[email]['senha'] == senha:
        session['email'] = email
        return redirect('/dashboard')
    return 'Login inválido. <a href="/">Tente novamente</a>'

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    usuarios = carregar_usuarios()
    saldo = usuarios[email].get('saldo', 0.0)
    msg = ''

    if request.method == 'POST':
        try:
            resposta = int(request.form['resposta'])
            if resposta == session.get('captcha_resposta'):
                ganho = round(0.33, 2)
                usuarios[email]['saldo'] += ganho
                salvar_usuarios(usuarios)
                msg = f'Captcha correto! R$ {ganho:.2f} adicionados.'
            else:
                msg = 'Resposta incorreta. Tente novamente.'
        except:
            msg = 'Resposta inválida.'

    a, b = random.randint(1, 10), random.randint(1, 10)
    session['captcha_resposta'] = a + b

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body {
                font-family: Arial;
                display: flex;
                flex-direction: column;
                align-items: center;
                background: #f0f0f0;
            }
            .container {
                display: flex;
                margin-top: 20px;
            }
            .side {
                width: 150px;
                margin: 10px;
            }
            .center {
                background: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                box-shadow: 0px 0px 10px #ccc;
            }
            .ads {
                background: #e0e0e0;
                margin: 10px 0;
                padding: 10px;
                border-radius: 6px;
            }
            .bottom-ad {
                margin-top: 30px;
                background: #ddd;
                padding: 15px;
                width: 500px;
                text-align: center;
                border-radius: 8px;
            }
            form {
                margin-top: 15px;
            }
            input[type="text"], input[type="submit"] {
                padding: 8px;
                margin: 5px;
            }
            .admin-link {
                margin-top: 15px;
            }
        </style>
    </head>
    <body>

        <div class="container">
            <div class="side">
                <div class="ads">[ANÚNCIO 1]</div>
                <div class="ads">[ANÚNCIO 2]</div>
                <div class="ads">[ANÚNCIO 3]</div>
            </div>

            <div class="center">
                <h3>Bem-vindo {{ email }}</h3>
                <p>Saldo: R$ {{ saldo }}</p>
                <form method="post">
                    Quanto é {{ a }} + {{ b }}?
                    <input type="text" name="resposta">
                    <input type="submit" value="Enviar">
                </form>
                <p>{{ msg }}</p>

                <form action="/sacar" method="post">
                    Chave PIX: <input type="text" name="pix" required>
                    <input type="submit" value="Sacar">
                </form>

                {% if email in admin_emails %}
                <div class="admin-link">
                    <a href="/admin">Painel Admin</a>
                </div>
                {% endif %}
            </div>

            <div class="side">
                <div class="ads">[ANÚNCIO 4]</div>
                <div class="ads">[ANÚNCIO 5]</div>
                <div class="ads">[ANÚNCIO 6]</div>
            </div>
        </div>

        <div class="bottom-ad">[ANÚNCIO 7]</div>

    </body>
    </html>
    ''', email=email, saldo=f'{saldo:.2f}', a=a, b=b, msg=msg, admin_emails=ADMIN_EMAILS)

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    pix = request.form['pix']
    usuarios = carregar_usuarios()
    saldo = usuarios[email]['saldo']
    if saldo >= 0.33:
        usuarios[email]['saldo'] = 0.0
        salvar_usuarios(usuarios)
        saques = carregar_saques()
        saques.append({'email': email, 'pix': pix, 'valor': saldo})
        salvar_saques(saques)
        return 'Saque solicitado! <a href="/dashboard">Voltar</a>'
    return 'Saldo insuficiente. <a href="/dashboard">Voltar</a>'

@app.route('/admin')
def admin():
    if 'email' not in session or session['email'] not in ADMIN_EMAILS:
        return redirect('/')
    usuarios = carregar_usuarios()
    saques = carregar_saques()
    return render_template_string('''
        <h2>Admin</h2>
        <h3>Usuários:</h3>
        <ul>
        {% for email, dados in usuarios.items() %}
            <li>{{ email }} - Saldo: R$ {{ dados['saldo'] }}</li>
        {% endfor %}
        </ul>
        <h3>Solicitações de Saque:</h3>
        <ul>
        {% for saque in saques %}
            <li>{{ saque['email'] }} - PIX: {{ saque['pix'] }} - Valor: R$ {{ saque['valor'] }}</li>
        {% endfor %}
        </ul>
        <a href="/dashboard">Voltar</a>
    ''', usuarios=usuarios, saques=saques)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # padrão local
    app.run(host='0.0.0.0', port=port)
