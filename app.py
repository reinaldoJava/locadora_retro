# app.py
# Camada de transporte HTTP: define rotas Flask e gerencia estado de sessao.
#
# Padrao de sessao:
#   - DiretorNarrativo e serializado/desserializado a cada request (stateless HTTP).
#   - _extract_data_from_diretor  → dict serializavel salvo na sessao Flask.
#   - _load_diretor_from_data     → reconstroi o objeto a partir desse dict.
#   - _reset_game_state           → limpa a sessao e inicializa estado zerado.
#
# Fluxo de navegacao:
#   GET /          → intro (reseta estado)
#   GET /jogo      → pagina principal (dispara /api/iniciar-game-transition via hx-trigger="load")
#   POST /api/*    → acoes do jogo retornam fragmentos HTML para swap HTMX em #ui-jogo
#                    exceto /api/avancar-intro-slide (ultimo slide) → HX-Redirect: /jogo

from flask import Flask, render_template, request, session, make_response
from src.narrative_director import DiretorNarrativo
from src.engine import Engine
import random

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_1999'


# ---------------------------------------------------------------------------
# Gerenciamento de estado de sessao
# ---------------------------------------------------------------------------

def _get_game_state_data_from_session():
    if 'game_state_data' not in session:
        _reset_game_state()
    return session['game_state_data']

def _save_game_state_data_to_session(data):
    session['game_state_data'] = data
    session.modified = True

def _load_diretor_from_data(data):
    """Reconstroi DiretorNarrativo a partir do dict serializado na sessao."""
    motor = Engine(reset_on_init=False)
    motor.estado = data['motor_estado']
    motor.indice_arquivo_atual = data['motor_indice_arquivo_atual']

    # Se uma rota 2026 foi escolhida, aponta arquivos_cenario[1] para o arquivo correto
    rota_id = data.get('diretor_rota_escolhida_id')
    if rota_id:
        motor.arquivos_cenario[1] = f"evento_2026_gatilho_rota_{rota_id}.json"
    motor._carregar_arquivo_atual()

    diretor = DiretorNarrativo(motor)
    diretor.passo_cinematico            = data['diretor_passo_cinematico']
    diretor.nome_jogador                = data['diretor_nome_jogador']
    diretor.roteiro_intro               = data['diretor_roteiro_intro']
    diretor.slide_atual                 = data['diretor_slide_atual']
    diretor._initial_game_transition_step = data.get('diretor_initial_game_transition_step', 0)
    diretor.passo_prologo_2026          = data.get('diretor_passo_prologo_2026', 0)
    diretor.passo_encruzilhada_2026     = data.get('diretor_passo_encruzilhada_2026', 0)
    diretor.rota_escolhida_id           = data.get('diretor_rota_escolhida_id', None)
    diretor._passo_dialogo_evento       = data.get('diretor_passo_dialogo_evento', 0)
    diretor._ultimo_evento_dialogo_id   = data.get('diretor_ultimo_evento_dialogo_id', "")
    return diretor

def _extract_data_from_diretor(diretor_instance):
    """Extrai dict serializavel de DiretorNarrativo para persistencia na sessao."""
    return {
        'motor_estado':                       diretor_instance.motor.estado,
        'motor_indice_arquivo_atual':         diretor_instance.motor.indice_arquivo_atual,
        'diretor_passo_cinematico':           diretor_instance.passo_cinematico,
        'diretor_nome_jogador':               diretor_instance.nome_jogador,
        'diretor_roteiro_intro':              diretor_instance.roteiro_intro,
        'diretor_slide_atual':                diretor_instance.slide_atual,
        'diretor_initial_game_transition_step': diretor_instance._initial_game_transition_step,
        'diretor_passo_prologo_2026':         diretor_instance.passo_prologo_2026,
        'diretor_passo_encruzilhada_2026':    diretor_instance.passo_encruzilhada_2026,
        'diretor_rota_escolhida_id':          diretor_instance.rota_escolhida_id,
        'diretor_passo_dialogo_evento':       diretor_instance._passo_dialogo_evento,
        'diretor_ultimo_evento_dialogo_id':   diretor_instance._ultimo_evento_dialogo_id,
    }

def _get_diretor():
    return _load_diretor_from_data(_get_game_state_data_from_session())

def _save_diretor(diretor_instance):
    _save_game_state_data_to_session(_extract_data_from_diretor(diretor_instance))

def _reset_game_state():
    """Limpa a sessao e inicializa um novo DiretorNarrativo zerado."""
    session.clear()
    motor_inicial = Engine()
    diretor_inicial = DiretorNarrativo(motor_inicial)
    _save_diretor(diretor_inicial)
    session['nome_jogador'] = "Gerente"
    session['tema_visual']  = random.choice(['a', 'b', 'c'])
    session.modified = True


# ---------------------------------------------------------------------------
# Rotas de pagina (retornam HTML completo)
# ---------------------------------------------------------------------------

@app.route('/')
def tela_inicial():
    """Entrada do jogo: reseta estado e exibe tela de login (intro.html)."""
    _reset_game_state()
    return render_template('intro.html')

@app.route('/jogo')
def index_jogo():
    """Pagina principal do jogo. O #ui-jogo dispara /api/iniciar-game-transition via hx-trigger=load."""
    diretor = _get_diretor()
    _save_diretor(diretor)

    if 'tema_visual' not in session:
        session['tema_visual'] = random.choice(['a', 'b', 'c'])
        session.modified = True
    tema = session['tema_visual']

    return make_response(render_template('index.html', tema_visual=tema))


# ---------------------------------------------------------------------------
# Rotas da introducao (fragmentos HTMX → swap em #intro-container)
# ---------------------------------------------------------------------------

@app.route('/api/iniciar-intro', methods=['POST'])
def iniciar_intro_api():
    """Recebe o nome do jogador e retorna o primeiro slide da intro."""
    nome_jogador = request.form.get('nome', 'GERENTE').strip() or 'GERENTE'
    diretor = _get_diretor()
    response = diretor.iniciar_intro(nome_jogador)
    _save_diretor(diretor)
    return response

@app.route('/api/avancar-intro-slide', methods=['POST'])
def avancar_intro_slide_api():
    """Avanca para o proximo slide. No ultimo slide, emite HX-Redirect para /jogo."""
    diretor = _get_diretor()
    response = diretor.avancar_intro_slide()
    _save_diretor(diretor)
    return response


# ---------------------------------------------------------------------------
# Rotas cinematicas (fragmentos HTMX → swap em #ui-jogo)
# ---------------------------------------------------------------------------

@app.route('/api/animacao-concluida', methods=['POST'])
def animacao_concluida_api():
    """Notificacao do frontend quando uma animacao de terminal termina."""
    diretor = _get_diretor()
    response = diretor.handle_animacao_concluida()
    _save_diretor(diretor)
    return response

@app.route('/api/iniciar-game-transition', methods=['POST'])
def iniciar_game_transition_api():
    """Passo 1 da transicao inicial: exibe 'SISTEMA CARREGADO' + botao INICIAR SISTEMA."""
    diretor = _get_diretor()
    response = diretor.start_game_transition()
    _save_diretor(diretor)
    return response

@app.route('/api/transicao-para-game-1999', methods=['POST'])
def iniciar_game_1999_sequence_api():
    """Passo 2: exibe animacao do terminal GIF e inicia musica de 1999."""
    diretor = _get_diretor()
    response = diretor.start_game_1999_sequence()
    _save_diretor(diretor)
    return response


# ---------------------------------------------------------------------------
# Rotas de gameplay (fragmentos HTMX → swap em #ui-jogo)
# ---------------------------------------------------------------------------

@app.route('/api/interagir', methods=['POST'])
def interagir():
    """Processa escolha do jogador e avanca o estado narrativo."""
    escolha = request.form.get("choice", type=int)
    diretor = _get_diretor()
    response = diretor.proximo_passo(escolha)
    _save_diretor(diretor)
    return response

@app.route('/api/reset', methods=['POST'])
def reset_jogo():
    """Reseta estado e retorna ao primeiro frame de gameplay (usado em dev)."""
    _reset_game_state()
    diretor = _get_diretor()
    dados_motor = diretor.motor.formatar_para_frontend()
    response = make_response(diretor._renderizar_gameplay(dados_motor))
    _save_diretor(diretor)
    return response


if __name__ == '__main__':
    app.run(debug=True)
