# src/engine.py
# Maquina de estados narrativa: carrega eventos JSON, processa escolhas
# e calcula o estado das metricas (caixa, tracao, acervo, stress).
#
# Modelo de dados:
#   arquivos_cenario  — lista de arquivos JSON processados em sequencia
#                       [0] eventos_1999.json  → [1] evento_2026_gatilho_rota_X.json
#   estado            — dict mutavel com metricas, indice de evento e buffers de dialogo
#   eventos           — lista de eventos do arquivo atual (carregada em memoria)
#
# Fluxo de escolha (multi-turno):
#   1. formatar_para_frontend() — monta o frame atual para o DiretorNarrativo
#   2. processar_escolha(idx)   — aplica impactos e avanca o indice_evento
#   Buffers texto_gerente_pendente / texto_treplica_pendente permitem
#   exibir a fala do Gerente e a treplica do NPC antes de avancar o evento.

import json
import os
from pathlib import Path


class Engine:

    def __init__(self, lista_cenarios=None, reset_on_init=True):
        self.dia_atual = 1
        self.fluxo_atual = "inicio"
        self.historico_escolhas = []
        self.estado = {
            "indice_evento": 0,
            "rota_pendente_idx": None,
            "texto_treplica_pendente": None,
            "historico_rotas": [],
            "caixa": 100,
            "tracao": 50,
            "acervo": 50,
            "stress": 0
        }
        self.eventos = []
        self.indice_arquivo_atual = 0

        if reset_on_init:
            self.reset_completo()
            if lista_cenarios is None:
                lista_cenarios = ['eventos_1999.json', 'eventos_2026.json']
            self.arquivos_cenario = lista_cenarios
            self._carregar_arquivo_atual()
        else:
            # Modo de reconstrucao a partir de sessao: arquivos definidos externamente
            if lista_cenarios is None:
                lista_cenarios = ['eventos_1999.json', 'eventos_2026.json']
            self.arquivos_cenario = lista_cenarios

    def _carregar_arquivo_atual(self):
        """Le o arquivo JSON do cenario corrente e popula self.eventos."""
        if self.indice_arquivo_atual >= len(self.arquivos_cenario):
            self.eventos = []
            return
        arquivo = self.arquivos_cenario[self.indice_arquivo_atual]
        caminho = os.path.join(Path(__file__).resolve().parent.parent, "data", arquivo)
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        self.eventos = list(dados.values()) if isinstance(dados, dict) else dados

    def obter_evento_atual(self):
        """
        Retorna o proximo evento que satisfaca o gatilho de rota, ou None se
        o arquivo atual foi consumido (sinaliza virada de cenario).
        Eventos com gatilho_rota so aparecem se a rota correspondente estiver
        no historico_rotas do estado.
        """
        while self.estado["indice_evento"] < len(self.eventos):
            evt = self.eventos[self.estado["indice_evento"]]
            gatilho = evt.get("gatilho_rota")
            if not gatilho or gatilho in self.estado["historico_rotas"]:
                return evt
            self.estado["indice_evento"] += 1

        # Arquivo esgotado: avanca para o proximo cenario
        self.indice_arquivo_atual += 1
        self.estado["indice_evento"] = 0
        return None

    def formatar_para_frontend(self):
        """
        Monta o dict de estado do frame atual para consumo pelo DiretorNarrativo.

        Prioridade de exibicao (do mais especifico ao mais geral):
          1. texto_gerente_pendente — fala intercalada do Gerente (antes da treplica)
          2. texto_treplica_pendente — resposta do NPC apos a escolha do jogador
          3. evento atual — conteudo narrativo + opcoes de escolha
          4. virada_1999 / fim — sinais de transicao de fase
        """
        # Fala pendente do Gerente (exibida antes da treplica do NPC)
        if self.estado.get("texto_gerente_pendente"):
            return {
                "ano": self.estado.get("ano_buffer", 1999),
                "personagem": "Gerente",
                "texto": self.estado["texto_gerente_pendente"],
                "opcoes": ["Continuar"],
                "estado": self.estado
            }

        # Treplica pendente do NPC
        if self.estado.get("texto_treplica_pendente"):
            return {
                "ano": self.estado.get("ano_buffer", 1999),
                "personagem": self.estado.get("agente_atual", "Vagner"),
                "texto": self.estado["texto_treplica_pendente"],
                "opcoes": ["Continuar"],
                "estado": self.estado
            }

        evt = self.obter_evento_atual()
        if not evt:
            # indice_arquivo_atual == 1 e indice_evento == 0: acabou 1999, nao ha mais 2026 generico
            if self.indice_arquivo_atual == 1 and self.estado["indice_evento"] == 0:
                return {"virada_1999": True}
            return {"fim": True}

        # Sub-opcoes de uma rota: exibe pushback do Vagner + escolha granular
        if self.estado.get("rota_pendente_idx") is not None:
            rota = evt["rotas_principais"][self.estado["rota_pendente_idx"]]
            return {
                "personagem": self.estado.get("agente_atual", "Vagner"),
                "texto": rota.get('pushback_vagner', ''),
                "opcoes": [sub.get("foco", "Opcao") for sub in rota.get("sub_opcoes", [])],
                "estado": self.estado
            }

        # Evento padrao: agrega contexto, narracao e dialogos em um unico texto
        texto_partes = []
        if "contexto_ia"       in evt: texto_partes.append(evt["contexto_ia"])
        if "fala_narrativa"    in evt: texto_partes.append(f"Narrador:\n{evt['fala_narrativa']}")
        if "discurso_gerente"  in evt: texto_partes.append(f"Gerente:\n{evt['discurso_gerente']}")
        if "dialogos_iniciais" in evt:
            for d in evt["dialogos_iniciais"]:
                agente = d["agente"].replace("ID_", "")
                texto_partes.append(f"{agente}:\n{d['fala']}")
        texto_final = "\n\n".join(texto_partes)

        # Resolve personagem em foco para o spotlight de atores
        if "agente_foco" in evt:
            personagem = evt["agente_foco"].replace("ID_", "")
        elif "discurso_gerente" in evt:
            personagem = "Gerente"
        elif "dialogos_iniciais" in evt and evt["dialogos_iniciais"]:
            personagem = evt["dialogos_iniciais"][0]["agente"].replace("ID_", "")
        else:
            personagem = "Sistema"

        # Opcoes de escolha: rotas_principais ou opcoes simples
        if "rotas_principais" in evt:
            opcoes_txt = [r.get("nome", r.get("descricao", "Opcao")) for r in evt["rotas_principais"]]
        elif "opcoes" in evt:
            opcoes_txt = [o.get("foco", o.get("argumento_gerente", "Opcao")) for o in evt["opcoes"]]
        else:
            opcoes_txt = []

        return {
            "ano": evt.get("ano", 1999),
            "personagem": personagem,
            "texto": texto_final,
            "opcoes": opcoes_txt,
            "estado": self.estado
        }

    def processar_escolha(self, indice_opcao):
        """
        Aplica a escolha do jogador ao estado.

        Maquina de sub-estados:
          - texto_gerente_pendente   → limpa buffer, volta ao evento
          - texto_treplica_pendente  → limpa buffer, avanca indice_evento
          - rota_pendente_idx        → aplica sub_opcao escolhida (impacto + treplica)
          - evento com sub_opcoes    → registra rota, seta gerente_pendente
          - evento com treplica      → aplica impacto, seta treplica_pendente
          - evento simples           → aplica impacto, avanca indice_evento
        """
        if self.estado.get("texto_gerente_pendente"):
            self.estado["texto_gerente_pendente"] = None
            if (not self.estado.get("texto_treplica_pendente") and
                    self.estado.get("rota_pendente_idx") is None):
                self.estado["indice_evento"] += 1
                self.estado.pop("ano_buffer", None)
            return self.estado

        if self.estado.get("texto_treplica_pendente"):
            self.estado["texto_treplica_pendente"] = None
            self.estado.pop("ano_buffer", None)
            self.estado["indice_evento"] += 1
            return self.estado

        evt = self.obter_evento_atual()
        if not evt:
            return self.estado

        # Sub-opcao dentro de uma rota ja selecionada
        if self.estado.get("rota_pendente_idx") is not None:
            rota = evt["rotas_principais"][self.estado["rota_pendente_idx"]]
            sub_opcao = rota["sub_opcoes"][indice_opcao]
            self._aplicar_impacto_dinamico(sub_opcao)
            self.estado["texto_treplica_pendente"] = sub_opcao.get(
                "resolucao_vagner", sub_opcao.get("argumento_gerente", ""))
            self.estado["rota_pendente_idx"] = None
            return self.estado

        escolha = None
        if "rotas_principais" in evt:
            escolha = evt["rotas_principais"][indice_opcao]
            if "sub_opcoes" in escolha:
                # Rota com sub-opcoes: registra rota, espera pushback + sub-escolha
                self.estado["historico_rotas"].append(escolha.get("id_rota", ""))
                self.estado["rota_pendente_idx"] = indice_opcao
                agente_foco_default = evt.get("agente_foco", "ID_Vagner").replace("ID_", "")
                pushback = escolha.get("pushback_vagner", "")
                self.estado["agente_atual"] = self._detectar_agente_pushback(pushback, agente_foco_default)
                self.estado["texto_gerente_pendente"] = escolha.get("fala_gerente", "")
                return self.estado

        elif "opcoes" in evt:
            escolha = evt["opcoes"][indice_opcao]
            if escolha.get("argumento_gerente") or escolha.get("treplica"):
                id_escolha = escolha.get("id_opcao", escolha.get("id_rota", ""))
                if id_escolha:
                    self.estado["historico_rotas"].append(id_escolha)
                self._aplicar_impacto_dinamico(escolha)
                if escolha.get("argumento_gerente"):
                    self.estado["texto_gerente_pendente"] = escolha["argumento_gerente"]
                if escolha.get("treplica"):
                    self.estado["texto_treplica_pendente"] = escolha["treplica"]
                    self.estado["agente_atual"] = "Sistema"
                self.estado["ano_buffer"] = evt.get("ano", 1999)
                return self.estado

        # Escolha simples: aplica impacto e avanca
        if escolha:
            id_escolha = escolha.get("id_opcao", escolha.get("id_rota", ""))
            if id_escolha:
                self.estado["historico_rotas"].append(id_escolha)
            self._aplicar_impacto_dinamico(escolha)

        self.estado["indice_evento"] += 1
        return self.estado

    def _detectar_agente_pushback(self, pushback_text, agente_foco_default):
        """Identifica qual personagem fala no pushback pelo prefixo 'Nome:'."""
        nomes = {"Vagner": "Vagner", "Leila": "Leila",
                 "Mauricio": "Mauricio", "Gerente": "Gerente"}
        for nome, agente in nomes.items():
            if pushback_text.startswith(f"{nome}:"):
                return agente
        return agente_foco_default

    def _aplicar_impacto_dinamico(self, dict_opcao):
        """Aplica deltas numericos do campo 'impacto' ao estado de metricas."""
        impactos = dict_opcao.get("impacto",
                   dict_opcao.get("impactos",
                   dict_opcao.get("impacto_sistema", {})))
        for k, v in impactos.items():
            if isinstance(v, (int, float)) and k in self.estado:
                self.estado[k] = max(0, self.estado.get(k, 0) + v)

    def verificar_game_over(self):
        """Condicao de derrota: stress >= 1000."""
        return self.estado["stress"] >= 1000

    def reset_completo(self):
        """Reinicia todas as metricas e ponteiros para o estado inicial."""
        self.dia_atual = 1
        self.fluxo_atual = "inicio"
        self.historico_escolhas = []
        self.estado = {
            "indice_evento": 0,
            "rota_pendente_idx": None,
            "texto_treplica_pendente": None,
            "texto_gerente_pendente": None,
            "historico_rotas": [],
            "agente_atual": "Vagner",
            "caixa": 100,
            "tracao": 50,
            "acervo": 50,
            "stress": 0
        }
