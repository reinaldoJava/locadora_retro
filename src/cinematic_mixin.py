# src/cinematic_mixin.py
# Transicoes cinematicas animadas via maquina de estados:
#   - Transicao inicial (passos 1-3): SISTEMA CARREGADO → terminal GIF → gameplay 1999
#   - Virada 1999→2026 (passos 1-11+): fade, contagem regressiva, wormhole → prologo 2026
#
# Comunicacao com o frontend via header HX-Trigger (payload: {ui_commands: [...]}).
# Animacoes longas usam loopAutomatico (polling) ou esperarVideo (evento onended).
# Animacoes de terminal disparam CustomEvent animacao_terminal_concluida no browser.

import json
from flask import render_template, make_response, request
from src.audio_config import AUDIO_SETTINGS


class CinematicMixin:
    """Transicoes cinematicas: inicial e virada 1999-2026."""

    # ------------------------------------------------------------------ #
    # TRANSICAO INICIAL (tela sistema carregado -> gameplay 1999)         #
    # ------------------------------------------------------------------ #

    def start_game_transition(self):
        self._initial_game_transition_step = 1
        return self._orquestrar_initial_game_transition()

    def start_game_1999_sequence(self):
        self._initial_game_transition_step = 2
        return self._orquestrar_initial_game_transition()

    def handle_animacao_concluida(self):
        animacao_nome = request.form.get("animacao")

        if animacao_nome == "terminal_shutdown" and self._initial_game_transition_step == 2:
            # Terminal da intro concluido: avanca para o gameplay inicial
            self._initial_game_transition_step = 3
            return self.proximo_passo()

        if animacao_nome == "terminal_shutdown" and self.passo_cinematico == 10:
            # Terminal da virada 1999->2026 concluido: exibe o video wormhole
            return self.proximo_passo()

        return make_response("", 204)

    def _orquestrar_initial_game_transition(self):
        ui_commands = []
        response_data = ""

        if self._initial_game_transition_step == 1:
            response_data = render_template("cinematic_transition_placeholder.html")
            ui_commands.append({
                "action": "typeText",
                "args": {
                    "elementId": "system-message",
                    "fullText": "SISTEMA CARREGADO",
                    "speed": 60,
                    "typingVolume": AUDIO_SETTINGS.get("keyboard_volume", 0.15),
                    "postTypingCommand": {
                        "action": "showElementById",
                        "args": {"elementId": "btn-iniciar-sistema"}
                    }
                }
            })

        elif self._initial_game_transition_step == 2:
            response_data = render_template("cinematic_transition_animation_placeholder.html")
            ui_commands.append({
                "action": "animacaoTerminal",
                "args": {"tempo_ms": 3000, "auto_avancar": True}
            })
            cfg = AUDIO_SETTINGS["game_music_1999"]
            ui_commands.append({
                "action": "playAudio",
                "args": {
                    "id": cfg["id"], "acao": "trocar_trilha",
                    "src": cfg["src"], "volume": cfg["volume"], "loop": cfg["loop"]
                }
            })

        elif self._initial_game_transition_step == 3:
            self._initial_game_transition_step = 0
            dados_motor = self.motor.formatar_para_frontend()
            response_data = self._renderizar_gameplay(dados_motor)

        response = make_response(response_data)
        if ui_commands:
            response.headers["HX-Trigger"] = json.dumps({"ui_commands": ui_commands})
        return response

    # ------------------------------------------------------------------ #
    # VIRADA CINEMATICA 1999 -> 2026                                      #
    # ------------------------------------------------------------------ #

    def _orquestrar_virada_2026(self, dados_motor):
        self.passo_cinematico += 1
        response_data = ""
        ui_commands = []
        extra_triggers = {}

        if self.passo_cinematico == 1:
            extra_triggers["iniciar_fade_1999"] = {}
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=1,
                texto_virada="", numero_contagem_display="none",
                texto_feliz_ano_display="none", imagens_personagens_display="none"
            )
            ui_commands.append({"action": "loopAutomatico", "args": {"tempo_ms": 1500}})

        elif self.passo_cinematico == 2:
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=2,
                texto_virada="Parabéns, voce chegou ao final de 1999.<br>",
                numero_contagem_display="none", texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({"action": "loopAutomatico", "args": {"tempo_ms": 2500}})

        elif self.passo_cinematico == 3:
            texto = ("Parabéns, voce chegou ao final de 1999.<br><br>"
                     "Vai comecar a contagem regressiva para as novas aventuras "
                     "no ano 2000 que se iniciara em:")
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=3, texto_virada=texto,
                numero_contagem_display="none", texto_feliz_ano_display="none",
                imagens_personagens_display="none"
            )
            ui_commands.append({"action": "loopAutomatico", "args": {"tempo_ms": 3500}})

        elif 4 <= self.passo_cinematico <= 8:
            contador = 9 - self.passo_cinematico
            audio_src = (AUDIO_SETTINGS["countdown_bip_normal"]
                         if contador > 1 else AUDIO_SETTINGS["countdown_bip_final"])
            texto = ("Parabéns, voce chegou ao final de 1999.<br><br>"
                     "Vai comecar a contagem regressiva para as novas aventuras "
                     "no ano 2000 que se iniciara em:")
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=self.passo_cinematico,
                texto_virada=texto, numero_contagem_display="block",
                numero_contagem_valor=contador,
                texto_feliz_ano_display="none", imagens_personagens_display="none"
            )
            ui_commands.append({"action": "playAudio",
                                 "args": {"id": "som-contagem", "acao": "play_efeito",
                                          "src": audio_src}})
            ui_commands.append({"action": "loopAutomatico", "args": {"tempo_ms": 1000}})

        elif self.passo_cinematico == 9:
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=9,
                texto_virada_display="none", numero_contagem_display="none",
                texto_feliz_ano_display="block", imagens_personagens_display="flex"
            )
            ui_commands.append({"action": "loopAutomatico", "args": {"tempo_ms": 4500}})

        elif self.passo_cinematico == 10:
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=10, cena_fim_1999_display="none"
            )
            ui_commands.append({"action": "animacaoTerminal",
                                 "args": {"tempo_ms": 3000, "auto_avancar": True}})

        elif self.passo_cinematico == 11:
            response_data = render_template(
                "cinematic_1999_to_2026.html", passo=11,
                cena_fim_1999_display="none",
                container_shutdown_display="flex", video_shutdown_display="block"
            )
            ui_commands.append({"action": "esperarVideo", "args": {}})
            ui_commands.append({"action": "playVideo",
                                 "args": {"id": "video-shutdown", "acao": "play"}})

        else:
            self.passo_cinematico = 0
            self.motor.indice_arquivo_atual = 1
            self.motor.estado["indice_evento"] = 0
            self.motor._carregar_arquivo_atual()
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
