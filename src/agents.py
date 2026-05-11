from openai import OpenAI

# A mágica do zero custo: apontar o cliente para o localhost na porta do Ollama
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama' # A chave não importa para rodar local, mas a biblioteca exige preencher
)

# Os prompts exatamente como validamos no GDD
# Guardrails de arquitetura: força o LLM a atuar como API de diálogo
INSTRUCAO_GERAL = (
    "=== REGRA DE SISTEMA (STRICT ROLEPLAY) ===\n"
    "Você é um personagem de um jogo. Responda APENAS com a sua fala direta.\n"
    "RESTRIÇÕES CRÍTICAS:\n"
    "- NÃO narre ações em terceira pessoa.\n"
    "- NÃO use asteriscos para simular ações (ex: *sorri*, *olha para o gerente*).\n"
    "- NÃO invente nomes de outros personagens. USE APENAS OS PERSONAGENS CRIADOS NO CONTEXTO.\n"
    "- Fale diretamente com o gerente.\n\n"
    "- TODOS SÃO MUITO EDUCADOS E GENTIS.\n"
    "- IMPROVISAÇÕES CIRURGICAS NO TEXTOS E CONTEXTOS.\n"
    "- NÃO INVENTE NÚMEROS. APENAS TRABALHE COM OS EXISTENTES."
)

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
    # ... (seu código de inicialização do cliente) ...

    prompt_sistema = PROMPTS.get(agente_id, INSTRUCAO_GERAL)
    prompt_usuario = (
        f"[CENA - ANO {ano}]\n"
        f"Situação atual: {contexto_dia}\n\n"
        f"AÇÃO: Dirija-se EXCLUSIVA E DIRETAMENTE ao gerente ({nome_gerente}). "
        f"Dê a sua visão sobre a situação atual baseado no seu cargo e personalidade. "
        f"Seja assertivo, não gagueje, e vá direto ao ponto. "
        f"A cena começa agora:"
    )

    # ADICIONE ESTA LINHA PARA DEBUG:
    # print(f"DEBUG: Enviando para IA -> {prompt_usuario}")

    try:
        resposta = client.chat.completions.create(
            model="llama3.2:1b", # Recomendo fortemente este modelo para evitar recusas
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.1, # Aumentar um pouco ajuda a IA a ser mais "criativa"
            max_tokens=240,
            timeout=120.0
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Chefe, estou meio sem voz agora (Erro: {e})"