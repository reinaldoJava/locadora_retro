import json
import os
from pathlib import Path

class Engine:
    def __init__(self, lista_cenarios=None):
        self.reset_completo()
        # Se não passar nada, carrega a ordem cronológica padrão
        if lista_cenarios is None:
            lista_cenarios = ['eventos_1999.json', 'eventos_2026.json']

        self.estado = {
            "caixa": 1000, "stress": 0, "acervo": 100, "tracao": 50,
            "indice_evento": 0,
            "historico_rotas": [],
            "rota_pendente_idx": None
        }

        self.arquivos_cenario = lista_cenarios
        self.indice_arquivo_atual = 0

        self._carregar_arquivo_atual()

    def _carregar_arquivo_atual(self):
        """Metodo auxiliar para ler o arquivo da vez e garantir que é uma lista"""
        arquivo_da_vez = self.arquivos_cenario[self.indice_arquivo_atual]
        caminho = os.path.join(Path(__file__).resolve().parent.parent, "data", arquivo_da_vez)

        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        # Garante que iteramos sobre uma lista
        self.eventos = list(dados.values()) if isinstance(dados, dict) else dados

    def obter_evento_atual(self):
            # 1. Tenta achar o próximo evento válido dentro do arquivo atual
            while self.estado["indice_evento"] < len(self.eventos):
                evt = self.eventos[self.estado["indice_evento"]]
                gatilho = evt.get("gatilho_rota")

                # Se não tem gatilho, ou se o gatilho está no nosso histórico, é este!
                if not gatilho or gatilho in self.estado["historico_rotas"]:
                    return evt

                self.estado["indice_evento"] += 1

            # 2. Se o loop acima terminou, significa que acabaram os eventos DESTE arquivo.
            # Vamos tentar carregar a próxima "Era" (ex: pular de 1999 para 2026)
            self.indice_arquivo_atual += 1

            if self.indice_arquivo_atual < len(self.arquivos_cenario):
                self._carregar_arquivo_atual()
                self.estado["indice_evento"] = 0 # Reseta o ponteiro de leitura da nova Era
                return self.obter_evento_atual()
            else:
                # Se não tem mais arquivos na lista, o jogo acabou de verdade.
                return None

    def formatar_para_frontend(self):
        """Adapter Pattern: Normaliza qualquer schema de evento para o contrato do Front-end"""
        # CIRÚRGICO: Intercepta imediatamente se houver tréplica no buffer, sem tocar nos ponteiros de arquivo
        if self.estado.get("texto_treplica_pendente"):
            return {
                "ano": 1999, # Força manter 1999 visualmente ativo
                "personagem": "Vagner",
                "texto": self.estado["texto_treplica_pendente"],
                "opcoes": ["Continuar"],
                "estado": self.estado
            }

        evt = self.obter_evento_atual()
        if not evt:
            # SE o motor mudou para o arquivo índice 1 (2026) e o ponteiro está em 0, é a virada!
            if self.indice_arquivo_atual == 1 and self.estado["indice_evento"] == 0:
                return {"virada_1999": True}
            return {"fim": True}

        # CASO 1: Estamos na etapa 2 (Réplica/Sub-opção de 1999)
        if self.estado.get("rota_pendente_idx") is not None:
            rota = evt["rotas_principais"][self.estado["rota_pendente_idx"]]
            texto = f"GERENTE:\n{rota.get('fala_gerente', '')}\n\nVAGNER:\n{rota.get('pushback_vagner', '')}"
            opcoes = [sub.get("foco", "Opção") for sub in rota.get("sub_opcoes", [])]
            return {"personagem": "Vagner", "texto": texto, "opcoes": opcoes, "estado": self.estado}

        # CASO 2: Etapa 1 (Decisões normais ou 1º nível de 1999/2026)
        texto_partes = []
        if "contexto_ia" in evt: texto_partes.append(evt["contexto_ia"])
        if "fala_narrativa" in evt: texto_partes.append(f"Narrador:\n{evt['fala_narrativa']}")
        if "discurso_gerente" in evt: texto_partes.append(f"Gerente:\n{evt['discurso_gerente']}")

        if "dialogos_iniciais" in evt:
            for d in evt["dialogos_iniciais"]:
                agente = d["agente"].replace("ID_", "")
                texto_partes.append(f"{agente}:\n{d['fala']}")

        texto_final = "\n\n".join(texto_partes)
        personagem = evt.get("agente_foco", "Sistema").replace("ID_", "")

        opcoes_txt = []
        if "rotas_principais" in evt:
            opcoes_txt = [r.get("nome", r.get("descricao", "Opção")) for r in evt["rotas_principais"]]
        elif "opcoes" in evt:
            opcoes_txt = [o.get("foco", o.get("argumento_gerente", "Opção")) for o in evt["opcoes"]]

        return {"ano": evt.get("ano", 1999), "personagem": personagem, "texto": texto_final, "opcoes": opcoes_txt, "estado": self.estado}

    def processar_escolha(self, indice_opcao):
        # PASSO CRÍTICO: Se havia uma tréplica na tela, o "Continuar" apenas limpa o buffer
        if self.estado.get("texto_treplica_pendente"):
            self.estado["texto_treplica_pendente"] = None
            self.estado["indice_evento"] += 1
            return self.estado

        evt = self.obter_evento_atual()
        if not evt: return self.estado

        # CASO 1: Processando a sub-opção (Réplica -> Tréplica)
        if self.estado.get("rota_pendente_idx") is not None:
            rota = evt["rotas_principais"][self.estado["rota_pendente_idx"]]
            sub_opcao = rota["sub_opcoes"][indice_opcao]

            self._aplicar_impacto_dinamico(sub_opcao)

            # CIRÚRGICO: Aloca a tréplica no buffer e avança o ponteiro de eventos imediatamente
            self.estado["texto_treplica_pendente"] = sub_opcao.get("resolucao_vagner", sub_opcao.get("argumento_gerente", ""))
            self.estado["rota_pendente_idx"] = None
            return self.estado

        # CASO 2: Escolha Primária (1999 Nível 1 ou 2026)
        escolha = None
        if "rotas_principais" in evt:
            escolha = evt["rotas_principais"][indice_opcao]
            if "sub_opcoes" in escolha:
                self.estado["historico_rotas"].append(escolha.get("id_rota", ""))
                self.estado["rota_pendente_idx"] = indice_opcao
                return self.estado

        elif "opcoes" in evt:
            escolha = evt["opcoes"][indice_opcao]

        if escolha:
            id_escolha = escolha.get("id_opcao", escolha.get("id_rota", ""))
            if id_escolha: self.estado["historico_rotas"].append(id_escolha)
            self._aplicar_impacto_dinamico(escolha)

        self.estado["indice_evento"] += 1
        return self.estado



    def _aplicar_impacto_dinamico(self, dict_opcao):
        """Busca o impacto não importa o nome da chave (impacto, impactos, impacto_sistema)"""
        impactos = dict_opcao.get("impacto", dict_opcao.get("impactos", dict_opcao.get("impacto_sistema", {})))
        for k, v in impactos.items():
            if isinstance(v, (int, float)) and k in self.estado:
                self.estado[k] = max(0, self.estado.get(k, 0) + v)

    def verificar_game_over(self):
        return self.estado["stress"] >= 100 or self.estado["caixa"] <= 0

    def reset_completo(self):
        # Variáveis de fluxo globais
        self.dia_atual = 1
        self.fluxo_atual = "inicio"
        self.historico_escolhas = []

        # Estado interno com controle, histórico E as métricas financeiras/sociais
        self.estado = {
            "indice_evento": 0,
            "rota_pendente_idx": None,
            "texto_treplica_pendente": None,
            "historico_rotas": [],

            # === MÉTRICAS DO JOGO ===
            # (Substitua os números abaixo pelos valores iniciais REAIS do seu jogo)
            "caixa": 100,       # Ex: Valor de dinheiro inicial no caixa
            "tracao": 50,       # Ex: Popularidade/retenção inicial
            "acervo": 50,       # Ex: Estado do catálogo de fitas
            "stress": 0         # Ex: Stress começa zerado
        }
        print(">>> MOTOR REINICIADO: Voltamos para o Dia 1")