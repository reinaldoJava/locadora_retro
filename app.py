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

@app.route('/api/proximo-evento', methods=['GET'])
def proximo_evento():
    nome_jogador = session.get('nome_jogador', 'GERENTE')

    # 1. Pega os dados do motor de regras
    dados_evento = motor.formatar_para_frontend()

    # ==========================================
    # LÓGICA DO BURACO DE MINHOCA (BLINDADA)
    # ==========================================
    # Pega o ano atual do JSON. Se não vier nada, assume '1999'
    ano_atual = str(dados_evento.get('ano', '1999'))

    # Verifica se o jogador já passou pela transição nesta sessão
    ja_viajou = session.get('ja_viajou_no_tempo', False)

    print(f"[DEBUG TEMPORAL] Ano: {ano_atual} | Já viajou? {ja_viajou}", flush=True)

    # Se estamos em 2026 e ele AINDA NÃO viu o vídeo:
    if ano_atual == "2026" and ja_viajou is False:
        dados_evento['wormhole'] = True
        session['ja_viajou_no_tempo'] = True  # Trava de segurança para não repetir o vídeo
        session.modified = True
        print(">>> GATILHO DO VÍDEO ATIVADO! <<<", flush=True)
    else:
        dados_evento['wormhole'] = False
    # ==========================================
    # ==========================================
    # LÓGICA DO GIF DO TERMINAL (INTRO -> DIA 1)
    # ==========================================
    # Precisamos saber em que "dia" ou "rodada" o jogador está.
    # Assumindo que seu motor devolve um 'dia' ou 'turno' no JSON:
    dia_atual = dados_evento.get('dia', 0) # Substitua 'dia' pela variável que seu motor usa

    # ==========================================
    # LÓGICA DO GIF DO TERMINAL (Gatilho na primeira vez em 1999)
    # ==========================================
    ja_viu_gif = session.get('ja_viu_gif_terminal', False)
    ano_atual = str(dados_evento.get('ano', '1999'))

    # Pegamos o texto para saber se é a introdução ou não
    texto_da_vez = dados_evento.get('texto', '').upper()
    eh_introducao = "BEM-VINDO" in texto_da_vez or "MISSÃO" in texto_da_vez # Ajuste conforme seu texto de intro

    print(f"[DEBUG GIF] Ano: {ano_atual} | Já viu? {ja_viu_gif} | Dia: {dados_evento.get('dia')}", flush=True)

    # DISPARO: Se o ano é 1999, não é mais a intro (ou é o dia 0/1) e ainda não viu
    if ano_atual == "1999" and not ja_viu_gif:
        # Se o seu log diz Dia 0 agora, vamos disparar no 0 ou no 1
        # Vamos forçar o disparo se o 'dia' for 0 ou 1, o que vier primeiro
        dados_evento['play_gif_terminal'] = True
        session['ja_viu_gif_terminal'] = True
        session.modified = True
        print(">>> GATILHO DO GIF ATIVADO! <<<", flush=True)
    else:
        dados_evento['play_gif_terminal'] = False

    # 2. Processa o texto (Substitui GERENTE pelo nome do jogador)
    texto_bruto = dados_evento.get('texto', '')
    texto_processado = texto_bruto.replace("GERENTE:", f"{nome_jogador.upper()}:")

    dados_evento['texto'] = texto_processado
    dados_evento['nome_usuario'] = nome_jogador.upper()

    return jsonify(dados_evento), 200

if __name__ == '__main__':
    app.run(debug=True)