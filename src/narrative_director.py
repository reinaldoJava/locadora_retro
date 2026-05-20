# src/diretor.py
import json
import copy
import logging

from flask import render_template, make_response, request, redirect # Importar redirect
import os
from pathlib import Path
from src.audio_config import AUDIO_SETTINGS # Importar as configurações de áudio

class DiretorNarrativo:
    def __init__(self, engine_instance):
        self._initial_game_transition_step = None
        self.motor = engine_instance
        self.passo_cinematico = 0
        self.nome_jogador = "Gerente"
        self.roteiro_intro = []
        self.slide_atual = 0

        caminho_arquivo = os.path.join(Path(__file__).resolve().parent.parent, "data", "intro.json")
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            self._roteiro_intro_base = json.load(f)

        caminho_salto = os.path.join(Path(__file__).resolve().parent.parent, "data", "evento_salto_temporal.json")
        with open(caminho_salto, 'r', encoding='utf-8') as f:
            self._roteiro_salto_temporal = json.load(f)

        self.passo_prologo_2026 = 0
        self.passo_encruzilhada_2026 = 0
        self.rota_escolhida_id = None

    def proximo_passo(self, escolha_usuario=None):
        """Ponto de entrada único chamado pela rota do servidor"""
        if self.motor.verificar_game_over():
            return self._renderizar_game_over()

        # Prólogo de 2026: intercepta antes de processar escolha do motor
        if self.passo_prologo_2026 > 0:
            return self._orquestrar_prologo_2026(escolha_usuario)

        # Encruzilhada de 2026: exibição sequencial (narrador → gerente → opções)
        if self.passo_encruzilhada_2026 > 0:
            return self._orquestrar_encruzilhada_2026(escolha_usuario)

        if escolha_usuario is not None:
            self.motor.processar_escolha(escolha_usuario)

        # Novo: Orquestra a transição inicial do jogo antes de qualquer outra lógica
        if hasattr(self, '_initial_game_transition_step') and self._initial_game_transition_step > 0: # Verifica se o atributo existe
            return self._orquestrar_initial_game_transition()

        dados_motor = self.motor.formatar_para_frontend()

        if dados_motor.get("virada_1999") or self.passo_cinematico > 0:
            return self._orquestrar_virada_2026(dados_motor)

        if dados_motor.get("fim"):
            return self._renderizar_fim_de_jogo()

        return self._renderizar_gameplay(dados_motor)

    def _renderizar_gameplay(self, dados):
        """Renderiza o HTML do gameplay padrão."""
        # Detecta entrada no evento_encruzilhada_2026 e inicia sequência sequential
        if dados.get("ano") == 2026 and self.passo_encruzilhada_2026 == 0:
            evt_check = self.motor.obter_evento_atual()
            if evt_check and evt_check.get("id") == "evento_encruzilhada_2026":
                self.passo_encruzilhada_2026 = 1
                return self._orquestrar_encruzilhada_2026()

        estado_barras = dados.get("estado", {})
        texto_html = ""
        evt_atual = self.motor.obter_evento_atual()

        if evt_atual and "dialogos_iniciais" in evt_atual:
            for d in evt_atual["dialogos_iniciais"]:
                agente = d["agente"].replace("ID_", "")
                texto_html += (
                    f"<p class='nome-personagem'>{agente}</p>"
                    f"<p class='fala-dialogo'>{d['fala']}</p>"
                )
        else:
            texto_html = f"<p class='fala-dialogo'>{dados['texto'].replace(chr(10), '<br>')}</p>"

        opcoes_html = ""
        for idx, opcao_txt in enumerate(dados["opcoes"]):
            opcoes_html += f"<button class='btn-opcao' hx-post='/api/interagir' hx-vals='{{\"choice\": {idx}}}' hx-target='#ui-jogo' hx-swap='innerHTML'>{opcao_txt}</button>"

        personagem_foco = dados.get("personagem", "Sistema")

        # Spotlight — define quem aparece no slot direito e se está em foco
        if personagem_foco == "Sistema":
            # Sem personagem definido: slot direito vazio
            mostra_npc = False
            npc_eh_foco = False
            img_npc_src = ""
        elif personagem_foco == "Vagner":
            # Vagner fala: Gerente aparece à direita como ouvinte (apagado)
            mostra_npc = True
            npc_eh_foco = False
            img_npc_src = "/static/img/gerente.png"
        else:
            # Outro NPC (Mauricio, Leila, Gerente…) está em destaque à direita
            mostra_npc = True
            npc_eh_foco = True
            img_npc_src = f"/static/img/{personagem_foco.lower()}.png"

        # Determina o background correto: rota A/B/C/D define o cenário em 2026
        _ROTA_BG_2026 = {"A": "bg_2026_y2k_set", "B": "bg_2026_artefatos",
                          "C": "bg_2026_detox", "D": "bg_2026_pub"}
        ano = dados.get("ano", 1999)
        if ano == 2026:
            historico = self.motor.estado.get("historico_rotas", [])
            rota = next((r for r in reversed(historico) if r in ["A", "B", "C", "D"]), None)
            bg_src = f"/static/img/{_ROTA_BG_2026.get(rota, 'bg_2026')}.png"
        else:
            bg_src = f"/static/img/bg_{ano}.png"

        return render_template(
            "game_ui.html",
            ano=ano,
            bg_src=bg_src,
            personagem_foco=personagem_foco,
            mostra_npc=mostra_npc,
            npc_eh_foco=npc_eh_foco,
            img_npc_src=img_npc_src,
            img_esq_src="/static/img/vagner.png",
            ator_esq_foco=(personagem_foco == "Vagner"),
            texto_dialogo=texto_html,
            opcoes_dialogo=opcoes_html,
            caixa=estado_barras.get("caixa", 0),
            stress=estado_barras.get("stress", 0),
            acervo=estado_barras.get("acervo", 0),
            tracao=estado_barras.get("tracao", 0)
        )

    def start_game_transition(self):
        """Inicia a sequência de transição do jogo principal, mostrando a tela 'SISTEMA CARREGADO'."""
        self._initial_game_transition_step = 1
        return self._orquestrar_initial_game_transition()

    def _orquestrar_initial_game_transition(self):
        """Orquestra a transição da tela inicial (SISTEMA CARREGADO) para o início do game 1999."""
        ui_commands = []
        response_data = ""

        if self._initial_game_transition_step == 1:
            # PASSO 1: Renderiza o placeholder para "SISTEMA CARREGADO" e espera o clique do usuário
            response_data = render_template("cinematic_transition_placeholder.html")

            # Adiciona o comando typeText para "SISTEMA CARREGADO" sem sons de tecla
            ui_commands.append({
                "action": "typeText",
                "args": {
                    "elementId": "system-message", # ID do elemento no cinematic_transition_placeholder.html
                    "fullText": "SISTEMA CARREGADO",
                    "speed": 60,
                    "playTypingSounds": False, # Desativa os sons de tecla para este texto
                    "postTypingCommand": { # NOVO: Comando para executar após a digitação
                        "action": "showElementById",
                        "args": {"elementId": "btn-iniciar-sistema"}
                    }
                }
            })
            # O _initial_game_transition_step permanece em 1, esperando o clique do botão "iniciar sistema"
            # Nenhuma animação ou música do game é iniciada aqui.
        elif self._initial_game_transition_step == 2:
            # PASSO 2: Animação do terminal e início da música do game
            response_data = render_template("cinematic_transition_animation_placeholder.html") # Um placeholder para a animação

            # Dispara a animação do terminal
            ui_commands.append({
                "action": "animacaoTerminal",
                "args": {"tempo_ms": 3000, "auto_avancar": True} # auto_avancar para chamar handle_animacao_concluida
            })

            # Inicia a música de 1999
            game_music_1999_settings = AUDIO_SETTINGS["game_music_1999"]
            ui_commands.append({
                "action": "playAudio",
                "args": {
                    "id": game_music_1999_settings["id"],
                    "acao": "trocar_trilha",
                    "src": game_music_1999_settings["src"],
                    "volume": game_music_1999_settings["volume"],
                    "loop": game_music_1999_settings["loop"]
                }
            })
            # O _initial_game_transition_step permanece em 2, esperando a conclusão da animação

        elif self._initial_game_transition_step == 3: # Agora o passo 3 é o que renderiza o gameplay
            # Animação do terminal terminou, agora renderiza o gameplay real
            self._initial_game_transition_step = 0 # Reseta o passo da transição
            dados_motor = self.motor.formatar_para_frontend()
            response_data = self._renderizar_gameplay(dados_motor)
        
        response = make_response(response_data)
        if ui_commands:
            response.headers["HX-Trigger"] = json.dumps({"ui_commands": ui_commands})
        return response

    def start_game_1999_sequence(self):
        """Inicia a sequência de animação do terminal e música do game 1999."""
        self._initial_game_transition_step = 2
        return self._orquestrar_initial_game_transition()

    def handle_animacao_concluida(self):
        """Lida com a notificação do frontend de que uma animação terminou."""
        animacao_nome = request.form.get("animacao")

        if animacao_nome == "terminal_shutdown" and self._initial_game_transition_step == 2:
            print("Backend: Animação do terminal concluída. Avançando para o gameplay.")
            self._initial_game_transition_step = 3
            return self.proximo_passo()

        # CIRÚRGICO: Trata o fim da animação do terminal durante a cinemática de virada (passo 10 → 11)
        if animacao_nome == "terminal_shutdown" and self.passo_cinematico == 10:
            print("Backend: Animação do terminal concluída (virada). Avançando para o vídeo wormhole.")
            return self.proximo_passo()

        return make_response("", 204)

    def _orquestrar_virada_2026(self, dados_motor):
        self.passo_cinematico += 1
        response_data = ""
        ui_commands = []
        extra_triggers = {}

        # PASSO 1: Esconde o jogo, mostra a tela preta e limpa textos antigos
        if self.passo_cinematico == 1:
            extra_triggers["iniciar_fade_1999"] = {}
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=1,
                texto_virada="",
                numero_contagem_display="none",
                texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({
                "action": "loopAutomatico",
                "args": {"tempo_ms": 1500}
            })

        # PASSO 2: Mostra a mensagem inicial
        elif self.passo_cinematico == 2:
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=2,
                texto_virada="Parabéns, você chegou ao final de 1999.<br>",
                numero_contagem_display="none",
                texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({
                "action": "loopAutomatico",
                "args": {"tempo_ms": 2500}
            })

        # PASSO 3: Adiciona o texto explicativo da contagem (CIRÚRGICO: Variável corrigida)
        elif self.passo_cinematico == 3:
            texto_completo = "Parabéns, você chegou ao final de 1999.<br><br>Vai começar a contagem regressiva para as novas aventuras no ano 2000 que se iniciará em:"
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=3,
                texto_virada=texto_completo,
                numero_contagem_display="none",
                texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({
                "action": "loopAutomatico",
                "args": {"tempo_ms": 3500}
            })

        # PASSO 4 a 8: Contagem Regressiva de 5 a 1 segundo a segundo
        elif 4 <= self.passo_cinematico <= 8:
            contador = 9 - self.passo_cinematico
            audio_src = AUDIO_SETTINGS["countdown_bip_normal"] if contador > 1 else AUDIO_SETTINGS["countdown_bip_final"]
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=self.passo_cinematico,
                texto_virada="Parabéns, você chegou ao final de 1999.<br><br>Vai começar a contagem regressiva para as novas aventuras no ano 2000 que se iniciará em:",
                numero_contagem_display="block",
                numero_contagem_valor=contador,
                texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({
                "action": "playAudio",
                "args": {
                    "id": "som-contagem",
                    "acao": "play_efeito",
                    "src": audio_src
                }
            })
            ui_commands.append({
                "action": "loopAutomatico",
                "args": {"tempo_ms": 1000}
            })

        # PASSO 9: FIM DA CONTAGEM - Feliz Ano Novo e Personagens
        elif self.passo_cinematico == 9:
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=9,
                texto_virada_display="none",
                numero_contagem_display="none",
                texto_feliz_ano_display="block",
                imagens_personagens_display="flex"
            )
            ui_commands.append({
                "action": "loopAutomatico",
                "args": {"tempo_ms": 4500}
            })

        # PASSO 10: Dispara o Efeito do Terminal
        elif self.passo_cinematico == 10:
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=10,
                cena_fim_1999_display="none"
            )
            ui_commands.append({
                "action": "animacaoTerminal",
                "args": {"tempo_ms": 3000, "auto_avancar": True}
            })

        # PASSO 11: Execução do Vídeo Wormhole
        elif self.passo_cinematico == 11:
            response_data = render_template(
                "cinematic_1999_to_2026.html",
                passo=11,
                cena_fim_1999_display="none",
                container_shutdown_display="flex",
                video_shutdown_display="block"
            )
            ui_commands.append({
                "action": "esperarVideo",
                "args": {}
            })
            ui_commands.append({
                "action": "playVideo",
                "args": {"id": "video-shutdown", "acao": "play"}
            })

        # PASSO 12: FIM DA CINEMÁTICA - Inicia o Prólogo de 2026
        else:
            self.passo_cinematico = 0
            self.motor.indice_arquivo_atual = 1
            self.motor.estado["indice_evento"] = 0
            self.motor._carregar_arquivo_atual()

            # Delega ao prólogo antes de entrar no gameplay normal
            self.passo_prologo_2026 = 0
            return self._orquestrar_prologo_2026()

        response = make_response(response_data)
        triggers = {}
        if ui_commands:
            triggers["ui_commands"] = ui_commands
        triggers.update(extra_triggers)
        if triggers:
            response.headers["HX-Trigger"] = json.dumps(triggers)
        return response

    # ------------------------------------------------------------------
    # ENCRUZILHADA DE 2026 — exibição sequencial
    # ------------------------------------------------------------------

    def _orquestrar_encruzilhada_2026(self, escolha_usuario=None):
        """Exibe evento_encruzilhada_2026 em dois passos:
        Passo 1: Narrador (fala_narrativa) + [Continuar]
        Passo 2: Gerente (discurso_gerente) + 4 opções de rota
        Passo 3+: processa a rota escolhida e entra no gameplay normal.
        bg_2026.png é mantido durante todo o evento.
        """
        evt = self.motor.obter_evento_atual()
        est = self.motor.estado

        btn_continuar = ("<button class='btn-opcao' hx-post='/api/interagir' "
                         "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>")

        def _render(texto_html, opcoes_html, personagem="Sistema",
                    npc=False, npc_foco=False, npc_img="", vagner_foco=False):
            return make_response(render_template(
                "game_ui.html",
                ano=2026, bg_src="/static/img/bg_2026.png",
                personagem_foco=personagem,
                mostra_npc=npc, npc_eh_foco=npc_foco, img_npc_src=npc_img,
                img_esq_src="/static/img/vagner.png", ator_esq_foco=vagner_foco,
                texto_dialogo=texto_html, opcoes_dialogo=opcoes_html,
                caixa=est.get("caixa", 0), stress=est.get("stress", 0),
                acervo=est.get("acervo", 0), tracao=est.get("tracao", 0)
            ))

        # PASSO 1 — Narrador
        if self.passo_encruzilhada_2026 == 1:
            texto = f"<p class='texto-narrador'><em>{evt['fala_narrativa']}</em></p>"
            self.passo_encruzilhada_2026 = 2
            return _render(texto, btn_continuar)

        # PASSO 2 — Discurso do Gerente + as 4 opções de rota
        elif self.passo_encruzilhada_2026 == 2:
            texto = (f"<p class='nome-personagem'>Gerente</p>"
                     f"<p class='fala-dialogo'>{evt['discurso_gerente']}</p>")
            opcoes_html = "".join(
                f"<button class='btn-opcao' hx-post='/api/interagir' "
                f"hx-vals='{{\"choice\": {idx}}}' "
                f"hx-target='#ui-jogo' hx-swap='innerHTML'>{rota['nome']}</button>"
                for idx, rota in enumerate(evt["rotas_principais"])
            )
            self.passo_encruzilhada_2026 = 3
            return _render(texto, opcoes_html,
                           personagem="Gerente", npc=True, npc_foco=True,
                           npc_img="/static/img/gerente.png")

        # PASSO 3+ — rota escolhida: delega ao motor e entra no gameplay
        else:
            self.passo_encruzilhada_2026 = 0
            self.motor.processar_escolha(escolha_usuario)
            dados_novos = self.motor.formatar_para_frontend()
            return make_response(self._renderizar_gameplay(dados_novos))

    # ------------------------------------------------------------------
    # HELPERS DO PRÓLOGO DE 2026
    # ------------------------------------------------------------------

    def _render_prologo_slide(self, texto_html, opcoes_html,
                               vagner_visivel=False, vagner_foco=False,
                               npc_visivel=False, npc_foco=False, npc_img="",
                               img_esq_src=None, ator_esq_foco=None):
        """Renderiza um slide do prólogo usando o template game_ui com ano=2026.
        img_esq_src / ator_esq_foco permitem substituir Vagner no slot esquerdo.
        """
        if not vagner_visivel:
            personagem_foco = "Sistema"
        elif vagner_foco:
            personagem_foco = "Vagner"
        else:
            personagem_foco = "Outro"  # visível mas inativo

        # Slot esquerdo: usa Vagner como padrão, mas aceita outro personagem
        _img_esq = img_esq_src if img_esq_src is not None else "/static/img/vagner.png"
        _ator_esq_foco = ator_esq_foco if ator_esq_foco is not None else vagner_foco

        return render_template(
            "game_ui.html",
            ano=2026,
            bg_src="/static/img/bg_2026.png",
            personagem_foco=personagem_foco,
            mostra_npc=npc_visivel,
            npc_eh_foco=npc_foco,
            img_npc_src=npc_img,
            img_esq_src=_img_esq,
            ator_esq_foco=_ator_esq_foco,
            texto_dialogo=texto_html,
            opcoes_dialogo=opcoes_html,
            caixa=self.motor.estado.get("caixa", 0),
            stress=self.motor.estado.get("stress", 0),
            acervo=self.motor.estado.get("acervo", 0),
            tracao=self.motor.estado.get("tracao", 0)
        )

    def _formatar_dialogo(self, dialogo):
        """Formata um dict de diálogo como HTML com nome acima da fala."""
        agente = dialogo["agente"].replace("ID_", "")
        return (
            f"<p class='nome-personagem'>{agente}</p>"
            f"<p class='fala-dialogo'>{dialogo['fala']}</p>"
        )

    def _orquestrar_prologo_2026(self, escolha_usuario=None):
        """
        Máquina de estados do prólogo de 2026 (evento_salto_temporal.json).
        Passos 1-13: slides narrativos com botão Avançar.
        Passo 14:    escolha de rota (4 botões); aguarda escolha.
        Passo 15:    argumento do Gerente para a rota escolhida.
        Passo 16+:   entra no gameplay normal de 2026.
        """
        evento = self._roteiro_salto_temporal[0]
        cenas = evento["cenas_narrativas"]
        sub_opcoes = evento["sub_opcoes"]
        ui_commands = []

        btn_avancar = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Avançar</button>"
        )

        # ── Gerencia transição de estado ──────────────────────────────
        # Avanço simples: passos 14+ entram direto no gameplay de 2026
        self.passo_prologo_2026 += 1

        print(f">>> Prólogo 2026: passo {self.passo_prologo_2026}")

        # ── Renderização por passo ────────────────────────────────────

        # PASSO 1 ── Cena 1: narração (sem personagens)
        if self.passo_prologo_2026 == 1:
            texto = f"<p class='texto-narrador'><em>{cenas[0]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(texto, btn_avancar)
            # Inicia a trilha de 2026
            cfg = AUDIO_SETTINGS["game_music_2026"]
            ui_commands.append({"action": "playAudio", "args": {
                "id": cfg["id"], "acao": "trocar_trilha",
                "src": cfg["src"], "volume": cfg["volume"], "loop": cfg.get("loop", True)
            }})

        # PASSO 2 ── Cena 2: narração da entrada do visitante (só Jovem GenZ à direita)
        elif self.passo_prologo_2026 == 2:
            texto = f"<p class='texto-narrador'><em>{cenas[1]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=False,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.png"
            )

        # PASSO 3 ── Cena 2 diálogo: Leila (foco à esquerda, Jovem GenZ à direita inativo)
        elif self.passo_prologo_2026 == 3:
            texto = self._formatar_dialogo(cenas[1]["dialogos"][0])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.png",
                img_esq_src="/static/img/leila.png", ator_esq_foco=True
            )

        # PASSO 4 ── Cena 2 diálogo: Jovem GenZ (foco à direita, Leila à esquerda inativa)
        elif self.passo_prologo_2026 == 4:
            texto = self._formatar_dialogo(cenas[1]["dialogos"][1])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/jovem_genZ.png",
                img_esq_src="/static/img/leila.png", ator_esq_foco=False
            )

        # PASSO 5 ── Cena 2 diálogo: Leila 2ª fala (foco à esquerda)
        elif self.passo_prologo_2026 == 5:
            texto = self._formatar_dialogo(cenas[1]["dialogos"][2])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.png",
                img_esq_src="/static/img/leila.png", ator_esq_foco=True
            )

        # PASSO 6 ── Cena 2 diálogo: Maurício (foco à esquerda)
        elif self.passo_prologo_2026 == 6:
            texto = self._formatar_dialogo(cenas[1]["dialogos"][3])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.png",
                img_esq_src="/static/img/mauricio.png", ator_esq_foco=True
            )

        # PASSO 7 ── Cena 2 diálogo: Jovem GenZ 2ª fala (foco à direita, Maurício inativo)
        elif self.passo_prologo_2026 == 7:
            texto = self._formatar_dialogo(cenas[1]["dialogos"][4])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/jovem_genZ.png",
                img_esq_src="/static/img/mauricio.png", ator_esq_foco=False
            )

        # PASSO 8 ── Cena 3: Vagner (foco)
        elif self.passo_prologo_2026 == 8:
            texto = self._formatar_dialogo(cenas[2]["dialogos"][0])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True, vagner_foco=True,
                npc_visivel=True, npc_img="/static/img/gerente.png"
            )

        # PASSO 9 ── Cena 3: Maurício (foco)
        elif self.passo_prologo_2026 == 9:
            texto = self._formatar_dialogo(cenas[2]["dialogos"][1])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/mauricio.png"
            )

        # PASSO 10 ── Cena 3: Gerente (foco)
        elif self.passo_prologo_2026 == 10:
            texto = self._formatar_dialogo(cenas[2]["dialogos"][2])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/gerente.png"
            )

        # PASSO 11 ── Cena 3: Leila (foco, quebra a 4ª parede)
        elif self.passo_prologo_2026 == 11:
            texto = self._formatar_dialogo(cenas[2]["dialogos"][3])
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/leila.png"
            )

        # PASSO 12 ── Cena 4: narração da sala de guerra (sem personagens)
        elif self.passo_prologo_2026 == 12:
            texto = f"<p class='texto-narrador'><em>{cenas[3]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(texto, btn_avancar)

        # PASSO 13 ── Cena 4: Vagner faz a pergunta decisiva
        elif self.passo_prologo_2026 == 13:
            texto = (
                f"<p class='nome-personagem'>Vagner</p>"
                f"<p class='fala-dialogo'>{cenas[3]['fala_agente']}</p>"
            )
            response_data = self._render_prologo_slide(
                texto, btn_avancar,
                vagner_visivel=True, vagner_foco=True,
                npc_visivel=True, npc_img="/static/img/gerente.png"
            )

        # PASSO 14+ ── Entra no gameplay normal de 2026
        # (as rotas são escolhidas pelo evento_encruzilhada_2026 do próprio JSON)
        else:
            self.passo_prologo_2026 = 0
            dados_novos = self.motor.formatar_para_frontend()
            response_data = self._renderizar_gameplay(dados_novos)

        response = make_response(response_data)
        if ui_commands:
            response.headers["HX-Trigger"] = json.dumps({"ui_commands": ui_commands})
        return response

    def _renderizar_game_over(self):
        return render_template(
            "game_over.html",
            game_over_text="<h2>SISTEMA CORROMPIDO: GAME OVER</h2><p>As métricas da locadora colapsaram.</p>"
        )

    def _renderizar_fim_de_jogo(self):
        return render_template(
            "fim_de_jogo.html",
            fim_de_jogo_text="<h2>FIM DE JOGO</h2><p>Você chegou ao final da jornada!</p>"
        )

    def iniciar_intro(self, nome_jogador):
        self.nome_jogador = nome_jogador
        self.motor.reset_completo()
        self.motor.estado["nome_jogador"] = nome_jogador

        # CIRÚRGICO: deepcopy para não corromper o cache imutável da memória interna
        self.roteiro_intro = copy.deepcopy(self._roteiro_intro_base)
        if self.roteiro_intro:
            self.roteiro_intro[0]["texto"] = self.roteiro_intro[0]["texto"].replace("{NOME_JOGADOR}", nome_jogador)

        self.slide_atual = 0
        return self._renderizar_intro_slide()

    def avancar_intro_slide(self):
        self.slide_atual += 1
        if self.slide_atual < len(self.roteiro_intro):
            return self._renderizar_intro_slide()
        else:
            # NOVO: Inicia a transição do jogo principal em vez de redirecionar diretamente
            return self.start_game_transition()

    def _renderizar_intro_slide(self):
        if self.slide_atual >= len(self.roteiro_intro):
            # Isso não deve ser mais alcançado diretamente, pois avancar_intro_slide agora chama start_game_transition
            # No entanto, como fallback, ainda redireciona.
            return redirect('/jogo')

        slide = self.roteiro_intro[self.slide_atual]
        slide_texto_original = slide["texto"]
        slide_texto_formatado = slide_texto_original.replace("{NOME_JOGADOR}", self.nome_jogador)

        ui_commands = []
        if self.slide_atual == 0:
            intro_music_settings = AUDIO_SETTINGS["intro_music"]
            ui_commands.append({
                "action": "playAudio",
                "args": {
                    "id": intro_music_settings["id"],
                    "acao": "trocar_trilha",
                    "src": intro_music_settings["src"],
                    "volume": intro_music_settings["volume"],
                    "loop": intro_music_settings["loop"]
                }
            })

        ui_commands.append({
            "action": "typeText",
            "args": {
                "elementId": "elenco-texto",
                "fullText": slide_texto_formatado,
                "speed": 60
            }
        })

        response = make_response(render_template(
            "intro_slide.html",
            imagem=slide["imagem"],
            titulo=slide["titulo"],
            texto="",
            is_last_slide=(self.slide_atual == len(self.roteiro_intro) - 1)
        ))

        if ui_commands:
            response.headers["HX-Trigger"] = json.dumps({"ui_commands": ui_commands})
        return response