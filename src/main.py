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
    eventos_1999 = [v for k, v in dados_eventos.items() if v.get("ano") == 1999]
    eventos_2026 = [v for k, v in dados_eventos.items() if v.get("ano") == 2026]

    intro = next((e for e in eventos_1999 if "dia1" in e["id"]), None)
    encruzilhada = next((e for e in eventos_2026 if e.get("tipo_evento") == "decisao_mestra"), None)

    pool_1999 = [e for e in eventos_1999 if e != intro]
    random.shuffle(pool_1999)

    timeline = []
    if intro: timeline.append(intro)

    timeline.extend(pool_1999[:5]) # Adiciona Dias 2 ao 6

    if encruzilhada:
        timeline.append(encruzilhada) # Adiciona o Dia 7 exato

    # Retorna a timeline inicial E o pool de 2026 para sortearmos os dias 8+ dinamicamente
    return timeline, eventos_2026

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
    dados_2026 = carregar_json("eventos_2026.json")
    narrativas_db = carregar_json("nao_canonico.json")
    introducao = carregar_json("inicializacao_game.json")
    salto_temporal = carregar_json("evento_salto_temporal.json")

    # Junta o conteúdo dos dois arquivos em uma lista só
    dados_brutos = dados_1999 + dados_2026

    # AJUSTE BLINDADO: Mapeia o JSON não importa o formato que você usou!
    eventos_db = {}
    if isinstance(dados_brutos, list):
        for item in dados_brutos:
            if "id" in item:
                eventos_db[item["id"]] = item
            else:
                for chave, valor in item.items():
                    if isinstance(valor, dict):
                        valor["id"] = chave
                        eventos_db[chave] = valor

    # CHECAGEM DE SEGURANÇA
    chaves_carregadas = list(eventos_db.keys())
    if "evento_encruzilhada_2026" not in chaves_carregadas:
        print("\n❌ ERRO FATAL: O evento de 2026 ainda não foi encontrado!")
        print(f"👉 Chaves carregadas:\n{chaves_carregadas}\n")
        sys.exit(1)

    # 2. Inicialização dos Motores
    # 2. Inicialização dos Motores
    motor = Engine()
    linha_do_tempo, pool_2026 = montar_linha_do_tempo(eventos_db) # Recebe as 2 variáveis agora!

    print("\n" + "="*50)
    print("📼 LOCADORA RETRÔ: GERENTE DE DUAS ERAS 📼".center(50))
    print("="*50)
    time.sleep(1)

    nome_gerente = ""
    while not nome_gerente:
        nome_gerente = input("\n📝 Digite o seu nome para assumir a gerência: ").strip()
    nome_gerente = nome_gerente.capitalize()

    print(f"\n🔑 Parabéns, {nome_gerente}! Aqui estão as chaves. A locadora agora é sua.")
    time.sleep(2)

    # 3. Loop Principal (Usando Range de 1 a 10 para podermos puxar eventos dinamicamente)
    for dia_atual in range(1, 11):
        motor.estado["dia_atual"] = dia_atual

        # ==========================================
        # BUSCADOR DINÂMICO DE EVENTOS
        # ==========================================
        if dia_atual <= len(linha_do_tempo):
            evento = linha_do_tempo[dia_atual - 1] # Dias 1 a 7 já estão prontos
        else:
            # Dias 8, 9 e 10: Sorteia da rota escolhida!
            rota_atual = motor.estado.get("rota_2026")
            eventos_validos = [e for e in pool_2026 if e.get("gatilho_rota") == rota_atual and e not in linha_do_tempo]

            if eventos_validos:
                evento = random.choice(eventos_validos)
                linha_do_tempo.append(evento) # Trava o evento para não repetir
            else:
                print("\n[SISTEMA] Não há mais eventos para esta rota!")
                break # Encerra o jogo se acabar os eventos

        # ==========================================
        # O SALTO TEMPORAL
        # ==========================================
        if evento.get("ano") == 2026 and not motor.estado.get("transicao_2026_feita", False):
            # Aqui você pode chamar a leitura do salto_temporal.json que montamos na última resposta
            print("\n" + "🌀 ALERTA DE ANOMALIA: O BURACO DE MINHOCA 🌀".center(50, "="))
            time.sleep(2)
            motor.estado["transicao_2026_feita"] = True

        motor.mostrar_status_completo()
        print(f"📅 ANO: {evento.get('ano', '????')} | DIA: {dia_atual}/10")
        print(f"👔 GERENTE DE PLANTÃO: {nome_gerente}\n")
        print(f"📖 CONTEXTO: {evento.get('contexto_ia', '')}")

        # ==========================================
        # RAMIFICAÇÃO 1: A ENCRUZILHADA (DIA 7)
        # ==========================================
        if evento.get("tipo_evento") == "decisao_mestra":
            print(f"\n{evento['fala_narrativa']}")
            print(f"\n👔 {nome_gerente.upper()}: {evento['discurso_gerente']}")

            print("\nQual será o novo modelo de negócios da Locadora?")
            rotas = evento.get("rotas_principais", [])
            for i, rota in enumerate(rotas, 1):
                print(f" [{i}] {rota['nome']} \n     > {rota['descricao']}")

            escolha_rota = 0
            while escolha_rota not in range(1, len(rotas) + 1):
                try:
                    escolha_rota = int(input("\n👉 Sua decisão: ").strip())
                except ValueError:
                    pass

            rota_selecionada = rotas[escolha_rota - 1]
            motor.estado["rota_2026"] = rota_selecionada["id_opcao"] # Salva "A", "B", "C" ou "D"

            # Aplica o impacto (Note a chave "impacto_sistema")
            motor.aplicar_impacto(rota_selecionada["impacto_sistema"])
            time.sleep(1)

        # ==========================================
        # RAMIFICAÇÃO 2: OS EVENTOS DE 2026 (DIA 8 AO 10)
        # ==========================================
        elif evento.get("ano") == 2026:
            print(f"\n--- {evento.get('titulo', 'Evento')} ---")

            # Printa os múltiplos diálogos do JSON de 2026
            for fala in evento.get("dialogos_iniciais", []):
                nome_agente = fala["agente"].replace("ID_", "").upper()
                print(f"🗣️ {nome_agente}: \"{fala['fala']}\"")
                time.sleep(1.5)

            print("\nComo você argumenta tecnicamente?")
            opcoes = evento.get("opcoes", [])
            for i, op in enumerate(opcoes, 1):
                print(f" [{i}] [{op['foco']}] \"{op['argumento_gerente']}\"")

            escolha_sub = 0
            while escolha_sub not in range(1, len(opcoes) + 1):
                try:
                    escolha_sub = int(input("\n👉 Sua opção: ").strip())
                except ValueError:
                    pass

            sub_selecionada = opcoes[escolha_sub - 1]
            print("\n" + "="*50)
            print(f"👔 {nome_gerente.upper()}: \"{sub_selecionada['argumento_gerente']}\"")
            time.sleep(1)
            print(f"🗣️ EQUIPE: {sub_selecionada['treplica']}")
            print("="*50)

            # Aplica o impacto (Note a chave "impactos")
            motor.aplicar_impacto(sub_selecionada["impactos"])
            time.sleep(1)

        # ==========================================
        # RAMIFICAÇÃO 3: OS EVENTOS DE 1999 (DIA 1 AO 6)
        # ==========================================
        else:
            try:
                fala_agente = gerar_fala(evento["agente_foco"], evento["contexto_ia"], evento["ano"], nome_gerente)
                nome_exibicao = evento["agente_foco"].replace("ID_", "").upper()
                print(f"\n🗣️ {nome_exibicao}: \"{fala_agente}\"")
            except Exception as e:
                print(f"\n⚠️ [Erro na IA]: {e}")

            print("\nQual é a sua abordagem inicial?")
            rotas = evento.get("rotas_principais", [])
            for i, rota in enumerate(rotas, 1):
                print(f" [{i}] [{rota['nome']}] \"{rota['fala_gerente']}\"")

            escolha_rota = 0
            while escolha_rota not in range(1, len(rotas) + 1):
                try:
                    escolha_rota = int(input("\n👉 Sua abordagem: ").strip())
                except ValueError:
                    pass

            rota_selecionada = rotas[escolha_rota - 1]
            print("\n" + "="*50)
            print(f"👔 {nome_gerente.upper()}: \"{rota_selecionada['fala_gerente']}\"")
            nome_agente = evento["agente_foco"].replace("ID_", "").upper()
            print(f"🗣️ {nome_agente}: \"{rota_selecionada['pushback_vagner']}\"")
            print("="*50)

            print("\nComo você argumenta tecnicamente?")
            sub_opcoes = rota_selecionada["sub_opcoes"]
            for i, sub in enumerate(sub_opcoes, 1):
                print(f" [{i}] [Foco em {sub['foco']}] \"{sub['argumento_gerente']}\"")

            escolha_sub = 0
            while escolha_sub not in range(1, len(sub_opcoes) + 1):
                try:
                    escolha_sub = int(input("\n👉 Seu argumento: ").strip())
                except ValueError:
                    pass

            sub_selecionada = sub_opcoes[escolha_sub - 1]
            print("\n" + "="*50)
            print(f"👔 {nome_gerente.upper()}: \"{sub_selecionada['argumento_gerente']}\"")
            print(f"🗣️ {nome_agente}: \"{sub_selecionada['resolucao_vagner']}\"")
            print("="*50)

            # Aplica o impacto (Note a chave "impacto")
            motor.aplicar_impacto(sub_selecionada["impacto"])
            time.sleep(1)

        # Checagem de Game Over Universal
        derrota, motivo = motor.verificar_game_over()
        if derrota:
            print(f"\n❌ GAME OVER! {motivo}")
            return

    # Finalização
    print("✅ [Sistema] Dia concluído! Carregando o próximo dia...\n")
    time.sleep(1)
    print(f"⭐ SCORE FINAL: {motor.calcular_score_final():.1f} pontos.")


if __name__ == "__main__":
    try:
        iniciar_jogo()
    except KeyboardInterrupt:
        print("\n\nSessão encerrada. As fitas foram rebobinadas.")