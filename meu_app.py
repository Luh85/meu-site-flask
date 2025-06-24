from flask import Flask, request, redirect, session, render_template_string, send_from_directory
import json, os, random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'segredo'

USUARIOS_FILE = 'usuarios.json'
SAQUES_FILE = 'saques.json'
MENSAGENS_FILE = 'mensagens.json'
UPLOAD_FOLDER = 'static/fotos'
ADMIN_EMAILS = ['tattoozen18@gmail.com', 'paudoce176@gmail.com']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicialização
for arquivo, padrao in [(USUARIOS_FILE, {}), (SAQUES_FILE, []), (MENSAGENS_FILE, [])]:
    if not os.path.exists(arquivo):
        with open(arquivo, 'w') as f: json.dump(padrao, f)
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

# Funções utilitárias
def carregar_usuarios(): return json.load(open(USUARIOS_FILE))
def salvar_usuarios(u): json.dump(u, open(USUARIOS_FILE, 'w'))
def carregar_saques(): return json.load(open(SAQUES_FILE))
def salvar_saques(s): json.dump(s, open(SAQUES_FILE, 'w'))
def carregar_msgs(): return json.load(open(MENSAGENS_FILE))
def salvar_msgs(m): json.dump(m, open(MENSAGENS_FILE, 'w'))
def gerar_id7(): return str(random.randint(10**6, 10**7 - 1))

@app.route('/static/fotos/<path:nome>')
def foto(nome): return send_from_directory('static/fotos', nome)

@app.route('/')
def index():
    return render_template_string('''
    <html><head><meta charset="utf-8"><title>Bem-vindo</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script>
    </head><body>
    <div style="display:flex;">
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    <div style="width:60%;text-align:center">
      <h1>Ganhe recompensas resolvendo captchas!</h1>
      <nav><a href="/">Home</a> | <a href="/login_page">Login</a> | <a href="/cadastro_page">Cadastro</a></nav>
      <p><a href="/privacy">Política</a> | <a href="/terms">Termos</a> | <a href="/contact">Contato</a></p>
    </div>
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    </div>
    </body></html>
    ''')

@app.route('/terms')
@app.route('/privacy')
@app.route('/contact')
def info_pages():
    page = request.path.strip('/')
    titles = {'terms':'Termos de Uso','privacy':'Política de Privacidade','contact':'Contato'}
    return f"<div style='text-align:center'><h2>{titles.get(page,page)}</h2><p>Conteúdo de {titles.get(page,page)} aqui.</p><p><a href='/'>Voltar</a></p></div>"

@app.route('/cadastro_page')
def cadastro_page():
    return render_template_string('''
    <html><body><div style="display:flex;">
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    <div style="width:60%;text-align:center">
      <h2>Cadastro</h2>
      <form method="post" action="/cadastro">
        Nome:<input name="nome"><br>Email:<input name="email"><br>Senha:<input name="senha" type="password"><br>
        <input type="submit" value="Cadastrar">
      </form>
      <p><a href="/">Voltar</a></p>
    </div>
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    </div></body></html>
    ''')

@app.route('/login_page')
def login_page():
    return render_template_string('''
    <html><body><div style="display:flex;">
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    <div style="width:60%;text-align:center">
      <h2>Login</h2>
      <form method="post" action="/login">
        Email:<input name="email"><br>Senha:<input name="senha" type="password"><br>
        <input type="submit" value="Entrar">
      </form>
      <p><a href="/">Voltar</a></p>
    </div>
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    </div></body></html>
    ''')

@app.route('/cadastro', methods=['POST'])
def cadastro():
    email, senha, nome = request.form['email'], request.form['senha'], request.form['nome']
    u = carregar_usuarios()
    if email in u:
        return 'Email já cadastrado. <a href="/">Voltar</a>'
    u[email] = {'senha': senha, 'nome': nome, 'saldo': 0, 'id7': gerar_id7(), 'friends': [], 'blocked': [], 'foto': ''}
    salvar_usuarios(u)
    return redirect('/login_page')

@app.route('/login', methods=['POST'])
def login():
    email, senha = request.form['email'], request.form['senha']
    u = carregar_usuarios()
    if email in u and u[email]['senha'] == senha:
        session['email'] = email
        return redirect('/dashboard')
    return 'Login inválido. <a href="/login_page">Voltar</a>'

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'email' not in session: return redirect('/')
    email = session['email']
    u = carregar_usuarios()
    msgs = carregar_msgs()
    user = u[email]; msg = ''
    if request.method == 'POST':
        if 'resposta' in request.form:
            try:
                if int(request.form['resposta']) == session.get('captcha'):
                    user['saldo'] += 0.33; msg = 'Captcha certo! +R$0.33'
                else: msg = 'Captcha incorreto.'
                salvar_usuarios(u)
            except: msg = 'Inválido'
        if 'search' in request.form:
            alvo = request.form['search']
            for e in u:
                if e == alvo or u[e]['id7'] == alvo:
                    if e not in user['friends'] and e != email:
                        user['friends'].append(e); msg = 'Amigo adicionado.'
                    else: msg = 'Já é amigo.'
                    salvar_usuarios(u)
        if 'msg' in request.form and 'para' in request.form:
            destino = request.form['para']
            if destino in user['friends']:
                msgs.append({'de': email, 'para': destino, 'txt': request.form['msg'], 'visto': False})
                salvar_msgs(msgs)
        if 'nome' in request.form:
            user['nome'] = request.form['nome']; salvar_usuarios(u); msg = 'Nome alterado.'
        if 'foto' in request.files:
            f = request.files['foto']
            if f.filename:
                fn = secure_filename(email + os.path.splitext(f.filename)[1])
                f.save(os.path.join(UPLOAD_FOLDER, fn))
                user['foto'] = fn; salvar_usuarios(u)

    amigos = [(e, u[e]['nome'], u[e]['id7'], u[e]['foto']) for e in user['friends'] if e in u]
    a,b = random.randint(1,10), random.randint(1,10); session['captcha'] = a+b
    chat_msgs = [m for m in msgs if (m['para'] == email and not m.get('visto')) or m['de'] == email][-10:]

    # Marcar mensagens recebidas como lidas
    for m in msgs:
        if m['para'] == email: m['visto'] = True
    salvar_msgs(msgs)

    return render_template_string('''
    <html><body><div style="display:flex;">
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    <div style="width:60%;text-align:center">
      <h3>{{user['nome']}}</h3><p>ID: {{user['id7']}} | Saldo: R${{ '%.2f'|format(user['saldo']) }}</p>
      <form method="post"><input name="resposta" placeholder="{{a}}+{{b}}?"><input type="submit" value="Captcha"></form>
      <p>{{msg}}</p>
      <form method="post"><input name="search" placeholder="Buscar email ou ID"><input type="submit" value="Adicionar"></form>
      <form method="post" enctype="multipart/form-data">
        Nome:<input name="nome" value="{{user['nome']}}"> Foto:<input type="file" name="foto">
        <input type="submit" value="Atualizar">
      </form>
      <h4>Contatos:</h4>
      <ul>{% for e,n,i,f in amigos %}<li><img src="/static/fotos/{{f}}" width="30"> {{n}} - {{e}} (ID:{{i}})</li>{% endfor %}</ul>
      <form method="post" action="/sacar">PIX:<input name="pix" required><input type="submit" value="Sacar"></form>
      <h4>Chat:</h4>
      <form method="post">
        Para:<input name="para"><br>Mensagem:<br><textarea name="msg"></textarea><br>
        <input type="submit" value="Enviar">
      </form>
      <div>{% for m in chat_msgs %}<p><b>{{m['de']}}</b>: {{m['txt']}} {% if not m.get('visto') and m['para']==email %}<span style="color:red;">(nova)</span>{% endif %}</p>{% endfor %}</div>
      {% if email in admin_emails %}<p><a href="/admin">Admin</a></p>{% endif %}
    </div>
    <div style="width:20%">{% for _ in range(3) %}<div class="ads">[AD]</div>{% endfor %}</div>
    </div></body></html>
    ''', user=user, email=email, a=a, b=b, msg=msg, amigos=amigos, chat_msgs=chat_msgs, admin_emails=ADMIN_EMAILS)

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session: return redirect('/')
    u = carregar_usuarios(); s = carregar_saques()
    user = u[session['email']]
    if user['saldo'] >= 0.33:
        s.append({'email': session['email'], 'pix': request.form['pix'], 'valor': user['saldo']})
        user['saldo'] = 0; salvar_usuarios(u); salvar_saques(s)
        return 'Saque enviado! <a href="/dashboard">Voltar</a>'
    return 'Saldo insuficiente. <a href="/dashboard">Voltar</a>'

@app.route('/admin')
def admin():
    if session.get('email') not in ADMIN_EMAILS: return redirect('/')
    u = carregar_usuarios(); s = carregar_saques()
    return render_template_string('''<h2>Admin</h2>
    <ul>{% for e,d in u.items() %}<li>{{e}} - ID:{{d['id7']}} - R${{'%.2f'|format(d['saldo'])}}</li>{% endfor %}</ul>
    <h3>Saques:</h3><ul>{% for x in s %}<li>{{x['email']}} PIX:{{x['pix']}} R${{'%.2f'|format(x['valor'])}}</li>{% endfor %}</ul>
    <a href="/dashboard">Voltar</a>
    ''', u=u, s=s)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
