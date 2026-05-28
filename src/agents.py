# src/agents.py
# Interface com o modelo de linguagem via Gemini API (compatível com OpenAI SDK).
#
# Responsabilidade: gerar falas dinâmicas para agentes NPC quando o evento define
# um "agente_foco". Expõe duas funções públicas:
#   gerar_fala()        → string completa (uso síncrono / fallback)
#   gerar_fala_stream() → generator de tokens (uso via SSE em /api/fala-stream)
#
# Pool de falas (Firestore com fallback in-memory):
#   Compartilhado entre todas as sessões e instâncias Cloud Run. A primeira geração
#   de cada evento abastece os jogadores subsequentes via random.choice, minimizando
#   chamadas à API. O nome do jogador é substituído no renderer/JS, não no LLM,
#   garantindo que as falas do pool sejam reutilizáveis entre diferentes usuários.
#   Em dev local (sem credenciais GCP), usa dict in-memory automaticamente.
#
# Arquitetura do cliente:
#   OpenAI SDK apontado para o endpoint OpenAI-compatível do Gemini.
#   A api_key é lida da variável de ambiente GEMINI_API_KEY.

import os
import logging
import random
import threading
import time
from openai import OpenAI, RateLimitError

try:
    from google.cloud import firestore as _firestore
    _db = _firestore.Client()
    _FIRESTORE_OK = True
    print("[agents] Firestore: conectado")
except Exception as _fs_err:
    _db = None
    _FIRESTORE_OK = False
    print(f"[agents] Firestore: indisponível ({_fs_err}) — usando pool in-memory")

# Configuração do Logger para alertas no GCP
logger = logging.getLogger("locadora_retro")

_POOL_COLLECTION = "fala_pool"

# LLM_PROVIDER controla qual backend é usado:
#   "ollama"  (padrão) → Ollama local, modelo configurável via LLM_MODEL
#   "gemini"            → Gemini via API OpenAI-compatível, modelo configurável via LLM_MODEL
_PROVIDER = os.environ.get('LLM_PROVIDER', 'ollama').lower()

if _PROVIDER == 'gemini':
    _api_key = os.environ.get('GEMINI_API_KEY', '')
    _MODEL = os.environ.get('LLM_MODEL', 'gemini-3.1-flash-lite')
    print(f"[agents] provider=gemini model={_MODEL} api_key={'SET' if _api_key else 'MISSING'}")
    client = OpenAI(
        base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
        api_key=_api_key
    )
else:
    _MODEL = os.environ.get('LLM_MODEL', 'qwen2.5:1.5b-instruct')
    print(f"[agents] provider=ollama model={_MODEL}")
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama'
    )

# Pool in-memory usado como fallback quando Firestore não está disponível (dev local).
_pool: dict[str, list[str]] = {}
POOL_MAX = 15  # Máximo de variações armazenadas por evento

# Frases de fallback por personagem — exibidas quando a API falha após todas as tentativas.
# Devem soar naturais para não quebrar a imersão.
_FALLBACK: dict[str, str] = {
    "ID_Leila":      "Chefe, me dá um segundo... tô processando tudo isso.",
    "ID_Mauricio":   "Preciso de um instante para organizar meus pensamentos.",
    "ID_Marcos":     "Tô processando, gerente. Me dá um segundo.",
    "ID_Vagner":     "Espera aí, deixa eu calcular direito antes de falar.",
    "ID_Financeiro": "...",
}
_FALLBACK_DEFAULT = "..."

# Configuração de retry para erros 429 (rate limit da API).
# 2 retentativas = 3 chamadas total. Delays: 5s e 10s.
_RETRY_DELAYS = [5, 10]

# Guardrail mínimo compartilhado: ancora o personagem como funcionário falando COM o Gerente.
# Prompt curto é intencional — modelos pequenos (1.5B) obedecem melhor a poucas regras claras.
# Usa "Gerente" como placeholder — substituído pelo nome real no renderer ou no JS.
INSTRUCAO_GERAL = (
    "Você é um funcionário da locadora falando DIRETAMENTE com o Gerente. "
    "Ignore outros personagens mencionados no contexto — dirija-se só ao Gerente. "
    "Responda com 1 a 2 frases curtas. Sem frases de abertura clichê ou repetitivas. "
    "Dê sua opinião — a decisão final é do Gerente, não sua. "
    "PROIBIDO usar adjetivos pejorativos ou depreciativos para descrever clientes, "
    "funcionários ou qualquer pessoa citada no contexto (ex: fofoqueira, metida, difícil, "
    "problemática, chata). Trate todos os personagens com respeito mesmo ao discordar."
)

# Configuração por personagem: system prompt + parâmetros de geração.
# Temperaturas derivadas do perfil narrativo de cada personagem.
PROMPTS: dict[str, dict] = {
    "ID_Leila": {
        "nome": "Leila",
        "system": (
            "Você é Leila, atendente de 22 anos da locadora. "
            "Fale DIRETAMENTE com o Gerente — ignore outros personagens mencionados no contexto. "
            "Sem frases de abertura repetitivas. "
            "Normalmente animada e direta. Em temas de risco financeiro, fica mais contida e séria. "
            "Fala abertamente quando discorda, mas só quando perguntada ou provocada. "
            "Tende a concordar após ouvir o argumento do Gerente. "
            "Use no máximo 1 gíria dos anos 90, só se vier naturalmente."
        ),
        "temperature": 0.42,
        "max_tokens": 85,
    },
    "ID_Mauricio": {
        "nome": "Maurício",
        "system": (
            "Você é Maurício, curador cinéfilo de 30 anos da locadora. "
            "Fale DIRETAMENTE com o Gerente — ignore outros personagens mencionados no contexto. "
            "Sem frases de abertura repetitivas. "
            "Tom equilibrado — você respeita tanto o acervo quanto o financeiro. "
            "Quando discorda, argumenta com elegância e referências cinematográficas, nunca com drama. "
            "Aceita as decisões do Gerente de bom grado. "
            "Permite-se ironia leve quando o momento pede."
        ),
        "temperature": 0.31,
        "max_tokens": 85,
    },
    "ID_Marcos": {
        "nome": "Marcos",
        "system": (
            "Você é Marcos, estagiário de 28 anos da locadora. Você é discreto, observador e pragmático. "
            "Fale DIRETAMENTE com o Gerente — ignore outros personagens mencionados no contexto. "
            "Sem frases de abertura repetitivas. "
            "Você é um cinéfilo equilibrado: entende o valor da arte, mas prioriza a sustentabilidade do negócio. "
            "Curte drum and bass, raves e é fã de Sega — mistura referências de cinema com cultura dos anos 90. "
            "Conhece profundamente o bairro e o perfil dos clientes. "
            "Seu tom é profissional, direto e sem gírias forçadas ou metáforas de nicho. "
            "Aceita a decisão do Gerente, mas sempre dá seu ponto de vista antes."
        ),
        "temperature": 0.25,
        "max_tokens": 85,
    },
    "ID_Vagner": {
        "nome": "Vagner",
        "system": (
            "Você é Vagner, dono de uma videolocadora de bairro em 1999, 43 anos. Seu tom é de comerciante experiente, prático, direto e levemente ranzinza, mas que confia no seu Gerente.\n\n"
            "REGRAS CRÍTICAS DE RESPOSTA:\n"
            "1. Fale DIRETAMENTE com o Gerente. Reaja APENAS e estritamente à última ideia/escolha que o Gerente propôs.\n"
            "2. NÃO INVENTE dados, estatísticas (ex: 'queda de 12%') ou problemas novos que não estão na fala do Gerente.\n"
            "3. Avalie a proposta como um comerciante focado no caixa do dia: se a ideia do Gerente for ruim, critique a perda de dinheiro com unhas e dentes. Se a sacada do Gerente for genial e trouxer lucro, reconheça o mérito com uma resignação admirada.\n"
            "4. Responda com no máximo 2 ou 3 frases curtas, informais e impactantes. Sem clichês corporativos.\n"
            "5. NUNCA use adjetivos pejorativos para descrever clientes ou outros personagens (ex: fofoqueira, chato, difícil, problemático). Critique SITUAÇÕES e NÚMEROS, nunca o caráter de pessoas.\n\n"
            "6. Raramente faça alguma analogia sobre futebol.\n"
            "EXEMPLO DE FEEDBACK RUIM (Prejuízo):\n"
            "Gerente: 'Perdoo os R$15 se ela levar o combo por R$20.'\n"
            "Vagner: 'Peraí. Você tá trocando dinheiro limpo de multa por pipoca que tem custo de reposição? Desse jeito a nossa margem vai pro ralo, rapaz.'\n\n"
            "EXEMPLO DE FEEDBACK BOM (Lucro/Malícia Comercial):\n"
            "Gerente: 'Ela vai gastar R$5 a mais achando que ganhou um desconto. É o paradoxo da escolha.'\n"
            "Vagner: 'Rapaz, você me assusta às vezes. A cliente vai pagar mais caro e sair sorrindo? Vai logo pro balcão antes que eu mude de ideia.'"
        ),
        "temperature": 0.4,
        "max_tokens": 80,
    },
    "ID_Financeiro": {
        "nome": "Vagner",
        "system": (
            "Você é Vagner em modo de emergência financeira. "
            "Fale DIRETAMENTE com o Gerente — ignore outros personagens mencionados no contexto. "
            "Sem frases de abertura. Sem metáforas. Sem emoção. "
            "Apenas números, margens, prazos e riscos objetivos. "
            "Mantenha o respeito pela relação com o Gerente mesmo sendo completamente frio."
        ),
        "temperature": 0.1,
        "max_tokens": 80,
    },
}


def _montar_prompt_usuario(contexto_dia: str, ano: int, nome_personagem: str,
                           argumento: str = "") -> str:
    """Completion anchor: monta o prompt de usuário para o LLM.
    'Gerente' é placeholder — substituído pelo nome real no renderer/JS (pool-safety).

    Sem argumento (situação inicial):
        Personagem apresenta o dilema/desafio ao Gerente SEM recomendar solução.
        Isso evita contradição quando o LLM gerar o pushback na réplica.
    Com argumento (réplica/tréplica):
        Personagem reage DIRETAMENTE ao que o Gerente acabou de dizer.
    """
    base = f"[ANO {ano}] {contexto_dia}\n\n"
    if argumento:
        return (
            base +
            f"O Gerente disse: \"{argumento}\"\n\n"
            f"Reaja DIRETAMENTE a esta afirmação do Gerente. "
            f"{nome_personagem} respondeu:"
        )
    return (
        base +
        f"Apresente ao Gerente a situação e o que está em jogo. "
        f"Não recomende solução — descreva o desafio e deixe a decisão com o Gerente. "
        f"{nome_personagem} disse:"
    )


# ---------------------------------------------------------------------------
# API pública do pool
# ---------------------------------------------------------------------------

def obter_do_pool(evt_id: str) -> str | None:
    """Retorna fala aleatória do pool para o evento ou None se pool vazio.
    Lê do Firestore quando disponível, senão do dict in-memory.
    """
    if _FIRESTORE_OK:
        try:
            doc = _db.collection(_POOL_COLLECTION).document(evt_id).get()
            if doc.exists:
                falas = doc.to_dict().get("falas", [])
                return random.choice(falas) if falas else None
            return None
        except Exception:
            pass  # fallback in-memory
    falas = _pool.get(evt_id, [])
    return random.choice(falas) if falas else None


def adicionar_ao_pool(evt_id: str, fala: str) -> None:
    """Adiciona fala ao pool do evento respeitando o limite POOL_MAX.
    Persiste no Firestore quando disponível, senão no dict in-memory.
    """
    if not fala or not evt_id:
        return
    if _FIRESTORE_OK:
        try:
            ref = _db.collection(_POOL_COLLECTION).document(evt_id)
            doc = ref.get()
            falas = doc.to_dict().get("falas", []) if doc.exists else []
            if len(falas) < POOL_MAX:
                falas.append(fala)
                ref.set({"falas": falas})
            return
        except Exception:
            pass  # fallback in-memory
    if evt_id not in _pool:
        _pool[evt_id] = []
    if len(_pool[evt_id]) < POOL_MAX:
        _pool[evt_id].append(fala)


def preaquecer_replicas(evt: dict) -> None:
    """Dispara threads em background para pré-gerar as réplicas de todas as rotas do evento.
    Chamado ao final do SSE da situação, enquanto o jogador ainda está lendo e escolhendo.
    Pool hit posterior → resposta instantânea sem latência de LLM.
    """
    evt_id    = evt.get("id", "")
    agente_id = evt.get("agente_foco", "ID_Vagner")
    contexto  = evt.get("contexto_ia", "")
    ano       = evt.get("ano", 1999)

    rotas = evt.get("rotas_principais", [])
    for rota_idx, rota in enumerate(rotas):
        if "sub_opcoes" not in rota:
            continue  # só rotas com sub_opcoes têm réplica de LLM
        pool_key  = f"{evt_id}:replica:{rota_idx}"
        if obter_do_pool(pool_key):
            continue  # já aquecido
        argumento = rota.get("fala_gerente", "")
        temp      = rota.get("temp_replica")

        def _gerar(aid=agente_id, ctx=contexto, a=ano, t=temp, arg=argumento, pk=pool_key):
            try:
                fala = gerar_fala(aid, ctx, a, t, argumento=arg)
                adicionar_ao_pool(pk, fala)
            except Exception:
                pass  # falha silenciosa — pool miss será tratado normalmente

        threading.Thread(target=_gerar, daemon=True).start()


# ---------------------------------------------------------------------------
# Geração de falas
# ---------------------------------------------------------------------------

def _config(agente_id: str) -> dict:
    """Retorna a configuração do agente (nome, system, temperature, max_tokens)."""
    cfg = PROMPTS.get(agente_id)
    if cfg:
        return cfg
    nome = agente_id.replace("ID_", "")
    return {"nome": nome, "system": INSTRUCAO_GERAL, "temperature": 0.1, "max_tokens": 50}


def gerar_fala(agente_id: str, contexto_dia: str, ano: int,
               temperatura: float | None = None, argumento: str = "",
               texto_original: str = "") -> str:
    """Geração síncrona completa. Usada para réplica, tréplica e fallback.
    temperatura sobrescreve o default do personagem quando informada.
    argumento = o que o Gerente disse (fala_gerente / argumento_gerente).
    texto_original = texto estático de 1999 ou sentinel "_pending_" de 2026.
    Retry com Exponential Backoff em caso de 429 (rate limit).
    """
    cfg = _config(agente_id)
    # Adiciona o texto_original ao contexto do prompt para que o LLM possa reescrevê-lo
    prompt_usuario = _montar_prompt_usuario(contexto_dia, ano, cfg["nome"], argumento) + f"\nTexto Base: {texto_original}"
    temp = temperatura if temperatura is not None else cfg["temperature"]
    mensagens = [
        {"role": "system", "content": cfg["system"]},
        {"role": "user",   "content": prompt_usuario},
    ]
    for tentativa, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            resposta = client.chat.completions.create(
                model=_MODEL,
                messages=mensagens,
                temperature=temp,
                max_tokens=cfg["max_tokens"],
                stop=['\n'],
                timeout=30.0
            )
            return resposta.choices[0].message.content or ""
        except RateLimitError:
             if tentativa < len(_RETRY_DELAYS):
                 continue
             break
        except Exception as e:
            logger.warning(f"FALHA_LLM: Erro na geração para {agente_id} ({e}). Usando fallback.")
            break

    # Lógica de Fallback Final
    # Se texto_original for o sentinel ou vazio, usa a frase de personalidade
    if not texto_original or texto_original == "_pending_":
        return _FALLBACK.get(agente_id, _FALLBACK_DEFAULT)
    
    # Se for 1999, retorna o texto estático original (ex: resolucao_vagner)
    return texto_original



def gerar_fala_stream(agente_id: str, contexto_dia: str, ano: int,
                      temperatura: float | None = None, argumento: str = ""):
    """Generator de tokens para streaming SSE (situação inicial — sem argumento).
    temperatura sobrescreve o default do personagem quando informada.
    Retry com Exponential Backoff em caso de 429 (rate limit).
    O sleep entre tentativas apenas atrasa o primeiro token — conexão SSE permanece aberta.
    """
    cfg = _config(agente_id)
    prompt_usuario = _montar_prompt_usuario(contexto_dia, ano, cfg["nome"], argumento)
    temp = temperatura if temperatura is not None else cfg["temperature"]
    mensagens = [
        {"role": "system", "content": cfg["system"]},
        {"role": "user",   "content": prompt_usuario},
    ]
    for tentativa, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            stream = client.chat.completions.create(
                model=_MODEL,
                messages=mensagens,
                temperature=temp,
                max_tokens=cfg["max_tokens"],
                stop=['\n'],
                stream=True,
                timeout=30.0
            )
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield token
            return  # stream concluído com sucesso
        except RateLimitError:
            if tentativa < len(_RETRY_DELAYS):
                continue
            yield _FALLBACK.get(agente_id, _FALLBACK_DEFAULT)
            return
        except Exception:
            yield _FALLBACK.get(agente_id, _FALLBACK_DEFAULT)
            return
