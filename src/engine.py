# src/engine.py
# Maquina de estados narrativa: carrega eventos JSON, processa escolhas
# e calcula o estado das metricas (caixa, tracao, acervo, stress).

import json
import os
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Blueprint cache — carrega cada JSON de missão uma única vez por processo.
# Se CONTENT_BASE_URL estiver definida (ex.: GitHub Raw), busca via HTTP.
# Caso contrário lê do disco local (desenvolvimento).
# ---------------------------------------------------------------------------
_BLUEPRINT_CACHE: dict[str, list] = {}
_CONTENT_BASE_URL = os.environ.get("CONTENT_BASE_URL", "").rstrip("/")


def _load_blueprint(filename: str) -> list:
    """Retorna a lista de eventos do arquivo JSON, usando cache em memória.

    Produção : define CONTENT_BASE_URL=https://raw.githubusercontent.com/USER/REPO/BRANCH/data
    Dev local: deixa CONTENT_BASE_URL vazio — lê direto do disco.
    """
    if filename not in _BLUEPRINT_CACHE:
        if _CONTENT_BASE_URL:
            url = f"{_CONTENT_BASE_URL}/{filename}"
            with urllib.request.urlopen(url) as resp:
                dados = json.loads(resp.read())
        else:
            caminho = os.path.join(Path(__file__).resolve().parent.parent, "data", filename)
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
        _BLUEPRINT_CACHE[filename] = list(dados.values()) if isinstance(dados, dict) else dados
    return _BLUEPRINT_CACHE[filename]


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
        self.eventos = _load_blueprint(arquivo)

    def obter_evento_atual(self):
        # Crise ativa: retorna o evento de crise antes de qualquer outro
        if self.estado.get("crise_ativa_evento"):
            return self.estado["crise_ativa_evento"]

        while self.estado["indice_evento"] < len(self.eventos):
            evt = self.eventos[self.estado["indice_evento"]]
            pula_flag = evt.get("pula_se_flag")
            if pula_flag and self.estado.get("flags", {}).get(pula_flag):
                self.estado["indice_evento"] += 1
                continue
            mostra_flag = evt.get("mostra_se_flag")
            if mostra_flag:
                negado = mostra_flag.startswith("!")
                chave = mostra_flag[1:] if negado else mostra_flag
                flag_ativa = bool(self.estado.get("flags", {}).get(chave))
                if negado and flag_ativa or not negado and not flag_ativa:
                    self.estado["indice_evento"] += 1
                    continue
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
                agente_id_efetivo = self._resolver_agente(d["agente"])
                agente = agente_id_efetivo.replace("ID_", "")
                texto_partes.append(f"{agente}:\n{d['fala']}")
        texto_final = "\n\n".join(texto_partes)

        # Injeta memória narrativa: se alguma flag ativa possui memo neste evento,
        # prepend o lembrete para contextualizar a decisão atual.
        memos_ativos = []
        for flag, memo in evt.get("memo_se_flags", {}).items():
            if self.estado.get("flags", {}).get(flag):
                memos_ativos.append(f"[Memória] {memo}")
        if memos_ativos:
            texto_final = "\n".join(memos_ativos) + "\n\n" + texto_final

        if "agente_foco" in evt:
            personagem = self._resolver_agente(evt["agente_foco"]).replace("ID_", "")
        elif "discurso_gerente" in evt:
            personagem = "Gerente"
        elif "dialogos_iniciais" in evt and evt["dialogos_iniciais"]:
            personagem = evt["dialogos_iniciais"][0]["agente"].replace("ID_", "")
        else:
            personagem = "Sistema"

        if "rotas_principais" in evt:
            opcoes_txt = [r.get("nome", r.get("descricao", "Opcao")) for r in evt["rotas_principais"]]
        else:
            opcoes_txt = []

        return {
            "ano": evt.get("ano", 1999),
            "personagem": personagem,
            "agente_id_efetivo": self._resolver_agente(evt.get("agente_foco", "ID_Vagner")),
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

        if "rotas_principais" in evt:
            escolha = evt["rotas_principais"][indice_opcao]
            if "sub_opcoes" in escolha:
                # Rota com negociacao em dois niveis (1999)
                self.estado["historico_rotas"].append(escolha.get("id_rota", ""))
                self.estado["rota_pendente_idx"] = indice_opcao
                agente_foco_default = self._resolver_agente(
                    evt.get("agente_foco", "ID_Vagner")).replace("ID_", "")
                pushback = escolha.get("pushback_vagner", "")
                self.estado["agente_atual"] = self._detectar_agente_pushback(pushback, agente_foco_default)
                self.estado["texto_gerente_pendente"] = escolha.get("fala_gerente", "")
                self.estado["llm_argumento"] = escolha.get("fala_gerente", "")
                return self.estado
            # Rota simples (sem sub_opcoes): aplica impacto e abre dialogo LLM
            id_rota = escolha.get("id_rota", "")
            if id_rota:
                self.estado["historico_rotas"].append(id_rota)
            self._aplicar_impacto_dinamico(escolha)
            if escolha.get("fala_gerente"):
                agente_foco_default = self._resolver_agente(
                    evt.get("agente_foco", "ID_Vagner")).replace("ID_", "")
                self.estado["agente_atual"] = agente_foco_default
                self.estado["texto_gerente_pendente"] = escolha["fala_gerente"]
                self.estado["llm_argumento"] = escolha["fala_gerente"]
                self.estado["ano_buffer"] = evt.get("ano", 2026)
                self.estado["texto_treplica_pendente"] = "_pending_"
                self.estado["pool_key_treplica"] = (
                    f"{evt.get('id', '')}:treplica:{indice_opcao}"
                )
                self.estado["temp_treplica"] = escolha.get("temp_replica", 0.4)
            else:
                self.estado["indice_evento"] += 1
            return self.estado

        self.estado["indice_evento"] += 1
        return self.estado

    def _resolver_agente(self, agente_id: str) -> str:
        """Resolve IDs dinâmicos de agente conforme flags narrativas.

        ID_Curador  → ID_Mauricio (padrão) ou ID_Marcos (após mauricio_saiu)
        ID_Mauricio → ID_Marcos quando mauricio_saiu está ativa
        """
        mauricio_saiu = self.estado.get("flags", {}).get("mauricio_saiu")
        if agente_id == "ID_Curador":
            return "ID_Marcos" if mauricio_saiu else "ID_Mauricio"
        if agente_id == "ID_Mauricio" and mauricio_saiu:
            return "ID_Marcos"
        return agente_id

    def _detectar_agente_pushback(self, pushback_text, agente_foco_default):
        nomes = {"Vagner": "Vagner", "Leila": "Leila",
                 "Mauricio": "Mauricio", "Gerente": "Gerente"}
        for nome, agente in nomes.items():
            if pushback_text.startswith(f"{nome}:"):
                return agente
        return agente_foco_default

    # Métricas onde um delta POSITIVO prejudica o jogador (ao contrário das demais).
    _METRICAS_INVERSAS = {"stress"}

    def _aplicar_impacto_dinamico(self, dict_opcao):
        """Aplica deltas numericos multiplicados pelo fator de dificuldade.

        Deltas prejudiciais ao jogador são adicionalmente amplificados pelo
        fator de pressão dinâmica (self.estado['pressao']), que sobe quando
        todas as métricas estão confortáveis e cai quando o jogador está em apuros.
        """
        impactos = dict_opcao.get("impacto",
                   dict_opcao.get("impactos",
                   dict_opcao.get("impacto_sistema", {})))
        mult    = self.estado.get("dificuldade_mult", 1.0)
        pressao = self.estado.get("pressao", 1.0)
        for k, v in impactos.items():
            if isinstance(v, (int, float)) and k in self.estado:
                ruim = (k in self._METRICAS_INVERSAS and v > 0) or \
                       (k not in self._METRICAS_INVERSAS and v < 0)
                fator = mult * pressao if ruim else mult
                delta = round(v * fator)
                self.estado[k] = max(0, self.estado.get(k, 0) + delta)
        # Escreve flags de memória narrativa persistente
        for flag, valor in dict_opcao.get("escreve_flags", {}).items():
            self.estado.setdefault("flags", {})[flag] = valor
        # Recalcula pressão após cada impacto real
        self._atualizar_pressao()

    def _atualizar_pressao(self):
        """Recalcula o fator de pressão dinâmica após cada decisão.

        Lógica:
          5 métricas confortáveis → pressão +0.1 (max 2.0): más decisões pesam mais.
          ≤ 2 métricas seguras   → pressão -0.1 (min 1.0): jogo alivia ligeiramente.
          3–4 métricas seguras   → pressão mantida.

        Zonas de conforto:
          caixa ≥ 60 | tração ≥ 30 | acervo ≥ 30 | stress ≤ 60 | moral ≥ 40
        """
        est = self.estado
        seguras = sum([
            est.get("caixa", 0)         >= 60,
            est.get("tracao", 0)        >= 30,
            est.get("acervo", 0)        >= 30,
            est.get("stress", 0)        <= 60,
            est.get("moral_equipe", 0)  >= 40,
        ])
        p = est.get("pressao", 1.0)
        if seguras == 5:
            p = min(2.0, round(p + 0.1, 1))
        elif seguras <= 2:
            p = max(1.0, round(p - 0.1, 1))
        est["pressao"] = p

    def calcular_perfil(self) -> dict:
        """Classifica o perfil de gestão do jogador com base no estado final.

        Retorna dict consumido pela tela de fim de jogo para gerar o assessment via LLM:
          tipo      — arquétipo principal (Executor / Coach / Diplomata / Guerreiro / Curador / Estrategista)
          dominante — métrica mais maximizada (caixa / tração / acervo)
          risco     — alto / médio / baixo
          resumo    — frase descritiva para o prompt do LLM
          nota      — observação especial (ex: Maurício saiu)
          metricas_finais — snapshot das 5 métricas para exibição
        """
        est    = self.estado
        caixa  = est.get("caixa",        100)
        tracao = est.get("tracao",        50)
        acervo = est.get("acervo",        50)
        stress = est.get("stress",         0)
        moral  = est.get("moral_equipe",  70)

        g_caixa  = caixa  - 100   # ganho líquido vs. inicial
        g_tracao = tracao - 50
        g_acervo = acervo - 50
        p_moral  = 70 - moral     # perda de moral (positivo = piorou)

        dominante = max(
            {"caixa": g_caixa, "tração": g_tracao, "acervo": g_acervo},
            key=lambda k: {"caixa": g_caixa, "tração": g_tracao, "acervo": g_acervo}[k]
        )

        if stress >= 80 or caixa <= 20:
            risco = "alto"
        elif stress >= 40 or caixa <= 50:
            risco = "médio"
        else:
            risco = "baixo"

        mauricio_saiu = est.get("flags", {}).get("mauricio_saiu", False)

        if g_caixa > 30 and p_moral > 20:
            tipo   = "Executor"
            resumo = "Priorizou resultados financeiros de forma sistemática, mesmo com custo para a equipe."
        elif p_moral < 0 and g_tracao > 20:   # moral MELHOROU
            tipo   = "Coach"
            resumo = "Investiu em pessoas e relacionamento, apostando que engajamento gera resultado."
        elif g_tracao > 40 and stress < 40:
            tipo   = "Diplomata"
            resumo = "Navegou conflitos com habilidade, priorizando tração sem gerar desgaste excessivo."
        elif stress >= 60 and g_caixa > 0:
            tipo   = "Guerreiro"
            resumo = "Apostou em decisões de alto risco, pagando o custo no desgaste operacional."
        elif g_acervo > 30 and g_caixa < 0:
            tipo   = "Curador"
            resumo = "Priorizou qualidade do acervo em detrimento do caixa — visão de longo prazo."
        else:
            tipo   = "Estrategista"
            resumo = "Manteve equilíbrio entre as métricas sem comprometer nenhum eixo crítico."

        nota = ("Tomou a decisão mais impactante do jogo: deixou o curador ir embora."
                if mauricio_saiu else "")

        return {
            "tipo":      tipo,
            "dominante": dominante,
            "risco":     risco,
            "resumo":    resumo,
            "nota":      nota,
            "metricas_finais": {
                "caixa": caixa, "tracao": tracao, "acervo": acervo,
                "stress": stress, "moral": moral,
            },
        }

    def verificar_game_over(self):
        """Condicao de derrota: stress >= 150 ou game_over_forcado."""
        return (self.estado.get("stress", 0) >= 150 or
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
            "moral_equipe": 70,
            # --- Sistema de crise e dificuldade ---
            "dificuldade_mult": 1.0,
            "dificuldade_nome": "BETA",
            "crises_usadas": [],
            "crise_ativa_evento": None,
            "crise_ativa_id": None,
            "crise_resultado": None,
            "game_over_forcado": False,
            "_crise_alerta_pendente": False,
            "_crise_alerta_exibida": False,
            # --- Sistema de memória narrativa ---
            "flags": {},
            # --- Balanceamento dinâmico ---
            "pressao": 1.0,   # amplificador de deltas negativos; sobe quando confortável
        }
