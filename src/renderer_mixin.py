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
from src.agents import obter_do_pool, adicionar_ao_pool, gerar_fala


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

    def _renderizar_fala_llm(self, contexto: str, agente_id: str, ano: int,
                             pool_key: str, temperatura: float | None,
                             argumento: str = "") -> str:
        """Pool + gerar_fala síncrono para réplica e tréplica.
        Pool hit → instantâneo. Pool miss → chamada LLM (~1s), armazena no pool.
        'Gerente' no texto gerado é substituído pelo nome real do jogador.
        contexto  = contexto_ia (premissa da cena).
        argumento = o que o Gerente disse (fala_gerente ou argumento_gerente).
        """
        agente_nome = agente_id.replace("ID_", "")
       # fala = obter_do_pool(pool_key)
        fala = None
        if not fala:
            fala = gerar_fala(agente_id, contexto, ano, temperatura, argumento=argumento)
            adicionar_ao_pool(pool_key, fala)
        fala_personalizada = fala.replace("Gerente", self.nome_jogador)
        fala_html = fala_personalizada.replace(chr(10), "<br>")
        return ("<p class='nome-personagem'>" + agente_nome + "</p>"
                "<p class='fala-dialogo'>" + fala_html + "</p>")

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
        _contexto_ia_pendente = (
            bool(evt_atual and evt_atual.get("agente_foco") and evt_atual.get("contexto_ia") and
                 self.motor.estado.get("_contexto_exibido_id") != evt_atual.get("id") and
                 self.motor.estado.get("rota_pendente_idx") is None)
        )
        _tem_pendente = (self.motor.estado.get("texto_gerente_pendente") or
                         self.motor.estado.get("texto_treplica_pendente") or
                         _contexto_ia_pendente)
        if evt_atual and "dialogos_iniciais" in evt_atual and not _tem_pendente:
            # Exibe contexto_ia como frame Sistema antes de iniciar os dialogos do evento
            if (evt_atual.get("contexto_ia") and
                    self.motor.estado.get("_contexto_exibido_id") != evt_atual.get("id")):
                texto_html = ("<p class='fala-dialogo'>" +
                              evt_atual["contexto_ia"].replace(chr(10), "<br>") + "</p>")
                opcoes_html = ("<button class='btn-opcao' hx-post='/api/interagir' "
                               "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>")
                spotlight = dict(personagem_foco="Sistema",
                                 img_esq_src="/static/img/vagner.png", ator_esq_foco=False,
                                 mostra_npc=False, npc_eh_foco=False, img_npc_src="")
                return self._render_game_ui(texto_html, opcoes_html, spotlight,
                                            ano=evt_atual.get("ano", 2026),
                                            estado=self.motor.estado)
            return self._orquestrar_dialogo_evento(evt_atual, dados)

        estado_barras = dados.get("estado", {})

        # Fala dinâmica via LLM para eventos 1999 com agente_foco.
        # Pool hit  → renderização instantânea com nome personalizado.
        # Pool miss → placeholder com trigger SSE; geração e persistência no pool
        #             ocorrem no endpoint /api/fala-stream via streaming.
        if (evt_atual and
                evt_atual.get("agente_foco") and
                evt_atual.get("ano") == 1999 and
                not _tem_pendente and
                self.motor.estado.get("rota_pendente_idx") is None):
            evt_id      = evt_atual.get("id", "")
            agente_id   = evt_atual["agente_foco"]
            agente_nome = agente_id.replace("ID_", "")
            fala        = obter_do_pool(evt_id)
            if fala:
                # Pool hit: renderização instantânea; substitui placeholder pelo nome real.
                fala_personalizada = fala.replace("Gerente", self.nome_jogador)
                fala_html  = fala_personalizada.replace(chr(10), "<br>")
                texto_html = ("<p class='nome-personagem'>" + agente_nome + "</p>"
                              "<p class='fala-dialogo'>" + fala_html + "</p>")
            else:
                # Pool miss: placeholder com trigger para o handler SSE no motor_shell.js.
                texto_html = (
                    "<p class='nome-personagem'>" + agente_nome + "</p>"
                    "<p class='fala-dialogo' id='fala-stream-target'"
                    " data-nome-jogador='" + self.nome_jogador + "'>▌</p>"
                    "<div id='fala-stream-trigger' style='display:none'></div>"
                )
        elif _contexto_ia_pendente:
            # Contexto IA: exibe premissa da situação como frame SISTEMA sem chamar LLM
            texto_raw  = dados.get("texto") or ""
            texto_html = "<p class='fala-dialogo'>" + texto_raw.replace(chr(10), "<br>") + "</p>"
        elif self.motor.estado.get("texto_gerente_pendente"):
            # Fala do Gerente: exibe fala_gerente ou argumento_gerente sem chamar LLM
            texto_raw  = dados.get("texto") or ""
            texto_html = ("<p class='nome-personagem'>" + self.nome_jogador + "</p>"
                          "<p class='fala-dialogo'>" + texto_raw.replace(chr(10), "<br>") + "</p>")
        elif self.motor.estado.get("texto_treplica_pendente"):
            agente_atual = self.motor.estado.get("agente_atual", "Vagner")
            if agente_atual == "Sistema":
                # 2026: tréplica é texto estático com múltiplos personagens — exibe diretamente
                texto_raw  = dados.get("texto") or ""
                texto_html = "<p class='fala-dialogo'>" + texto_raw.replace(chr(10), "<br>") + "</p>"
            else:
                # 1999: tréplica gera via LLM usando contexto_ia + argumento_gerente
                texto_html = self._renderizar_fala_llm(
                    contexto    = evt_atual.get("contexto_ia", "") if evt_atual else "",
                    agente_id   = "ID_" + agente_atual,
                    ano         = dados.get("ano", 1999),
                    pool_key    = self.motor.estado.get("pool_key_treplica", ""),
                    temperatura = self.motor.estado.get("temp_treplica"),
                    argumento   = self.motor.estado.get("llm_argumento", ""),
                )
        elif self.motor.estado.get("rota_pendente_idx") is not None:
            if self.motor.estado.get("crise_ativa_evento"):
                # Evento de crise: exibe texto estático do pushback (fala do personagem)
                texto_raw  = dados.get("texto", "")
                agente_nome = (evt_atual.get("agente_foco", "Sistema").replace("ID_", "")
                               if evt_atual else "Sistema")
                texto_html = ("<p class='nome-personagem'>" + agente_nome + "</p>"
                              "<p class='fala-dialogo'>" + texto_raw.replace(chr(10), "<br>") + "</p>")
            else:
                # Réplica 1999: contexto_ia como cena + fala_gerente como gatilho → gerar_fala síncrono com pool
                evt_id    = evt_atual.get("id", "") if evt_atual else ""
                rota_idx  = self.motor.estado["rota_pendente_idx"]
                rota      = (evt_atual["rotas_principais"][rota_idx]
                             if evt_atual and "rotas_principais" in evt_atual else {})
                pool_key  = f"{evt_id}:replica:{rota_idx}"
                agente_id = evt_atual.get("agente_foco", "ID_Vagner") if evt_atual else "ID_Vagner"
                texto_html = self._renderizar_fala_llm(
                    contexto        = evt_atual.get("contexto_ia", "") if evt_atual else "",
                    agente_id       = agente_id,
                    ano             = dados.get("ano", 1999),
                    pool_key        = pool_key,
                    temperatura     = rota.get("temp_replica"),
                    argumento       = self.motor.estado.get("llm_argumento", ""),
                )
        else:
            texto_raw  = dados.get("texto") or ""
            texto_html = "<p class='fala-dialogo'>" + texto_raw.replace(chr(10), "<br>") + "</p>"
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
        caixa       = est.get("caixa",  0)
        tracao      = est.get("tracao", 0)
        acervo      = est.get("acervo", 0)
        stress      = est.get("stress", 0)
        mult        = est.get("dificuldade_mult", 1.0)
        dificuldade = est.get("dificuldade_nome", "BETA")
        score_base  = caixa + tracao + acervo - stress
        score_total = int(score_base * mult)

        if score_total >= 300:
            classificacao = "LENDARIO - A locadora entrou para a historia!"
        elif score_total >= 200:
            classificacao = "EXCELENTE - Uma gestao de mao cheia!"
        elif score_total >= 120:
            classificacao = "BOM - Sobrevivemos a virada do milenio."
        elif score_total >= 60:
            classificacao = "REGULAR - Deu pra segurar as pontas."
        else:
            classificacao = "DIFICIL - Mal chegamos ao fim."

        return render_template(
            "fim_de_jogo.html",
            caixa=caixa, tracao=tracao, acervo=acervo, stress=stress,
            score_total=score_total, classificacao=classificacao,
            dificuldade=dificuldade
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
