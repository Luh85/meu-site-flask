from flask import Flask, request, redirect, session, render_template_string, send_from_directory
import json, os, random, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'segredo'

USUARIOS_FILE = 'usuarios.json'
SAQUES_FILE = 'saques.json'
ADMIN_EMAILS = ['tattoozen18@gmail.com', 'paudoce176@gmail.com']
UPLOAD_FOLDER = 'static/fotos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(USUARIOS_FILE):
    json.dump({}, open(USUARIOS_FILE, 'w'))
if not os.path.exists(SAQUES_FILE):
    json.dump([], open(SAQUES_FILE, 'w'))

def carregar_usuarios(): return json.load(open(USUARIOS_FILE))
def salvar_usuarios(u): json.dump(u, open(USUARIOS_FILE, 'w'))
def carregar_saques(): return json.load(open(SAQUES_FILE))
def salvar_saques(s): json.dump(s, open(SAQUES_FILE, 'w'))
def gerar_id7(): return str(random.randint(10**6, 10**7-1))

@app.route('/static/fotos/<path:nome>')
def foto(nome): return send_from_directory('static/fotos', nome)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html><html><head>
      <meta charset="utf-8">
      <title>Bem-vindo | Site Captcha</title>
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script>
    </head><body>
    <div style="text-align:center">
      <nav><a href="/">Home</a> | <a href="/login_page">Login</a> | <a href="/cadastro_page">Cadastro</a></nav>
      <h1>Ganhe recompensas resolvendo captchas</h1>
      <p>Resolva desafios, ganhe saldo e saque via PIX. Em breve: chat, amigos, rastreamento...</p>
      <p><a href="/privacy">Política de Privacidade</a> | <a href="/terms">Termos de Uso</a> | <a href="/contact">Contato</a></p>
      <div class="ads">[ANÚNCIO]</div>
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
      <html><head><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script><title>Cadastro</title></head>
      <body style="text-align:center">
      <h2>Cadastro</h2>
      <form method="post" action="/cadastro">
        Nome:<input name="nome" required><br>
        Email:<input name="email" required><br>
        Senha:<input name="senha" type="password" required><br>
        <input type="submit" value="Cadastrar">
      </form>
      <p><a href="/">Voltar</a></p></body></html>
    ''')

@app.route('/login_page')
def login_page():
    return render_template_string('''
      <html><head><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script><title>Login</title></head>
      <body style="text-align:center">
      <h2>Login</h2>
      <form method="post" action="/login">
        Email:<input name="email" required><br>Senha:<input name="senha" type="password" required><br>
        <input type="submit" value="Entrar">
      </form>
      <p><a href="/">Voltar</a></p></body></html>
    ''')

@app.route('/cadastro', methods=['POST'])
def cadastro():
    email = request.form['email']
    nome = request.form['nome']
    senha = request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios:
        return 'Email já cadastrado. <a href="/">Voltar</a>'
    usuarios[email] = {
        'senha': senha, 'nome': nome, 'saldo': 0.0, 'id7': gerar_id7(),
        'friends': [], 'blocked': [], 'foto': ''
    }
    salvar_usuarios(usuarios)
    return redirect('/login_page')

@app.route('/login', methods=['POST'])
def login():
    email, senha = request.form['email'], request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios and usuarios[email]['senha'] == senha:
        session['email'] = email
        return redirect('/dashboard')
    return 'Login inválido. <a href="/login_page">Tente novamente</a>'

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'email' not in session: return redirect('/')
    email = session['email']
    usuarios = carregar_usuarios()
    u = usuarios[email]; msg = ''
    if request.method == 'POST':
        if 'resposta' in request.form:
            try:
                if int(request.form['resposta']) == session.get('captcha'):
                    u['saldo'] += 0.33; msg = 'Captcha certo! +R$ 0.33'
                else: msg = 'Captcha incorreto.'
                salvar_usuarios(usuarios)
            except: msg = 'Resposta inválida.'
        if 'search' in request.form:
            alvo = request.form['search']
            if alvo in usuarios or alvo in [usuarios[k]['id7'] for k in usuarios]:
                for e in usuarios:
                    if e == alvo or usuarios[e]['id7'] == alvo:
                        if e not in u['friends'] and e != email:
                            u['friends'].append(e); msg = 'Adicionado.'
                        else: msg = 'Já é amigo.'
                        salvar_usuarios(usuarios)
        if 'nome' in request.form:
            u['nome'] = request.form['nome']; salvar_usuarios(usuarios); msg = 'Nome alterado.'
        if 'foto' in request.files:
            f = request.files['foto']
            if f.filename:
                fn = secure_filename(email + os.path.splitext(f.filename)[1])
                path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
                f.save(path); u['foto'] = fn; salvar_usuarios(usuarios)
    a,b = random.randint(1,10), random.randint(1,10)
    session['captcha'] = a + b
    amigos = [(f, usuarios[f]['id7'], usuarios[f]['nome'], usuarios[f]['foto']) for f in u['friends'] if f in usuarios and f not in u['blocked']]
    return render_template_string('''
    <html><head><title>Dashboard</title></head><body style="text-align:center">
    <h2>Olá {{u['nome']}}</h2><p>Saldo: R${{ '%.2f'|format(u['saldo']) }}</p>
    <form method="post"><input name="resposta" placeholder="{{a}}+{{b}}?">
    <input type="submit" value="Captcha"></form>
    <p>{{msg}}</p>
    <form method="post"><input name="search" placeholder="Buscar email ou ID">
    <input type="submit" value="Adicionar"></form>
    <form method="post" enctype="multipart/form-data">
        Nome: <input name="nome" value="{{u['nome']}}">
        Foto: <input type="file" name="foto">
        <input type="submit" value="Atualizar">
    </form>
    <ul>{% for e,i,n,f in amigos %}<li><img src="/static/fotos/{{f}}" width="30"> {{n}} ({{e}} - ID:{{i}})</li>{% endfor %}</ul>
    <form method="post" action="/sacar">PIX:<input name="pix" required><input type="submit" value="Sacar"></form>
    {% if email in admin_emails %}<p><a href="/admin">Admin</a></p>{% endif %}
    <div class="ads">[ANÚNCIO]</div>
    </body></html>
    ''', u=u, email=email, a=a, b=b, msg=msg, amigos=amigos, admin_emails=ADMIN_EMAILS)

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session: return redirect('/')
    usuarios = carregar_usuarios()
    u = usuarios[session['email']]
    if u['saldo'] >= 0.33:
        saques = carregar_saques()
        saques.append({'email': session['email'], 'pix': request.form['pix'], 'valor': u['saldo']})
        u['saldo'] = 0.0
        salvar_usuarios(usuarios); salvar_saques(saques)
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
