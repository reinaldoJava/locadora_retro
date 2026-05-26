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

import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, session, make_response, Response, stream_with_context, jsonify
from src.narrative_director import DiretorNarrativo
from src.engine import Engine
from src.agents import gerar_fala_stream, adicionar_ao_pool, preaquecer_replicas
import random

# ---------------------------------------------------------------------------
# Firestore — cliente compartilhado (mesmo padrão de agents.py)
# Em dev local (sem credenciais GCP) cai no fallback gracioso.
# ---------------------------------------------------------------------------
try:
    from google.cloud import firestore as _fs
    _db_placar = _fs.Client()
    _PLACAR_OK = True
    print("[app] Firestore placar: conectado")
except Exception as _fs_err:
    _db_placar = None
    _PLACAR_OK = False
    print(f"[app] Firestore placar: indisponível ({_fs_err}) — placar desativado")

# ---------------------------------------------------------------------------
# Dados estaticos: game_over events indexados por id
# ---------------------------------------------------------------------------
_BASE_DATA = Path(__file__).resolve().parent / "data"
with open(_BASE_DATA / "game_over.json", "r", encoding="utf-8") as _f:
    _GAME_OVER_EVENTOS = {evt["id"]: evt for evt in json.load(_f)}

_DIFICULDADE_MULT = {"vhs": 0.6, "beta": 1.0, "laser": 1.5}
_DIFICULDADE_NOME = {"vhs": "VHS", "beta": "BETA", "laser": "LASER DISC"}

app = Flask(__name__)
# Em produção (Cloud Run), SECRET_KEY vem do Secret Manager via env var.
# Localmente, usa o valor do .env ou o fallback de dev abaixo.
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_super_segura_1999_dev')


@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 ano
        response.cache_control.public = True
    return response


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
    return render_template('intro.html', tema_visual=session['tema_visual'])

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
    """Recebe o nome e a dificuldade do jogador; retorna o primeiro slide da intro."""
    _nome = (request.form.get('nome', 'Gerente').strip() or 'Gerente')[:15]
    nome_jogador = _nome[0].upper() + _nome[1:] if _nome else 'Gerente'
    dificuldade  = request.form.get('dificuldade', 'beta').lower()
    if dificuldade not in _DIFICULDADE_MULT:
        dificuldade = 'beta'
    diretor = _get_diretor()
    diretor.motor.estado['dificuldade_mult'] = _DIFICULDADE_MULT[dificuldade]
    diretor.motor.estado['dificuldade_nome'] = _DIFICULDADE_NOME[dificuldade]
    session['dificuldade'] = dificuldade
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

def _verificar_e_injetar_crise(diretor):
    """Verifica limiares de metricas e injeta evento de crise se necessario.
    Chamado apos cada processamento de escolha. Nao age se uma crise ja esta ativa."""
    estado = diretor.motor.estado
    if estado.get("crise_ativa_evento"):
        return  # Crise ja ativa; aguarda resolucao

    crises_usadas = estado.get("crises_usadas", [])

    # Determina qual crise deve ser disparada (prioridade: caixa > stress > acervo > tracao)
    crise_id = None
    if estado.get("caixa", 100) <= 0:
        crise_id = "ultimato_advogado_caixa"
    elif estado.get("stress", 0) >= 90:
        crise_id = "ultimato_vagner_operacional"
    elif estado.get("acervo", 50) <= 20:
        crise_id = "ultimato_mauricio_acervo"
    elif estado.get("tracao", 50) <= 10:
        crise_id = "ultimato_leila_tracao"

    if not crise_id:
        return  # Sem crise

    if crise_id in crises_usadas:
        # Segunda ocorrencia: game over imediato
        estado["game_over_forcado"] = True
        return

    # Injeta crise
    crises_usadas.append(crise_id)
    estado["crises_usadas"]    = crises_usadas
    estado["crise_ativa_id"]   = crise_id
    estado["crise_ativa_evento"] = _GAME_OVER_EVENTOS[crise_id]


@app.route('/api/interagir', methods=['POST'])
def interagir():
    """Processa escolha do jogador e avanca o estado narrativo."""
    escolha = request.form.get("choice", type=int)
    diretor = _get_diretor()
    response = diretor.proximo_passo(escolha)
    # Verifica crise apos cada escolha efetiva do jogador
    if escolha is not None:
        _verificar_e_injetar_crise(diretor)
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


@app.route('/api/fala-stream')
def fala_stream_api():
    """Streaming SSE da fala do NPC atual. Lê o evento da sessão, gera via Gemini
    e adiciona a fala completa ao pool ao concluir — abastecendo jogadores futuros."""
    diretor = _get_diretor()
    evt = diretor.motor.obter_evento_atual()
    if not evt or not evt.get("agente_foco"):
        return Response("data: [DONE]\n\n", mimetype='text/event-stream')

    evt_id    = evt.get("id", "")
    agente_id = evt["agente_foco"]
    contexto  = evt.get("contexto_ia", "")
    ano       = diretor.motor.estado.get("ano", 1999)

    temperatura = evt.get("temp_situacao")

    def generate():
        full_text = ""
        for token in gerar_fala_stream(agente_id, contexto, ano, temperatura):
            full_text += token
            # Escapa quebras de linha para o protocolo SSE (cada mensagem é uma linha)
            safe_token = token.replace('\n', '\\n')
            yield f"data: {safe_token}\n\n"
        adicionar_ao_pool(evt_id, full_text)
        # Pré-aquece réplicas de todas as rotas em background enquanto o jogador lê e escolhe
        preaquecer_replicas(evt)
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'   # Desativa buffer do Nginx para SSE
        }
    )


# ---------------------------------------------------------------------------
# Rotas de placar (leaderboard)
# ---------------------------------------------------------------------------

@app.route('/api/salvar_placar', methods=['POST'])
def salvar_placar_api():
    """Salva iniciais e pontuacao no Firestore e retorna o placar atualizado."""
    iniciais    = request.form.get('iniciais', 'AAA').upper()[:3].strip() or 'AAA'
    score       = request.form.get('score', type=int, default=0)
    dificuldade = session.get('dificuldade', 'beta').upper()

    if _PLACAR_OK:
        try:
            _db_placar.collection('placar').add({
                'iniciais':    iniciais,
                'score':       score,
                'dificuldade': dificuldade,
                'timestamp':   datetime.utcnow(),
            })
        except Exception as e:
            print(f"[app] salvar_placar erro: {e}", flush=True)

    return _render_placar_html(score)


@app.route('/api/placar', methods=['GET'])
def placar_api():
    """Retorna o top-10 do placar como fragmento HTML."""
    return _render_placar_html()


def _render_placar_html(score_atual=None):
    """Busca top-10 do Firestore e renderiza fragmento HTML do placar."""
    entradas = []
    if _PLACAR_OK:
        try:
            docs = (
                _db_placar.collection('placar')
                .order_by('score', direction=_fs.Query.DESCENDING)
                .limit(10)
                .stream()
            )
            for doc in docs:
                d = doc.to_dict()
                entradas.append({
                    'iniciais':    d.get('iniciais', '???'),
                    'score':       d.get('score', 0),
                    'dificuldade': d.get('dificuldade', ''),
                })
        except Exception as e:
            print(f"[app] render_placar erro: {e}", flush=True)

    return render_template('placar_fragment.html',
                           entradas=entradas,
                           score_atual=score_atual)


if __name__ == '__main__':
    app.run(debug=True)
