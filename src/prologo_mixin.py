# src/prologo_mixin.py
# Sequencias narrativas do arco 2026: prologo (13 passos), encruzilhada de rotas
# e orquestracao de dialogos iniciais de eventos.
#
# Estado relevante em DiretorNarrativo:
#   passo_prologo_2026      — cursor de 1-13 para o prologo (evento_salto_temporal.json)
#   passo_encruzilhada_2026 — cursor de 1-3 para a escolha de rota (A/B/C/D)
#   rota_escolhida_id       — letra da rota selecionada na encruzilhada
#   _passo_dialogo_evento   — cursor para exibicao sequencial de dialogos_iniciais

import json
from flask import render_template, make_response, session as flask_session
from src.audio_config import AUDIO_SETTINGS
from src.utils import formatar_dialogo


class PrologoMixin:
    """Prologo 2026, encruzilhada e sequenciamento de dialogos."""

    # ------------------------------------------------------------------ #
    # ENCRUZILHADA DE 2026                                                #
    # ------------------------------------------------------------------ #

    def _orquestrar_encruzilhada_2026(self, escolha_usuario=None):
        evt = self.motor.obter_evento_atual()
        est = self.motor.estado

        btn_continuar = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>"
        )

        # Passo 1: Narrador
        if self.passo_encruzilhada_2026 == 1:
            texto = f"<p class='texto-narrador'><em>{evt['fala_narrativa']}</em></p>"
            self.passo_encruzilhada_2026 = 2
            spotlight = dict(personagem_foco="Sistema",
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                             mostra_npc=False, npc_eh_foco=False, img_npc_src="")
            return make_response(self._render_game_ui(
                texto, btn_continuar, spotlight, ano=2026,
                bg_src="/static/img/bg_2026.webp", estado=est))

        # Passo 2: Discurso do Gerente + 4 opcoes
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
            spotlight = dict(personagem_foco="Gerente",
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                             mostra_npc=True, npc_eh_foco=True,
                             img_npc_src="/static/img/gerente.webp")
            return make_response(self._render_game_ui(
                texto, opcoes_html, spotlight, ano=2026,
                bg_src="/static/img/bg_2026.webp", estado=est))

        # Passo 3+: rota escolhida
        else:
            self.passo_encruzilhada_2026 = 0
            _ROTA_LETRA = {0: "A", 1: "B", 2: "C", 3: "D"}
            letra = _ROTA_LETRA.get(escolha_usuario, "A")
            self.rota_escolhida_id = letra
            self.motor.processar_escolha(escolha_usuario)
            self.motor.arquivos_cenario[1] = f"evento_2026_gatilho_rota_{letra}.json"
            self.motor.indice_arquivo_atual = 1
            self.motor.estado["indice_evento"] = 0
            self.motor._carregar_arquivo_atual()
            dados_novos = self.motor.formatar_para_frontend()
            return make_response(self._renderizar_gameplay(dados_novos))

    # ------------------------------------------------------------------ #
    # PROLOGO DE 2026 (evento_salto_temporal.json)                        #
    # ------------------------------------------------------------------ #

    def _orquestrar_prologo_2026(self, escolha_usuario=None):
        evento = self._roteiro_salto_temporal[0]
        cenas = evento["cenas_narrativas"]
        ui_commands = []

        btn_avancar = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Avancar</button>"
        )

        self.passo_prologo_2026 += 1

        if self.passo_prologo_2026 == 1:
            texto = f"<p class='texto-narrador'><em>{cenas[0]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(texto, btn_avancar)
            cfg = AUDIO_SETTINGS["game_music_2026"]
            ui_commands.append({"action": "playAudio", "args": {
                "id": cfg["id"], "acao": "trocar_trilha",
                "src": cfg["src"], "volume": cfg["volume"],
                "loop": cfg.get("loop", True)
            }})

        elif self.passo_prologo_2026 == 2:
            texto = f"<p class='texto-narrador'><em>{cenas[1]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(
                texto, btn_avancar, npc_visivel=True,
                npc_img="/static/img/jovem_genZ.webp")

        elif self.passo_prologo_2026 == 3:
            texto = formatar_dialogo(cenas[1]["dialogos"][0])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.webp",
                img_esq_src="/static/img/leila.webp", ator_esq_foco=True)

        elif self.passo_prologo_2026 == 4:
            texto = formatar_dialogo(cenas[1]["dialogos"][1])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/jovem_genZ.webp",
                img_esq_src="/static/img/leila.webp", ator_esq_foco=False)

        elif self.passo_prologo_2026 == 5:
            texto = formatar_dialogo(cenas[1]["dialogos"][2])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.webp",
                img_esq_src="/static/img/leila.webp", ator_esq_foco=True)

        elif self.passo_prologo_2026 == 6:
            texto = formatar_dialogo(cenas[1]["dialogos"][3])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_img="/static/img/jovem_genZ.webp",
                img_esq_src="/static/img/mauricio.webp", ator_esq_foco=True)

        elif self.passo_prologo_2026 == 7:
            texto = formatar_dialogo(cenas[1]["dialogos"][4])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/jovem_genZ.webp",
                img_esq_src="/static/img/mauricio.webp", ator_esq_foco=False)

        elif self.passo_prologo_2026 == 8:
            texto = formatar_dialogo(cenas[2]["dialogos"][0])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True, vagner_foco=True,
                npc_visivel=True, npc_img="/static/img/gerente.webp")

        elif self.passo_prologo_2026 == 9:
            texto = formatar_dialogo(cenas[2]["dialogos"][1])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/mauricio.webp")

        elif self.passo_prologo_2026 == 10:
            texto = formatar_dialogo(cenas[2]["dialogos"][2])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/gerente.webp")

        elif self.passo_prologo_2026 == 11:
            texto = formatar_dialogo(cenas[2]["dialogos"][3])
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True,
                npc_visivel=True, npc_foco=True, npc_img="/static/img/leila.webp")

        elif self.passo_prologo_2026 == 12:
            texto = f"<p class='texto-narrador'><em>{cenas[3]['narracao']}</em></p>"
            response_data = self._render_prologo_slide(texto, btn_avancar)

        elif self.passo_prologo_2026 == 13:
            texto = (f"<p class='nome-personagem'>Vagner</p>"
                     f"<p class='fala-dialogo'>{cenas[3]['fala_agente']}</p>")
            response_data = self._render_prologo_slide(
                texto, btn_avancar, vagner_visivel=True, vagner_foco=True,
                npc_visivel=True, npc_img="/static/img/gerente.webp")

        else:
            self.passo_prologo_2026 = 0
            dados_novos = self.motor.formatar_para_frontend()
            response_data = self._renderizar_gameplay(dados_novos)

        response = make_response(response_data)
        if ui_commands:
            response.headers["HX-Trigger"] = json.dumps({"ui_commands": ui_commands})
        return response
