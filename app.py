from flask import Flask, render_template, request, session, make_response
from src.narrative_director import DiretorNarrativo
from src.engine import Engine

import random

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_1999' # Mantenha sua chave secreta!

# --- Funções Auxiliares para Gerenciamento de Estado na Sessão ---

def _get_game_state_data_from_session():
    """Retrieves game state data from session, or initializes if not present."""
    print(">>> _get_game_state_data_from_session: Verificando sessão...")
    if 'game_state_data' not in session:
        print(">>> _get_game_state_data_from_session: 'game_state_data' NÃO encontrado na sessão. Resetando estado.")
        _reset_game_state()
    else:
        print(">>> _get_game_state_data_from_session: 'game_state_data' encontrado na sessão.")
    return session['game_state_data']

def _save_game_state_data_to_session(data):
    """Saves game state data to session."""
    session['game_state_data'] = data
    session.modified = True
    print(">>> _save_game_state_data_to_session: Estado do jogo salvo na sessão.")

def _load_diretor_from_data(data):
    """Reconstructs DiretorNarrativo object from serializable data."""
    print(">>> _load_diretor_from_data: Carregando diretor a partir dos dados.")
    motor = Engine(reset_on_init=False) # <--- ALTERADO: Não reseta o motor ao carregar da sessão
    motor.estado = data['motor_estado']
    motor.indice_arquivo_atual = data['motor_indice_arquivo_atual']
    # Se uma rota 2026 foi escolhida, aponta arquivos_cenario[1] para o arquivo correto
    rota_id = data.get('diretor_rota_escolhida_id')
    if rota_id:
        motor.arquivos_cenario[1] = f"evento_2026_gatilho_rota_{rota_id}.json"
    motor._carregar_arquivo_atual()

    diretor = DiretorNarrativo(motor)
    diretor.passo_cinematico = data['diretor_passo_cinematico']
    diretor.nome_jogador = data['diretor_nome_jogador']
    diretor.roteiro_intro = data['diretor_roteiro_intro']
    diretor.slide_atual = data['diretor_slide_atual']
    diretor._initial_game_transition_step = data.get('diretor_initial_game_transition_step', 0) # Carregar o novo estado
    print(f">>> _load_diretor_from_data: _initial_game_transition_step carregado: {diretor._initial_game_transition_step}")
    diretor.passo_prologo_2026 = data.get('diretor_passo_prologo_2026', 0)
    diretor.passo_encruzilhada_2026 = data.get('diretor_passo_encruzilhada_2026', 0)
    diretor.rota_escolhida_id = data.get('diretor_rota_escolhida_id', None)
    diretor._passo_dialogo_evento = data.get('diretor_passo_dialogo_evento', 0)
    diretor._ultimo_evento_dialogo_id = data.get('diretor_ultimo_evento_dialogo_id', "")
    return diretor

def _extract_data_from_diretor(diretor_instance):
    """Extracts serializable data from DiretorNarrativo object."""
    data = {
        'motor_estado': diretor_instance.motor.estado,
        'motor_indice_arquivo_atual': diretor_instance.motor.indice_arquivo_atual,
        'diretor_passo_cinematico': diretor_instance.passo_cinematico,
        'diretor_nome_jogador': diretor_instance.nome_jogador,
        'diretor_roteiro_intro': diretor_instance.roteiro_intro,
        'diretor_slide_atual': diretor_instance.slide_atual,
        'diretor_initial_game_transition_step': diretor_instance._initial_game_transition_step,
        'diretor_passo_prologo_2026': diretor_instance.passo_prologo_2026,
        'diretor_passo_encruzilhada_2026': diretor_instance.passo_encruzilhada_2026,
        'diretor_rota_escolhida_id': diretor_instance.rota_escolhida_id,
        'diretor_passo_dialogo_evento': diretor_instance._passo_dialogo_evento,
        'diretor_ultimo_evento_dialogo_id': diretor_instance._ultimo_evento_dialogo_id,
    }
    print(f">>> _extract_data_from_diretor: _initial_game_transition_step extraído: {diretor_instance._initial_game_transition_step}")
    return data

def _get_diretor():
    """Gets the current DiretorNarrativo instance, loading from session."""
    game_state_data = _get_game_state_data_from_session()
    return _load_diretor_from_data(game_state_data)

def _save_diretor(diretor_instance):
    """Saves the current DiretorNarrativo instance's state to session."""
    game_state_data = _extract_data_from_diretor(diretor_instance)
    _save_game_state_data_to_session(game_state_data)

def _reset_game_state():
    """Resets the entire game state in the session."""
    session.clear()
    motor_inicial = Engine() # <--- Aqui o reset_on_init=True é o padrão
    diretor_inicial = DiretorNarrativo(motor_inicial)

    _save_diretor(diretor_inicial) # This will now save a dictionary
    session['nome_jogador'] = "Gerente" # Default name, can be overwritten by intro
    session['tema_visual'] = random.choice(['a', 'b', 'c'])  # Sorteia tema por partida
    session.modified = True # Ensure session is marked as modified
    print(">>> ESTADO DO JOGO RESETADO NA SESSÃO <<<")

# ==========================================
# ROTA 1: A PORTA DE ENTRADA (A INTRO)
# ==========================================
@app.route('/')
def tela_inicial():
    print(">>> Rota / (tela_inicial) acessada.")
    _reset_game_state() # Garante um estado limpo ao iniciar a intro
    return render_template('intro.html')

# ==========================================
# ROTA 2: O JOGO PRINCIPAL
# ==========================================
@app.route('/jogo')
def index_jogo():
    print(">>> Rota /jogo (index_jogo) acessada.")
    # Carrega o estado do diretor da sessão para garantir que ele seja persistido
    diretor = _get_diretor()
    _save_diretor(diretor) # Salva o estado atualizado (mesmo que não alterado)

    # Garante tema sorteado; passa explicitamente para o template (não depende de session no Jinja2)
    if 'tema_visual' not in session:
        session['tema_visual'] = random.choice(['a', 'b', 'c'])
        session.modified = True
    tema = session['tema_visual']

    response = make_response(render_template('index.html', tema_visual=tema))
    return response


# ==========================================
# NOVAS ROTAS DA INTRODUÇÃO (HTMX)
# ==========================================
@app.route('/api/iniciar-intro', methods=['POST'])
def iniciar_intro_api():
    print(">>> Rota /api/iniciar-intro acessada.")
    nome_jogador = request.form.get('nome', 'GERENTE').strip()
    if not nome_jogador:
        nome_jogador = 'GERENTE'

    diretor = _get_diretor()
    response = diretor.iniciar_intro(nome_jogador)
    _save_diretor(diretor)
    return response

@app.route('/api/avancar-intro-slide', methods=['POST'])
def avancar_intro_slide_api():
    print(">>> Rota /api/avancar-intro-slide acessada.")
    diretor = _get_diretor()
    response = diretor.avancar_intro_slide()
    _save_diretor(diretor)
    return response

# NOVA ROTA: Notificação de animação concluída do frontend
@app.route('/api/animacao-concluida', methods=['POST'])
def animacao_concluida_api():
    print(">>> Rota /api/animacao-concluida acessada.")
    diretor = _get_diretor()
    response = diretor.handle_animacao_concluida()
    _save_diretor(diretor)
    return response

# NOVA ROTA: Inicia a transição do game principal (chamada pelo botão "ESTABELECER CONEXÃO")
@app.route('/api/iniciar-game-transition', methods=['POST'])
def iniciar_game_transition_api():
    print(">>> Rota /api/iniciar-game-transition acessada.")
    diretor = _get_diretor()
    response = diretor.start_game_transition()
    _save_diretor(diretor)
    return response

# NOVA ROTA: Inicia a sequência de animação do terminal e música do game 1999 (chamada pelo botão "iniciar sistema")
@app.route('/api/transicao-para-game-1999', methods=['POST'])
def iniciar_game_1999_sequence_api():
    print(">>> Rota /api/transicao-para-game-1999 acessada.")
    diretor = _get_diretor()
    response = diretor.start_game_1999_sequence()
    _save_diretor(diretor)
    return response

# ==========================================
# ROTAS PRINCIPAIS DO JOGO (HTMX)
# ==========================================
@app.route('/api/interagir', methods=['POST'])
def interagir():
    print(">>> Rota /api/interagir acessada.")
    escolha = request.form.get("choice", type=int) # HTMX envia como form data

    diretor = _get_diretor()
    response = diretor.proximo_passo(escolha)
    _save_diretor(diretor)
    return response

@app.route('/api/reset', methods=['POST'])
def reset_jogo():
    print(">>> Rota /api/reset acessada.")
    _reset_game_state() # Reseta o estado do jogo na sessão

    # Após resetar, renderiza a tela inicial do jogo
    diretor = _get_diretor()
    dados_motor = diretor.motor.formatar_para_frontend()
    response = make_response(diretor._renderizar_gameplay(dados_motor))
    _save_diretor(diretor)
    return response

if __name__ == '__main__':
    app.run(debug=True)