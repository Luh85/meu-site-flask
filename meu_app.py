from flask import Flask, request, redirect, session, render_template_string, jsonify
import json, os, random, uuid, datetime

app = Flask(__name__)
app.secret_key = 'segredo'

USUARIOS_FILE = 'usuarios.json'
SAQUES_FILE = 'saques.json'
MENSAGENS_FILE = 'mensagens.json'
GRUPOS_FILE = 'grupos.json'
ADMIN_EMAILS = ['tattoozen18@gmail.com', 'paudoce176@gmail.com']

# Inicializa os arquivos
for f, v in [
    (USUARIOS_FILE, {}), (SAQUES_FILE, []), 
    (MENSAGENS_FILE, {}), (GRUPOS_FILE, {})
]:
    if not os.path.exists(f):
        with open(f, 'w') as arq:
            json.dump(v, arq)

def ler_json(c):
    with open(c, 'r') as f: return json.load(f)
def salvar_json(c, d):
    with open(c, 'w') as f: json.dump(d, f, indent=2)

def gerar_id7():
    return str(random.randint(10**6, 10**7-1))

@app.route('/')
def index():
    return '''<h1>Bem-vindo</h1><p><a href='/login_page'>Login</a> | <a href='/cadastro_page'>Cadastro</a></p>'''

@app.route('/cadastro_page')
def cadastro_page():
    return '''<form method="post" action="/cadastro">Email: <input name="email"><br>Senha: <input name="senha" type="password"><br><input type="submit" value="Cadastrar"></form>'''

@app.route('/login_page')
def login_page():
    return '''<form method="post" action="/login">Email: <input name="email"><br>Senha: <input name="senha" type="password"><br><input type="submit" value="Entrar"></form>'''

@app.route('/cadastro', methods=['POST'])
def cadastro():
    email = request.form['email']
    senha = request.form['senha']
    usuarios = ler_json(USUARIOS_FILE)
    if email in usuarios:
        return 'Email já cadastrado. <a href="/">Voltar</a>'
    usuarios[email] = {
        'senha': senha, 'saldo': 0.0,
        'id7': gerar_id7(), 'friends': [], 'bloqueados': []
    }
    salvar_json(USUARIOS_FILE, usuarios)
    return redirect('/login_page')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']
    usuarios = ler_json(USUARIOS_FILE)
    if email in usuarios and usuarios[email]['senha'] == senha:
        session['email'] = email
        return redirect('/dashboard')
    return 'Login inválido. <a href="/login_page">Tente novamente</a>'

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    usuarios = ler_json(USUARIOS_FILE)
    u = usuarios[email]
    msg = ''

    if request.method == 'POST':
        if 'resposta' in request.form:
            try:
                if int(request.form['resposta']) == session.get('captcha'):
                    u['saldo'] += 0.33
                    salvar_json(USUARIOS_FILE, usuarios)
                    msg = 'Captcha certo! +R$ 0.33'
                else:
                    msg = 'Captcha incorreto.'
            except:
                msg = 'Erro na resposta.'
        elif 'buscar' in request.form:
            alvo = request.form['buscar']
            if alvo in usuarios and alvo != email:
                if alvo not in u['friends']:
                    u['friends'].append(alvo)
                    salvar_json(USUARIOS_FILE, usuarios)
                    msg = 'Adicionado com sucesso!'
                else:
                    msg = 'Já está na lista.'
        elif 'bloquear' in request.form:
            alvo = request.form['bloquear']
            if alvo in usuarios and alvo not in u['bloqueados']:
                u['bloqueados'].append(alvo)
                salvar_json(USUARIOS_FILE, usuarios)
                msg = 'Usuário bloqueado.'

    a, b = random.randint(1, 10), random.randint(1, 10)
    session['captcha'] = a + b
    amigos = u['friends']
    return render_template_string('''
    <h2>Olá {{email}}</h2>
    <p>ID: {{id7}} | Saldo: R${{saldo}}</p>
    <form method="post">Captcha: Quanto é {{a}}+{{b}}? <input name="resposta"><input type="submit"></form>
    <p>{{msg}}</p>
    <form method="post">Adicionar amigo: <input name="buscar"><input type="submit"></form>
    <form method="post">Bloquear: <input name="bloquear"><input type="submit"></form>
    <h3>Amigos:</h3><ul>{% for a in amigos %}<li>{{a}} | <a href='/chat/{{a}}'>Chat</a></li>{% endfor %}</ul>
    <p><a href='/chat_global'>Chat Global</a></p>
    <p><a href='/logout'>Sair</a></p>
    {% if email in admin_emails %}<p><a href='/admin'>Admin</a></p>{% endif %}
    ''', email=email, id7=u['id7'], saldo='%.2f' % u['saldo'], a=a, b=b, msg=msg, amigos=amigos, admin_emails=ADMIN_EMAILS)

@app.route('/chat/<alvo>', methods=['GET', 'POST'])
def chat_privado(alvo):
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    if email == alvo:
        return redirect('/dashboard')
    usuarios = ler_json(USUARIOS_FILE)
    if alvo not in usuarios:
        return 'Usuário não encontrado'
    if email in usuarios[alvo].get('bloqueados', []):
        return 'Você foi bloqueado por esse usuário.'

    conv_id = '-'.join(sorted([email, alvo]))
    mensagens = ler_json(MENSAGENS_FILE)
    if conv_id not in mensagens:
        mensagens[conv_id] = []

    if request.method == 'POST':
        texto = request.form['mensagem']
        mensagens[conv_id].append({'de': email, 'msg': texto, 'hora': str(datetime.datetime.now())})
        salvar_json(MENSAGENS_FILE, mensagens)

    historico = mensagens[conv_id][-20:]
    chat_html = '<h2>Chat com %s</h2>' % alvo
    chat_html += '<form method="post"><input name="mensagem" placeholder="Mensagem"><input type="submit"></form>'
    for m in historico:
        chat_html += f"<p><b>{m['de']}:</b> {m['msg']} <small>{m['hora']}</small></p>"
    chat_html += '<p><a href="/dashboard">Voltar</a></p>'
    return chat_html

@app.route('/chat_global', methods=['GET','POST'])
def chat_global():
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    mensagens = ler_json(MENSAGENS_FILE)
    if 'global' not in mensagens:
        mensagens['global'] = []

    if request.method == 'POST':
        texto = request.form['mensagem']
        mensagens['global'].append({'de': email, 'msg': texto, 'hora': str(datetime.datetime.now())})
        salvar_json(MENSAGENS_FILE, mensagens)

    historico = mensagens['global'][-30:]
    chat_html = '<h2>Chat Global</h2>'
    chat_html += '<form method="post"><input name="mensagem" placeholder="Mensagem"><input type="submit"></form>'
    for m in historico:
        chat_html += f"<p><b>{m['de']}:</b> {m['msg']} <small>{m['hora']}</small></p>"
    chat_html += '<p><a href="/dashboard">Voltar</a></p>'
    return chat_html

@app.route('/admin')
def admin():
    if session.get('email') not in ADMIN_EMAILS:
        return redirect('/')
    usuarios = ler_json(USUARIOS_FILE)
    saques = ler_json(SAQUES_FILE)
    return render_template_string('''<h2>Admin</h2><ul>{% for u, d in usuarios.items() %}<li>{{u}} - Saldo: {{d['saldo']}}</li>{% endfor %}</ul><h3>Saques:</h3><ul>{% for s in saques %}<li>{{s['email']}}: R$ {{s['valor']}} (PIX: {{s['pix']}})</li>{% endfor %}</ul><a href='/dashboard'>Voltar</a>''', usuarios=usuarios, saques=saques)

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session:
        return redirect('/')
    usuarios = ler_json(USUARIOS_FILE)
    email = session['email']
    u = usuarios[email]
    if u['saldo'] >= 0.33:
        saques = ler_json(SAQUES_FILE)
        saques.append({'email': email, 'pix': request.form['pix'], 'valor': u['saldo']})
        u['saldo'] = 0.0
        salvar_json(SAQUES_FILE, saques)
        salvar_json(USUARIOS_FILE, usuarios)
        return 'Saque solicitado. <a href="/dashboard">Voltar</a>'
    return 'Saldo insuficiente. <a href="/dashboard">Voltar</a>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
