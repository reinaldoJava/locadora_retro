from flask import Flask, render_template, request, jsonify, session

from src.engine import Engine

app = Flask(__name__)
motor = Engine()
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)

# IMPORTANTE: Para usar "session" no Flask, você OBRIGATORIAMENTE precisa de uma secret key.
# Se isso não estiver aqui, o Flask dá erro interno ao tentar salvar o nome do jogador.
app.secret_key = 'chave_secreta_super_segura_1999'

# ==========================================
# ROTA 1: A PORTA DE ENTRADA (A INTRO)
# ==========================================
@app.route('/')
def tela_inicial():
    session.clear() # Limpa o nome antigo se o cara reiniciar o jogo
    return render_template('intro.html')

# ==========================================
# ROTA 2: O JOGO PRINCIPAL
# ==========================================
@app.route('/jogo')
def tela_jogo():
    # Opcional (Trava de Segurança): Se tentar pular a intro direto pela URL, volta pro início
    if 'nome_jogador' not in session:
        return redirect('/')

    return render_template('index.html') # Aqui é o HTML principal do seu jogo

# ==========================================
# ROTA DA API: RECEBE E SALVA O NOME
# ==========================================
@app.route('/api/iniciar-sessao', methods=['POST'])
def iniciar_sessao():
    dados = request.get_json()

    # Pega o nome, se vier vazio, assume "GERENTE"
    nome_jogador = dados.get('nome', '').strip()
    if not nome_jogador:
        nome_jogador = 'GERENTE'

    # Salva no "cofre" da sessão do Flask
    session['nome_jogador'] = nome_jogador

    return jsonify({"status": "sucesso", "nome_salvo": nome_jogador}), 200

@app.route('/api/proximo-evento', methods=['GET'])
def proximo_evento():
    dados_normalizados = motor.formatar_para_frontend()
    return jsonify(dados_normalizados)

@app.route('/api/escolha', methods=['POST'])
def registrar_escolha():
    indice = request.json.get('indice')
    novo_estado = motor.processar_escolha(indice)

    return jsonify({
        "game_over": motor.verificar_game_over(),
        "estado": novo_estado
    })


if __name__ == '__main__':
    app.run(debug=True)