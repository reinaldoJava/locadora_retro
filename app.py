from flask import Flask, render_template, request, jsonify, session, redirect

from src.engine import Engine
import json
import os


app = Flask(__name__)
motor = Engine()
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
def index_jogo():
    # Se o cara chegou aqui e não tem nome na sessão,
    # ou se queremos garantir que o jogo comece do zero:
    if 'nome_jogador' not in session:
        global motor
        from src.engine import Engine
        motor = Engine()
        print(">>> [SEGURANÇA] Nome não encontrado, motor resetado para 1999.")

    return render_template('index.html') # ou o nome do seu arquivo principal

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


@app.route('/api/escolha', methods=['POST'])
def registrar_escolha():
    indice = request.json.get('indice')
    novo_estado = motor.processar_escolha(indice)

    return jsonify({
        "game_over": motor.verificar_game_over(),
        "estado": novo_estado
    })


@app.route('/api/intro-roteiro', methods=['GET'])
def intro_roteiro():
    caminho_arquivo = os.path.join(app.root_path, 'data', 'intro.json')
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        dados_intro = json.load(f)
    return jsonify(dados_intro), 200

# ==========================================
# ROTA PRINCIPAL
# ==========================================
@app.route('/api/proximo-evento', methods=['GET'])
def proximo_evento():
    nome_jogador = session.get('nome_jogador', 'GERENTE')
    # 1. Pega o estado do motor
    dados_evento = motor.formatar_para_frontend()

    # 2. Aplica as regras de negócio de UI (Flags)
    dados_evento['play_gif_terminal'] = _gatilho_gif_terminal(dados_evento)
    dados_evento['wormhole'] = _gatilho_wormhole(dados_evento)

    # [!] DÚVIDA AQUI: Precisamos de uma flag como dados_evento['cena_4_personagens'] = _gatilho_final_1999(dados_evento)

    # 3. Formata os dados finais
    dados_evento['texto'] = _processar_texto(dados_evento.get('texto', ''), nome_jogador)
    dados_evento['nome_usuario'] = nome_jogador.upper()

    return jsonify(dados_evento), 200


@app.route('/api/reset', methods=['POST'])
def reset_jogo():
    # 1. Limpa os cookies (nome do jogador, etc)
    session.clear()

    # 2. Reseta o objeto motor que está na memória do servidor
    motor.reset_completo()

    return jsonify({"status": "sucesso"}), 200

# ==========================================
# FUNÇÕES AUXILIARES (HELPERS)
# ==========================================
def _processar_texto(texto_bruto, nome_jogador):
    """Substitui o placeholder pelo nome do jogador no texto."""
    if not texto_bruto:
        return ""
    return texto_bruto.replace("GERENTE:", f"{nome_jogador.upper()}:")

def _gatilho_gif_terminal(dados_evento):
    """Verifica e dispara o GIF do terminal apenas na primeira vez em 1999."""
    ja_viu = session.get('ja_viu_gif_terminal', False)
    ano_atual = str(dados_evento.get('ano', '1999'))

    if ano_atual == "1999" and not ja_viu:
        session['ja_viu_gif_terminal'] = True
        session.modified = True
        print(">>> GATILHO DO GIF ATIVADO! <<<", flush=True)
        return True
    return False

def _gatilho_wormhole(dados_evento):
    """Verifica e dispara a viagem no tempo apenas na primeira vez em 2026."""
    ja_viajou = session.get('ja_viajou_no_tempo', False)
    ano_atual = str(dados_evento.get('ano', '1999'))

    if ano_atual == "2026" and not ja_viajou:
        session['ja_viajou_no_tempo'] = True
        session.modified = True
        print(">>> GATILHO DO VÍDEO WORMHOLE/SHUTDOWN ATIVADO! <<<", flush=True)
        return True
    return False



if __name__ == '__main__':
    app.run(debug=True)