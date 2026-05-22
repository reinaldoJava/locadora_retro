# src/intro_mixin.py
# Sequencia de slides de introducao exibida em intro.html (#intro-container).
# Ao terminar o ultimo slide, emite HX-Redirect para /jogo em vez de iniciar
# a transicao cinematica diretamente (que pertence ao contexto de index.html).

import copy
import json
from flask import render_template, make_response, redirect
from src.audio_config import AUDIO_SETTINGS


class IntroMixin:
    """Sequencia de introducao do jogo (slides de intro)."""

    def iniciar_intro(self, nome_jogador):
        self.nome_jogador = nome_jogador
        self.motor.reset_completo()
        self.motor.estado["nome_jogador"] = nome_jogador
        self.roteiro_intro = copy.deepcopy(self._roteiro_intro_base)
        if self.roteiro_intro:
            self.roteiro_intro[0]["texto"] = (
                self.roteiro_intro[0]["texto"].replace("{NOME_JOGADOR}", nome_jogador)
            )
        self.slide_atual = 0
        return self._renderizar_intro_slide()

    def avancar_intro_slide(self):
        self.slide_atual += 1
        if self.slide_atual < len(self.roteiro_intro):
            return self._renderizar_intro_slide()
        # Ultimo slide concluido: redireciona para a pagina principal do jogo.
        # HX-Redirect faz o browser navegar para /jogo (pagina completa),
        # onde #ui-jogo existe e o fluxo cinematico comeca corretamente.
        response = make_response("", 204)
        response.headers["HX-Redirect"] = "/jogo"
        return response

    def _renderizar_intro_slide(self):
        if self.slide_atual >= len(self.roteiro_intro):
            return redirect("/jogo")

        slide = self.roteiro_intro[self.slide_atual]
        texto_formatado = slide["texto"].replace("{NOME_JOGADOR}", self.nome_jogador)
        ui_commands = []

        if self.slide_atual == 0:
            cfg = AUDIO_SETTINGS["intro_music"]
            ui_commands.append({
                "action": "playAudio",
                "args": {
                    "id": cfg["id"], "acao": "trocar_trilha",
                    "src": cfg["src"], "volume": cfg["volume"], "loop": cfg["loop"]
                }
            })

        ui_commands.append({
            "action": "typeText",
            "args": {"elementId": "elenco-texto", "fullText": texto_formatado, "speed": 60}
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
