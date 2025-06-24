from flask import Flask, request, redirect, session, render_template_string
import json, os, random
import uuid

app = Flask(__name__)
app.secret_key = 'segredo'

USUARIOS_FILE = 'usuarios.json'
SAQUES_FILE = 'saques.json'
ADMIN_EMAILS = ['tattoozen18@gmail.com', 'paudoce176@gmail.com']

# Inicializa os arquivos
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, 'w') as f:
        json.dump({}, f)
if not os.path.exists(SAQUES_FILE):
    with open(SAQUES_FILE, 'w') as f:
        json.dump([], f)

def carregar_usuarios():
    return json.load(open(USUARIOS_FILE, 'r'))
def salvar_usuarios(usuarios):
    json.dump(usuarios, open(USUARIOS_FILE, 'w'))
def carregar_saques():
    return json.load(open(SAQUES_FILE, 'r'))
def salvar_saques(saques):
    json.dump(saques, open(SAQUES_FILE, 'w'))

def gerar_id7():
    return str(random.randint(10**6, 10**7-1))

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html><html><head>
      <meta charset="utf-8">
      <title>Bem-vindo | Site Captcha</title>
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script>
    </head><body>
    <nav><a href="/">Home</a> | <a href="/login_page">Login</a> | <a href="/cadastro_page">Cadastro</a></nav>
    <h1>Ganhe recompensas resolvendo captchas</h1>
    <p>Resolva desafios, ganhe saldo e saque via PIX. Em breve: chat, amigos, rastreamento...</p>
    <p><a href="/privacy">Política de Privacidade</a> | <a href="/terms">Termos de Uso</a> | <a href="/contact">Contato</a></p>
    <div class="ads">[ANÚNCIO]</div>
    </body></html>
    ''')

@app.route('/terms')
@app.route('/privacy')
@app.route('/contact')
def info_pages():
    page = request.path.strip('/')
    titles = {'terms':'Termos de Uso','privacy':'Política de Privacidade','contact':'Contato'}
    return f"<h2>{titles.get(page,page)}</h2><p>Conteúdo de {titles.get(page,page)} aqui.</p><p><a href='/'>Voltar</a></p>"

@app.route('/cadastro_page')
def cadastro_page():
    return render_template_string('''
      <!DOCTYPE html><html><head><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script><title>Cadastro</title></head>
      <body><h2>Cadastro</h2>
      <form method="post" action="/cadastro">
        Email:<input name="email" required><br>Senha:<input name="senha" type="password" required><br>
        <input type="submit" value="Cadastrar">
      </form>
      <p><a href="/">Voltar</a></p></body></html>
    ''')

@app.route('/login_page')
def login_page():
    return render_template_string('''
      <!DOCTYPE html><html><head><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script><title>Login</title></head>
      <body><h2>Login</h2>
      <form method="post" action="/login">
        Email:<input name="email" required><br>Senha:<input name="senha" type="password" required><br>
        <input type="submit" value="Entrar">
      </form>
      <p><a href="/">Voltar</a></p></body></html>
    ''')

@app.route('/cadastro', methods=['POST'])
def cadastro():
    email = request.form['email']
    senha = request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios:
        return 'Email já cadastrado. <a href="/">Voltar</a>'
    usuarios[email] = {
        'senha': senha,
        'saldo': 0.0,
        'id7': gerar_id7(),
        'friends': []
    }
    salvar_usuarios(usuarios)
    return redirect('/login_page')

@app.route('/login', methods=['POST'])
def login():
    email, senha = request.form['email'], request.form['senha']
    usuarios = carregar_usuarios()
    if email in usuarios and usuarios[email]['senha']==senha:
        session['email']=email
        return redirect('/dashboard')
    return 'Login inválido. <a href="/login_page">Tente novamente</a>'

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'email' not in session:
        return redirect('/')
    email = session['email']
    usuarios = carregar_usuarios()
    u = usuarios[email]
    saldo = u['saldo']; msg=''
    if request.method=='POST' and 'resposta' in request.form:
        try:
            if int(request.form['resposta'])==session.get('captcha'):
                ganho=0.33; u['saldo']+=ganho; salvar_usuarios(usuarios)
                msg=f'Captcha certo! +R$ {ganho:.2f}'
            else: msg='Captcha incorreto.'
        except: msg='Resposta inválida.'
    # pesquisa e add friend
    if request.method=='POST' and 'search_email' in request.form:
        target = request.form['search_email']
        if target in usuarios and target!=email:
            if target not in u['friends']:
                u['friends'].append(target); msg='Amigo adicionado.'
            else: msg='Já é amigo.'
            salvar_usuarios(usuarios)

    # gerar novo captcha
    a,b = random.randint(1,10),random.randint(1,10)
    session['captcha']=a+b

    friends = [(f, usuarios[f]['id7']) for f in u['friends']]

    return render_template_string('''
    <!DOCTYPE html><html><head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180526871985180" crossorigin="anonymous"></script><title>Dashboard</title>
    </head><body>
    <nav><a href="/dashboard">Dashboard</a> | <a href="/logout">Logout</a></nav>
    <div>Seu ID: {{u["id7"]}}</div>
    <div>Saldo: R${{"%.2f"|format(saldo)}}</div>
    <div>
      <div style="float:left;width:30%;"><div class="ads">[AD]</div></div>
      <div style="margin:0 auto;width:40%;">
        <h3>Olá {{email}}</h3>
        <form method="post">
          <input name="resposta" placeholder="Quanto é {{a}}+{{b}}?">
          <input type="submit" value="Enviar">
        </form><p>{{msg}}</p>
        <form method="post"><input name="search_email" placeholder="Buscar email"><input type="submit" value="Buscar/Adicionar"></form>
        <ul>{% for f,i in friends %}<li>{{f}} (ID:{{i}})</li>{% endfor %}</ul>
        <form action="/sacar" method="post">PIX:<input name="pix" required><input type="submit" value="Sacar"></form>
        {% if email in admin_emails %}<p><a href="/admin">Admin</a></p>{% endif %}
      </div>
      <div style="float:right;width:30%;"><div class="ads">[AD]</div></div>
    </div>
    <div style="clear:both; text-align:center;"><div class="ads">[AD]</div></div>
    </body></html>
    ''', email=email, saldo=saldo, msg=msg, a=a, b=b, u=u,
       friends=friends, admin_emails=ADMIN_EMAILS)

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session: return redirect('/')
    usuarios = carregar_usuarios(); u=usuarios[session['email']]
    if u['saldo']>=0.33:
        saques=carregar_saques(); saques.append({'email':session['email'],'pix':request.form['pix'],'valor':u['saldo']})
        u['saldo']=0; salvar_saques(saques); salvar_usuarios(usuarios)
        return 'Saque enviado! <a href="/dashboard">Voltar</a>'
    return 'Saldo insuficiente. <a href="/dashboard">Voltar</a>'

@app.route('/admin')
def admin():
    if session.get('email') not in ADMIN_EMAILS: return redirect('/')
    usuarios=carregar_usuarios(); saques=carregar_saques()
    return render_template_string('''
      <h2>Admin</h2><ul>{% for e,d in usuarios.items() %}<li>{{e}} - ID:{{d['id7']}} - R${{"%.2f"|format(d['saldo'])}}</li>{% endfor %}</ul>
      <h3>Saques:</h3><ul>{% for s in saques %}<li>{{s['email']}} PIX:{{s['pix']}} R${{"%.2f"|format(s['valor'])}}</li>{% endfor %}</ul>
      <p><a href="/dashboard">Voltar</a></p>
    ''', usuarios=usuarios, saques=saques)

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
