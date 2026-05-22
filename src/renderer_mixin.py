# src/renderer_mixin.py
# Camada de renderizacao: converte estado do Engine em HTML para o frontend.
# Todos os metodos retornam strings HTML ou objetos Response Flask.
#
# _render_game_ui()       — unico ponto de chamada a render_template(game_ui.html)
# _renderizar_gameplay()  — frame padrao: detecta spotlight, monta texto e opcoes
# _orquestrar_dialogo_evento() — exibe dialogos_iniciais um por vez antes das opcoes
# _render_prologo_slide() — slide do prologo 2026 (compartilhado com PrologoMixin)

from flask import render_template, make_response, session as flask_session
from src.Maps import ROTA_BG_2026, IMG_PERSONS


class RendererMixin:
    """Metodos de renderizacao de templates. Herda estado de DiretorNarrativo."""

    # ------------------------------------------------------------------ #
    # HELPERS DE CALCULO                                                   #
    # ------------------------------------------------------------------ #

    def _calcular_bg_src(self, ano):
        if ano == 2026:
            historico = self.motor.estado.get("historico_rotas", [])
            rota = next((r for r in reversed(historico) if r in ROTA_BG_2026), None)
            return f"/static/img/{ROTA_BG_2026.get(rota, 'bg_2026')}.png"
        return f"/static/img/bg_{ano}.png"

    def _spotlight_for_agente(self, agente_raw):
        agente = agente_raw.replace("ID_", "")
        if agente == "Vagner":
            return dict(personagem_foco="Vagner",
                        img_esq_src="/static/img/vagner.png", ator_esq_foco=True,
                        mostra_npc=True, npc_eh_foco=False,
                        img_npc_src="/static/img/gerente.png")
        nome_img = IMG_PERSONS.get(agente, agente.lower())
        return dict(personagem_foco=agente,
                    img_esq_src="/static/img/vagner.png", ator_esq_foco=False,
                    mostra_npc=True, npc_eh_foco=True,
                    img_npc_src=f"/static/img/{nome_img}.png")

    def _tema_atual(self):
        return "tema-" + flask_session.get("tema_visual", "a")

    def _render_game_ui(self, texto_html, opcoes_html, spotlight, ano,
                        bg_src=None, estado=None):
        """Wrapper unico para render_template('game_ui.html')."""
        if bg_src is None:
            bg_src = self._calcular_bg_src(ano)
        est = estado if estado is not None else self.motor.estado
        return render_template(
            "game_ui.html",
            tema_escolhido=self._tema_atual(),
            ano=ano,
            bg_src=bg_src,
            personagem_foco=spotlight["personagem_foco"],
            mostra_npc=spotlight["mostra_npc"],
            npc_eh_foco=spotlight["npc_eh_foco"],
            img_npc_src=spotlight["img_npc_src"],
            img_esq_src=spotlight["img_esq_src"],
            ator_esq_foco=spotlight["ator_esq_foco"],
            texto_dialogo=texto_html,
            opcoes_dialogo=opcoes_html,
            caixa=est.get("caixa", 0),
            stress=est.get("stress", 0),
            acervo=est.get("acervo", 0),
            tracao=est.get("tracao", 0),
        )

    # ------------------------------------------------------------------ #
    # RENDERIZACAO GAMEPLAY PADRAO                                         #
    # ------------------------------------------------------------------ #

    def _renderizar_gameplay(self, dados):
        """Renderiza o HTML do gameplay padrao."""
        if dados.get("ano") == 2026 and self.passo_encruzilhada_2026 == 0:
            evt_check = self.motor.obter_evento_atual()
            if evt_check and evt_check.get("id") == "evento_encruzilhada_2026":
                self.passo_encruzilhada_2026 = 1
                return self._orquestrar_encruzilhada_2026()

        evt_atual = self.motor.obter_evento_atual()
        _tem_pendente = (self.motor.estado.get("texto_gerente_pendente") or
                         self.motor.estado.get("texto_treplica_pendente"))
        if evt_atual and "dialogos_iniciais" in evt_atual and not _tem_pendente:
            return self._orquestrar_dialogo_evento(evt_atual, dados)

        estado_barras = dados.get("estado", {})
        texto_raw = dados.get("texto") or ""
        texto_html = f"<p class='fala-dialogo'>{texto_raw.replace(chr(10), '<br>')}</p>"
        opcoes_html = "".join(
            f"<button class='btn-opcao' hx-post='/api/interagir' "
            f"hx-vals='{{\"choice\": {idx}}}' "
            f"hx-target='#ui-jogo' hx-swap='innerHTML'>{opcao_txt}</button>"
            for idx, opcao_txt in enumerate(dados["opcoes"])
        )

        personagem_foco = dados.get("personagem", "Sistema")
        if personagem_foco == "Sistema":
            spotlight = dict(personagem_foco="Sistema",
                             img_esq_src="/static/img/vagner.png", ator_esq_foco=False,
                             mostra_npc=False, npc_eh_foco=False, img_npc_src="")
        elif personagem_foco == "Vagner":
            spotlight = dict(personagem_foco="Vagner",
                             img_esq_src="/static/img/vagner.png", ator_esq_foco=True,
                             mostra_npc=True, npc_eh_foco=False,
                             img_npc_src="/static/img/gerente.png")
        else:
            spotlight = dict(personagem_foco=personagem_foco,
                             img_esq_src="/static/img/vagner.png", ator_esq_foco=False,
                             mostra_npc=True, npc_eh_foco=True,
                             img_npc_src=f"/static/img/{personagem_foco.lower()}.png")

        ano = dados.get("ano", 1999)
        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano,
                                    estado=estado_barras)

    def _orquestrar_dialogo_evento(self, evt, dados):
        """Exibe dialogos_iniciais de um evento UM POR VEZ."""
        evt_id = evt.get("id", "")
        dialogos = evt["dialogos_iniciais"]
        estado_barras = dados.get("estado", {})
        ano = dados.get("ano", 2026)

        if evt_id != self._ultimo_evento_dialogo_id:
            self._ultimo_evento_dialogo_id = evt_id
            self._passo_dialogo_evento = 0

        btn_continuar = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>"
        )

        if self._passo_dialogo_evento < len(dialogos):
            d = dialogos[self._passo_dialogo_evento]
            agente = d["agente"].replace("ID_", "")
            texto_html = (f"<p class='nome-personagem'>{agente}</p>"
                          f"<p class='fala-dialogo'>{d['fala']}</p>")
            self._passo_dialogo_evento += 1
            opcoes_html = btn_continuar
            spotlight = self._spotlight_for_agente(d["agente"])
        else:
            texto_html = ""
            opcoes_html = "".join(
                f"<button class='btn-opcao' hx-post='/api/interagir' "
                f"hx-vals='{{\"choice\": {idx}}}' "
                f"hx-target='#ui-jogo' hx-swap='innerHTML'>{opcao_txt}</button>"
                for idx, opcao_txt in enumerate(dados["opcoes"])
            )
            spotlight = dict(personagem_foco="Sistema",
                             img_esq_src="/static/img/vagner.png", ator_esq_foco=False,
                             mostra_npc=False, npc_eh_foco=False, img_npc_src="")

        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano,
                                    estado=estado_barras)

    # ------------------------------------------------------------------ #
    # RENDERIZACAO DE RESULTADO FINAL                                      #
    # ------------------------------------------------------------------ #

    def _renderizar_game_over(self):
        return render_template(
            "game_over.html",
            game_over_text="<h2>SISTEMA CORROMPIDO: GAME OVER</h2>"
                           "<p>As metricas da locadora colapsaram.</p>"
        )

    def _renderizar_fim_de_jogo(self):
        est = self.motor.estado
        caixa  = est.get("caixa",  0)
        tracao = est.get("tracao", 0)
        acervo = est.get("acervo", 0)
        stress = est.get("stress", 0)
        score_total = caixa + tracao + acervo - stress

        if score_total >= 200:
            classificacao = "LENDARIO - A locadora entrou para a historia!"
        elif score_total >= 150:
            classificacao = "EXCELENTE - Uma gestao de mao cheia!"
        elif score_total >= 100:
            classificacao = "BOM - Sobrevivemos a virada do milenio."
        elif score_total >= 50:
            classificacao = "REGULAR - Deu pra segurar as pontas."
        else:
            classificacao = "DIFICIL - Mal chegamos ao fim."

        return render_template(
            "fim_de_jogo.html",
            caixa=caixa, tracao=tracao, acervo=acervo, stress=stress,
            score_total=score_total, classificacao=classificacao
        )

    # ------------------------------------------------------------------ #
    # SLIDE DO PROLOGO (compartilhado com prologo_mixin)                  #
    # ------------------------------------------------------------------ #

    def _render_prologo_slide(self, texto_html, opcoes_html,
                               vagner_visivel=False, vagner_foco=False,
                               npc_visivel=False, npc_foco=False, npc_img="",
                               img_esq_src=None, ator_esq_foco=None):
        if not vagner_visivel:
            personagem_foco = "Sistema"
        elif vagner_foco:
            personagem_foco = "Vagner"
        else:
            personagem_foco = "Outro"

        _img_esq = img_esq_src if img_esq_src is not None else "/static/img/vagner.png"
        _ator_esq = ator_esq_foco if ator_esq_foco is not None else vagner_foco

        spotlight = dict(personagem_foco=personagem_foco,
                         img_esq_src=_img_esq, ator_esq_foco=_ator_esq,
                         mostra_npc=npc_visivel, npc_eh_foco=npc_foco,
                         img_npc_src=npc_img)
        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano=2026,
                                    bg_src="/static/img/bg_2026.png")
