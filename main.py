from flask import Flask, render_template, request, redirect, url_for, session, flash
import os, json, time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'

ARQUIVO_USUARIOS = 'usuarios.json'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB limite (opcional)

# garante que a pasta exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# helpers
def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_usuarios(dados):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_obrigatorio():
    return 'usuario' in session

# --- Normaliza usuários antigos (caso já existam strings simples) ---
def normalizar_estrutura_usuarios(usuarios):
    updated = False
    for k, v in list(usuarios.items()):
        if isinstance(v, str):
            usuarios[k] = {'senha': v, 'tema': 'vermelho', 'avatar': None}
            updated = True
        else:
            # garante chaves
            if 'senha' not in v:
                v['senha'] = ''
            if 'tema' not in v:
                v['tema'] = 'vermelho'
            if 'avatar' not in v:
                v['avatar'] = None
    if updated:
        salvar_usuarios(usuarios)
    return usuarios


@app.route('/eu', methods=['GET'])
def eu():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']
    perfil = usuarios.get(usuario, {})

    return render_template('eu.html', usuario=usuario, perfil=perfil)


# --- Rotas ---

@app.route('/salvar_anotacoes', methods=['POST'])
def salvar_anotacoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']

    anotacao = request.form.get('anotacao', '').strip()

    if anotacao:
        if 'anotacoes' not in usuarios[usuario]:
            usuarios[usuario]['anotacoes'] = []
        usuarios[usuario]['anotacoes'].append(anotacao)
        salvar_usuarios(usuarios)

    return redirect(url_for('eu'))



@app.route('/', methods=['GET', 'POST'])
def login():
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        if usuario in usuarios and usuarios[usuario]['senha'] == senha:
            session['usuario'] = usuario
            return redirect(url_for('home'))
        else:
            return render_template('login.html', erro='Usuário ou senha incorretos')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        senha = request.form['senha']

        if not usuario or not senha:
            return render_template('register.html', erro='Preencha todos os campos')
        if usuario in usuarios:
            return render_template('register.html', erro='Usuário já cadastrado')

        usuarios[usuario] = {
            'senha': senha,
            'tema': 'vermelho',
            'avatar': None
        }
        salvar_usuarios(usuarios)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if not login_obrigatorio():
        return redirect(url_for('login'))
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']
    perfil = usuarios.get(usuario, {})
    return render_template('home.html', usuario=usuario, perfil=perfil)

@app.route('/sobre')
def sobre():
    if not login_obrigatorio():
        return redirect(url_for('login'))
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']
    perfil = usuarios.get(usuario, {})
    return render_template('sobre.html', usuario=usuario, perfil=perfil)

@app.route('/servicos')
def servicos():
    if not login_obrigatorio():
        return redirect(url_for('login'))
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']
    perfil = usuarios.get(usuario, {})
    return render_template('servicos.html', usuario=usuario, perfil=perfil)

@app.route('/contato')
def contato():
    if not login_obrigatorio():
        return redirect(url_for('login'))
    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']
    perfil = usuarios.get(usuario, {})
    return render_template('contato.html', usuario=usuario, perfil=perfil)

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not login_obrigatorio():
        return redirect(url_for('login'))
    


    usuarios = normalizar_estrutura_usuarios(carregar_usuarios())
    usuario = session['usuario']

    if request.method == 'POST':
        # trocar senha
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuarios[usuario]['senha'] = nova_senha

        # trocar tema
        novo_tema = request.form.get('tema')
        if novo_tema:
            usuarios[usuario]['tema'] = novo_tema

        # upload avatar
        if 'avatar' in request.files:
            arquivo = request.files['avatar']
            if arquivo and arquivo.filename:
                if allowed_file(arquivo.filename):
                    nome_seguro = secure_filename(arquivo.filename)
                    timestamp = int(time.time())
                    novo_nome = f"{usuario}_{timestamp}_{nome_seguro}"
                    caminho = os.path.join(app.config['UPLOAD_FOLDER'], novo_nome)
                    arquivo.save(caminho)
                    usuarios[usuario]['avatar'] = novo_nome
                else:
                    return render_template('perfil.html', usuario=usuario, tema=usuarios[usuario].get('tema','vermelho'),
                                        erro='Formato inválido. Use png, jpg, jpeg ou gif.')
        salvar_usuarios(usuarios)
        return render_template('perfil.html', usuario=usuario, tema=usuarios[usuario].get('tema','vermelho'),
                            perfil=usuarios[usuario], msg='Perfil atualizado com sucesso!')

    # GET
    perfil = usuarios.get(usuario, {})
    tema = perfil.get('tema', 'vermelho')
    return render_template('perfil.html', usuario=usuario, tema=tema, perfil=perfil)

if __name__ == '__main__':
    app.run(debug=True)
