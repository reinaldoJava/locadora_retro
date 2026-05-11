import json
import os
import sys
import time
from pathlib import Path

from agents import gerar_fala
from engine import Engine

# Configuração de caminhos para garantir que funcione em qualquer OS
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")

def carregar_json(nome_arquivo):
    """Lê um arquivo JSON da pasta data."""
    caminho = os.path.join(DATA_DIR, nome_arquivo)
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {nome_arquivo} não encontrado em {DATA_DIR}")
        sys.exit(1)


import random

def montar_linha_do_tempo(dados_eventos):
    """
    Constrói a jornada de 10 dias dinamicamente, evitando hardcoding de IDs.
    - Dia 1: Evento fixo de introdução.
    - Dias 2 a 6: Sorteados entre os eventos restantes de 1999.
    - Dias 7 a 10: Sorteados entre os eventos de 2026.
    """
    # Agrupa eventos por ano
    eventos_1999 = [v for k, v in dados_eventos.items() if v.get("ano") == 1999]
    eventos_2026 = [v for k, v in dados_eventos.items() if v.get("ano") == 2026]

    # Isola o evento de introdução (Dona Sônia) garantindo que seja o dia 1
    intro = next((e for e in eventos_1999 if "dia1" in e["id"]), None)

    # Remove a intro da pool para não ser sorteada novamente
    pool_1999 = [e for e in eventos_1999 if e != intro]

    import random
    random.shuffle(pool_1999)
    random.shuffle(eventos_2026)

    timeline = []

    if intro:
        timeline.append(intro)

    # Completa 1999 pegando os próximos 5 eventos da pool embaralhada
    timeline.extend(pool_1999[:5])

    # Adiciona 4 eventos da pool de 2026
    timeline.extend(eventos_2026[:4])

    return timeline

def exibir_transicao(slug, dados_narrativos):
    """Exibe textos dramáticos do arquivo nao_canonico.json."""
    info = dados_narrativos.get(slug)
    if info:
        print("\n" + "=".center(50, "="))
        if "titulo" in info: print(f"\n{info['titulo']}")
        print(f"\n{info['texto']}")
        print("\n" + "=".center(50, "=") + "\n")
        time.sleep(3)

def iniciar_jogo():
    # 1. Importação dos Dados
    dados_1999 = carregar_json("eventos_1999.json")
    dados_2026 = carregar_json("eventos_2026.json") # Carrega o segundo arquivo!
    narrativas_db = carregar_json("nao_canonico.json")
    introducao = carregar_json("inicializcao_game.json")
    salto_temporal = carregar_json("salto_temporal.json")

    # Junta o conteúdo dos dois arquivos em uma lista só
    dados_brutos = dados_1999 + dados_2026

    # AJUSTE BLINDADO: Mapeia o JSON não importa o formato que você usou!
    eventos_db = {}

    if isinstance(dados_brutos, list):
        for item in dados_brutos:
            if "id" in item:
                # Se o JSON tiver a estrutura: {"id": "1999_...", "ano": 1999}
                eventos_db[item["id"]] = item
            else:
                # Se o JSON tiver a estrutura: {"1999_...": {"ano": 1999}}
                for chave, valor in item.items():
                    if isinstance(valor, dict):
                        valor["id"] = chave
                        eventos_db[chave] = valor

    # CHECAGEM DE SEGURANÇA (Mantida para garantir)
    chaves_carregadas = list(eventos_db.keys())
    if "2026_dilema_autenticidade_malu2000" not in chaves_carregadas:
        print("\n❌ ERRO FATAL: O evento de 2026 ainda não foi encontrado!")
        print(f"👉 Chaves carregadas:\n{chaves_carregadas}\n")
        sys.exit(1)

    # 2. Inicialização dos Motores
    motor = Engine()
    linha_do_tempo = montar_linha_do_tempo(eventos_db)

    print("\n" + "="*50)
    print("📼 LOCADORA RETRÔ: GERENTE DE DUAS ERAS 📼".center(50))
    print("="*50)
    time.sleep(1)

    # ... RESTANTE DA SUA FUNÇÃO CONTINUA EXATAMENTE IGUAL A PARTIR DAQUI ...
    # === NOVO: PEDIR O NOME DO GERENTE ===

    # === NOVO: PEDIR O NOME DO GERENTE ===
    nome_gerente = ""
    while not nome_gerente:
        nome_gerente = input("\n📝 Digite o seu nome para assumir a gerência: ").strip()

    # Capitaliza a primeira letra do nome
    nome_gerente = nome_gerente.capitalize()

    print(f"\n🔑 Parabéns, {nome_gerente}! Aqui estão as chaves. A locadora agora é sua.")
    time.sleep(2)

    # 3. Loop Principal (10 Dias)
    for indice, evento in enumerate(linha_do_tempo):
        dia_atual = indice + 1
        motor.estado["dia_atual"] = dia_atual

        # SUBSTITUIÇÃO CIRÚRGICA:
        # Verifica se o evento pertence a 2026 e se a transição ainda não foi exibida.
        # (Supondo que 'evento' seja o dicionário do JSON)

        if evento.get("ano") == 2026 and not motor.estado.get("transicao_2026_feita", False):
            exibir_transicao("transicao_2026", narrativas_db)
            motor.estado["transicao_2026_feita"] = True  # Trava para não repetir no dia seguinte

        motor.mostrar_status_completo()
        print(f"📅 ANO: {evento['ano']} | DIA: {dia_atual}/10")
        print(f"👔 GERENTE DE PLANTÃO: {nome_gerente}\n") # Mostra o nome no painel
        # === ADICIONE ESTA LINHA: Exibe o contexto da situação para o jogador ===
        print(f"📖 CONTEXTO: {evento['contexto_ia']}")
        # Chamada ao Agente de IA (Ollama/Docker)
        try:
            fala_agente = gerar_fala(
                evento["agente_foco"],
                evento["contexto_ia"],
                evento["ano"],
                nome_gerente
            )
            nome_exibicao = evento["agente_foco"].replace("ID_", "").upper()
            print(f"\n🗣️ {nome_exibicao}: \"{fala_agente}\"")
        except Exception as e:
            # Adicione o {e} no final para vermos o erro exato:
            print(f"\n⚠️ [Erro na IA]: O agente está sem voz hoje. Motivo: {e}")
            fala_agente = "Gerente, temos um problema técnico e de gestão aqui!"

        # ==========================================
        # ÁRVORE DE DIÁLOGO (Camadas 2 a 5)
        # ==========================================

        # --- FASE 1: ESCOLHA DA ABORDAGEM PRINCIPAL ---
        print("\nQual é a sua abordagem inicial?")
        rotas = evento.get("rotas_principais", [])

        for i, rota in enumerate(rotas, 1):
            print(f" [{i}] [{rota['nome']}] \"{rota['fala_gerente']}\"")

        escolha_rota = 0
        while escolha_rota not in range(1, len(rotas) + 1):
            try:
                entrada = input("\n👉 Sua abordagem: ").strip()
                escolha_rota = int(entrada)
            except ValueError:
                print("Digite apenas o número da opção.")

        rota_selecionada = rotas[escolha_rota - 1]

        # --- FASE 2: O PUSHBACK DO PERSONAGEM ---
        print("\n" + "="*50)
        print(f"👔 {nome_gerente.upper()}: \"{rota_selecionada['fala_gerente']}\"")
        time.sleep(1.5)

        nome_agente = evento["agente_foco"].replace("ID_", "").upper()
        print(f"🗣️ {nome_agente}: \"{rota_selecionada['pushback_vagner']}\"")
        print("="*50)
        time.sleep(1)

        # --- FASE 3: A RÉPLICA TÉCNICA (SUB-OPÇÕES) ---
        print("\nComo você argumenta tecnicamente?")
        sub_opcoes = rota_selecionada["sub_opcoes"]
        for i, sub in enumerate(sub_opcoes, 1):
            print(f" [{i}] [Foco em {sub['foco']}] \"{sub['argumento_gerente']}\"")

        escolha_sub = 0
        while escolha_sub not in range(1, len(sub_opcoes) + 1):
            try:
                entrada = input("\n👉 Seu argumento: ").strip()
                escolha_sub = int(entrada)
            except ValueError:
                print("Digite apenas o número da opção.")

        sub_selecionada = sub_opcoes[escolha_sub - 1]

        # --- FASE 4: RESOLUÇÃO E IMPACTO ---
        print("\n" + "="*50)
        print(f"👔 {nome_gerente.upper()}: \"{sub_selecionada['argumento_gerente']}\"")
        time.sleep(1.5)
        print(f"🗣️ {nome_agente}: \"{sub_selecionada['resolucao_vagner']}\"")
        print("="*50)

        # Processamento da Decisão no Motor
        impacto = sub_selecionada["impacto"]
        motor.aplicar_impacto(impacto)
        time.sleep(1)

        # Verificação de Condição de Derrota
        derrota, motivo = motor.verificar_game_over()
        if derrota:
            print(f"\n❌ GAME OVER! {motivo}")
            return

    # 4. Finalização (Vitória)
    print("✅ [Sistema] Dia concluído! Carregando o próximo dia...\n")
    time.sleep(1)
    print(f"⭐ SCORE FINAL: {motor.calcular_score_final():.1f} pontos.")


if __name__ == "__main__":
    try:
        iniciar_jogo()
    except KeyboardInterrupt:
        print("\n\nSessão encerrada. As fitas foram rebobinadas.")