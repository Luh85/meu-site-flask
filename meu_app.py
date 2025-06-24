          {% for m in chat_msgs %}
            <p><b>{{ 'Você' if m['de']==email else u[m['de']]['nome'] }}</b>: {{ m['txt'] }}</p>
          {% endfor %}
        </div>
        <p><a href="/dashboard">Voltar para Dashboard</a></p>
      </div>
      <div style="width:20%">{% for _ in range(3) %}<div class="ads">[ANÚNCIO]</div>{% endfor %}</div>
    </div></body></html>
    ''', user=user, email=email, amigos=amigos, msg=msg, chat_msgs=chat_msgs, u=u)

@app.route('/chat_count')
def chat_count():
    if 'email' not in session:
        return jsonify({'count': 0})
    email = session['email']
    msgs = carregar_msgs()
    count = sum(1 for m in msgs if m['para'] == email)
    return jsonify({'count': count})

@app.route('/sacar', methods=['POST'])
def sacar():
    if 'email' not in session:
        return redirect('/')
    u = carregar_usuarios()
    s = carregar_saques()
    user = u[session['email']]
    if user['saldo'] >= 0.33:
        s.append({'email': session['email'], 'pix': request.form['pix'], 'valor': user['saldo']})
        user['saldo'] = 0
        salvar_usuarios(u)
        salvar_saques(s)
        return 'Saque enviado! <a href="/dashboard">Voltar</a>'
    return 'Saldo insuficiente. <a href="/dashboard">Voltar</a>'

@app.route('/admin')
def admin():
    if session.get('email') not in ADMIN_EMAILS:
        return redirect('/')
    u = carregar_usuarios()
    s = carregar_saques()
    return render_template_string('''
    <h2>Admin</h2>
    <ul>
      {% for e, d in u.items() %}
        <li>{{ e }} - ID: {{ d['id7'] }} - R${{ '%.2f'|format(d['saldo']) }}</li>
      {% endfor %}
    </ul>
    <h3>Saques:</h3>
    <ul>
      {% for x in s %}
        <li>{{ x['email'] }} - PIX: {{ x['pix'] }} - R${{ '%.2f'|format(x['valor']) }}</li>
      {% endfor %}
    </ul>
    <p><a href="/dashboard">Voltar</a></p>
    ''', u=u, s=s)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
