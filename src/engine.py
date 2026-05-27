# src/engine.py
# Maquina de estados narrativa: carrega eventos JSON, processa escolhas
# e calcula o estado das metricas (caixa, tracao, acervo, stress).

import json
import os
from pathlib import Path


class Engine:

    def __init__(self, lista_cenarios=None, reset_on_init=True):
        self.dia_atual = 1
        self.fluxo_atual = "inicio"
        self.historico_escolhas = []
        self.estado = {}
        self.eventos = []
        self.indice_arquivo_atual = 0

        if reset_on_init:
            self.reset_completo()
            if lista_cenarios is None:
                lista_cenarios = ['eventos_1999.json', 'eventos_2026.json']
            self.arquivos_cenario = lista_cenarios
            self._carregar_arquivo_atual()
        else:
            if lista_cenarios is None:
                lista_cenarios = ['eventos_1999.json', 'eventos_2026.json']
            self.arquivos_cenario = lista_cenarios

    def _carregar_arquivo_atual(self):
        if self.indice_arquivo_atual >= len(self.arquivos_cenario):
            self.eventos = []
            return
        arquivo = self.arquivos_cenario[self.indice_arquivo_atual]
        caminho = os.path.join(Path(__file__).resolve().parent.parent, "data", arquivo)
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        self.eventos = list(dados.values()) if isinstance(dados, dict) else dados

    def obter_evento_atual(self):
        # Crise ativa: retorna o evento de crise antes de qualquer outro
        if self.estado.get("crise_ativa_evento"):
            return self.estado["crise_ativa_evento"]

        while self.estado["indice_evento"] < len(self.eventos):
            evt = self.eventos[self.estado["indice_evento"]]
            gatilho = evt.get("gatilho_rota")
            if not gatilho or gatilho in self.estado["historico_rotas"]:
                return evt
            self.estado["indice_evento"] += 1

        self.indice_arquivo_atual += 1
        self.estado["indice_evento"] = 0
        return None

    def formatar_para_frontend(self):
        if self.estado.get("texto_gerente_pendente"):
            return {
                "ano": self.estado.get("ano_buffer", 1999),
                "personagem": "Gerente",
                "texto": self.estado["texto_gerente_pendente"],
                "opcoes": ["Continuar"],
                "estado": self.estado
            }

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
            if self.indice_arquivo_atual == 1 and self.estado["indice_evento"] == 0:
                return {"virada_1999": True}
            return {"fim": True}

        if self.estado.get("rota_pendente_idx") is not None:
            rota = evt["rotas_principais"][self.estado["rota_pendente_idx"]]
            return {
                "ano": evt.get("ano", self.estado.get("ano_buffer", 1999)),
                "personagem": self.estado.get("agente_atual", "Vagner"),
                "texto": rota.get('pushback_vagner', ''),
                "opcoes": [sub.get("foco", "Opcao") for sub in rota.get("sub_opcoes", [])],
                "estado": self.estado
            }

        if (evt.get("agente_foco") and evt.get("contexto_ia") and
                self.estado.get("_contexto_exibido_id") != evt.get("id")):
            return {
                "ano": evt.get("ano", 1999),
                "personagem": "Sistema",
                "texto": evt["contexto_ia"],
                "opcoes": ["Continuar"],
                "estado": self.estado,
            }

        texto_partes = []
        if "contexto_ia"       in evt: texto_partes.append(evt["contexto_ia"])
        if "fala_narrativa"    in evt: texto_partes.append(f"Narrador:\n{evt['fala_narrativa']}")
        if "discurso_gerente"  in evt: texto_partes.append(f"Gerente:\n{evt['discurso_gerente']}")
        if "dialogos_iniciais" in evt:
            for d in evt["dialogos_iniciais"]:
                agente = d["agente"].replace("ID_", "")
                texto_partes.append(f"{agente}:\n{d['fala']}")
        texto_final = "\n\n".join(texto_partes)

        if "agente_foco" in evt:
            personagem = evt["agente_foco"].replace("ID_", "")
        elif "discurso_gerente" in evt:
            personagem = "Gerente"
        elif "dialogos_iniciais" in evt and evt["dialogos_iniciais"]:
            personagem = evt["dialogos_iniciais"][0]["agente"].replace("ID_", "")
        else:
            personagem = "Sistema"

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
            if self.estado.get("crise_ativa_evento"):
                # Crise resolvida: nao incrementa indice_evento (evento era virtual)
                self.estado["crise_ativa_evento"] = None
                self.estado["crise_resolvida"] = True
            else:
                self.estado["indice_evento"] += 1
            return self.estado

        evt = self.obter_evento_atual()
        if not evt:
            return self.estado

        # Consumir frame de contexto_ia: eventos 1999 (agente_foco) e 2026 (dialogos_iniciais)
        if (evt.get("contexto_ia") and
                self.estado.get("_contexto_exibido_id") != evt.get("id") and
                self.estado.get("rota_pendente_idx") is None and
                ("agente_foco" in evt or "dialogos_iniciais" in evt)):
            self.estado["_contexto_exibido_id"] = evt.get("id", "")
            return self.estado

        if self.estado.get("rota_pendente_idx") is not None:
            rota_idx  = self.estado["rota_pendente_idx"]
            rota      = evt["rotas_principais"][rota_idx]
            sub_opcao = rota["sub_opcoes"][indice_opcao]
            self._aplicar_impacto_dinamico(sub_opcao)
            # Armazena resultado da crise (vitoria / game_over) se crise ativa
            if self.estado.get("crise_ativa_evento"):
                self.estado["crise_resultado"] = sub_opcao.get("resultado", "game_over")
            self.estado["texto_treplica_pendente"] = sub_opcao.get(
                "resolucao_agente", sub_opcao.get("resolucao_vagner",
                sub_opcao.get("argumento_gerente", "")))
            self.estado["temp_treplica"] = sub_opcao.get("temp_treplica")
            self.estado["pool_key_treplica"] = (
                f"{evt.get('id', '')}:treplica:{rota_idx}:{indice_opcao}"
            )
            self.estado["rota_pendente_idx"] = None
            if sub_opcao.get("argumento_gerente"):
                self.estado["texto_gerente_pendente"] = sub_opcao["argumento_gerente"]
                self.estado["llm_argumento"] = sub_opcao["argumento_gerente"]
                self.estado["ano_buffer"] = evt.get("ano", 1999)
            return self.estado

        escolha = None
        if "rotas_principais" in evt:
            escolha = evt["rotas_principais"][indice_opcao]
            if "sub_opcoes" in escolha:
                self.estado["historico_rotas"].append(escolha.get("id_rota", ""))
                self.estado["rota_pendente_idx"] = indice_opcao
                agente_foco_default = evt.get("agente_foco", "ID_Vagner").replace("ID_", "")
                pushback = escolha.get("pushback_vagner", "")
                self.estado["agente_atual"] = self._detectar_agente_pushback(pushback, agente_foco_default)
                self.estado["texto_gerente_pendente"] = escolha.get("fala_gerente", "")
                self.estado["llm_argumento"] = escolha.get("fala_gerente", "")
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
                    self.estado["llm_argumento"] = escolha["argumento_gerente"]
                if escolha.get("treplica"):
                    self.estado["texto_treplica_pendente"] = escolha["treplica"]
                    agente_foco = evt.get("agente_foco")
                    if agente_foco:
                        self.estado["agente_atual"] = agente_foco.replace("ID_", "")
                        self.estado["pool_key_treplica"] = (
                            f"{evt.get('id', '')}:treplica:{indice_opcao}"
                        )
                    else:
                        self.estado["agente_atual"] = "Sistema"
                self.estado["ano_buffer"] = evt.get("ano", 1999)
                return self.estado

        if escolha:
            id_escolha = escolha.get("id_opcao", escolha.get("id_rota", ""))
            if id_escolha:
                self.estado["historico_rotas"].append(id_escolha)
            self._aplicar_impacto_dinamico(escolha)

        self.estado["indice_evento"] += 1
        return self.estado

    def _detectar_agente_pushback(self, pushback_text, agente_foco_default):
        nomes = {"Vagner": "Vagner", "Leila": "Leila",
                 "Mauricio": "Mauricio", "Gerente": "Gerente"}
        for nome, agente in nomes.items():
            if pushback_text.startswith(f"{nome}:"):
                return agente
        return agente_foco_default

    def _aplicar_impacto_dinamico(self, dict_opcao):
        """Aplica deltas numericos multiplicados pelo fator de dificuldade."""
        impactos = dict_opcao.get("impacto",
                   dict_opcao.get("impactos",
                   dict_opcao.get("impacto_sistema", {})))
        mult = self.estado.get("dificuldade_mult", 1.0)
        for k, v in impactos.items():
            if isinstance(v, (int, float)) and k in self.estado:
                delta = round(v * mult)
                self.estado[k] = max(0, self.estado.get(k, 0) + delta)

    def verificar_game_over(self):
        """Condicao de derrota: stress >= 1000 ou game_over_forcado."""
        return (self.estado.get("stress", 0) >= 1000 or
                self.estado.get("game_over_forcado", False))

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
            "llm_argumento": "",
            "historico_rotas": [],
            "agente_atual": "Vagner",
            "caixa": 100,
            "tracao": 50,
            "acervo": 50,
            "stress": 0,
            # --- Sistema de crise e dificuldade ---
            "dificuldade_mult": 1.0,
            "dificuldade_nome": "BETA",
            "crises_usadas": [],
            "crise_ativa_evento": None,
            "crise_ativa_id": None,
            "crise_resultado": None,
            "game_over_forcado": False,
        }
