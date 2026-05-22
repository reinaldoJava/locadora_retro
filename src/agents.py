# src/agents.py
# Interface com o modelo de linguagem local via Ollama (compativel com OpenAI SDK).
#
# Responsabilidade: gerar falas dinamicas para agentes NPC quando o evento define
# um "agente_foco". O caller (engine.py via renderer_mixin.py) passa o contexto do
# dia e recebe a fala como string HTML-safe, pronta para renderizacao.
#
# Arquitetura: cliente OpenAI apontado para localhost:11434 (Ollama). Cada agente
# tem um system-prompt fixo em PROMPTS que define personalidade e restricoes de
# roleplay. O user-prompt e montado dinamicamente com contexto, ano e nome do gerente.

from openai import OpenAI

# Cliente aponta para Ollama rodando localmente; a api_key e exigida pela biblioteca
# mas ignorada pelo servidor Ollama.
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

# Guardrail de roleplay: impede que o LLM narre acoes, invente personagens ou
# quebre a imersao do jogo. Compartilhado por todos os agentes como prefixo.
INSTRUCAO_GERAL = (
    "=== REGRA DE SISTEMA (STRICT ROLEPLAY) ===\n"
    "Você é um personagem de um jogo. Responda APENAS com a sua fala direta.\n"
    "RESTRIÇÕES CRÍTICAS:\n"
    "- NÃO narre ações em terceira pessoa.\n"
    "- NÃO use asteriscos para simular ações (ex: *sorri*, *olha para o gerente*).\n"
    "- NÃO invente nomes de outros personagens. USE APENAS OS PERSONAGENS CRIADOS NO CONTEXTO.\n"
    "- Fale diretamente com o gerente.\n\n"
    "- TODOS SÃO EDUCADOS E GENTIS.\n"
    "- IMPROVISAÇÕES CIRURGICAS NO TEXTOS SEM ALTERAR OS CONTEXTOS.\n"
    "- NÃO INVENTE NÚMEROS. APENAS TRABALHE COM OS JÁ EXISTENTES."
)

# System-prompts individuais: personalidade + tarefa de cada NPC.
PROMPTS = {
    "ID_Leila": f"{INSTRUCAO_GERAL}Você é Leila, atendente jovem, enérgica e focada no cliente. "
                "Em 1999, use poucas gírias da época. Bem extovertida e gosta de novidades. Em 2026, foque em métricas e redes sociais. "
                "Sua Tarefa: Informe o Gerente sobre o problema e sugira uma saída amigável. Seja breve.",

    "ID_Mauricio": f"{INSTRUCAO_GERAL}Você é Maurício, curador cinéfilo, polido e e introvertido, tem um bom coração. É apaixonado pelo que faz. "
                   "Você prioriza a preservação das fitas acima do lucro."
                   "Sua Tarefa: Reclame da situação exigindo proteção ao acervo. Seja breve e eloquente, as vezes rebuscado.",

    "ID_Vagner": f"{INSTRUCAO_GERAL}Você é Vagner, dono da locadora, gerente financeiro, conservador. Torcedor fanático do Vitoria "
                 "Você tem pavor de perder dinheiro. A Blockbuster é o rival. "
                 "Sua Tarefa: Alerte o Gerente sobre o risco financeiro e exija lucro com bom senso. Tem um bom coração e gosta dos funcionários",

    "ID_Financeiro": f"{INSTRUCAO_GERAL}Você é a voz da consciência financeira (sob os preceitos de Vagner). "
                     "Sua Tarefa: Fale com o gerente focando puramente no fluxo de caixa e regras do sistema. Seja implacável e breve."
}


def gerar_fala(agente_id, contexto_dia, ano, nome_gerente):
    """Gera a fala de um NPC via LLM local.

    Monta o user-prompt com contexto do dia, ano e nome do gerente,
    e retorna a fala gerada como string. Em caso de falha de conexao
    com o Ollama, retorna uma fala de fallback para nao travar o jogo.
    """
    prompt_sistema = PROMPTS.get(agente_id, INSTRUCAO_GERAL)
    prompt_usuario = (
        f"[CENA - ANO {ano}]\n"
        f"Situação atual: {contexto_dia}\n\n"
        f"AÇÃO: Dirija-se EXCLUSIVA E DIRETAMENTE ao gerente ({nome_gerente}). "
        f"Dê a sua visão sobre a situação atual baseado no seu cargo e personalidade. "
        f"Seja assertivo, não gagueje, e vá direto ao ponto. "
        f"A cena começa agora:"
    )

    try:
        resposta = client.chat.completions.create(
            model="qwen2.5-instruct",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.5,
            max_tokens=240,
            timeout=120.0
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Chefe, estou meio sem voz agora (Erro: {e})"
