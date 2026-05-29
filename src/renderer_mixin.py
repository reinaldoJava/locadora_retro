# src/renderer_mixin.py
# Camada de renderizacao: converte estado do Engine em HTML para o frontend.
# Todos os metodos retornam strings HTML ou objetos Response Flask.
#
# _render_game_ui()       — unico ponto de chamada a render_template(game_ui.html)
# _renderizar_gameplay()  — frame padrao: detecta spotlight, monta texto e opcoes
# _orquestrar_dialogo_evento() — exibe dialogos_iniciais um por vez antes das opcoes
# _render_prologo_slide() — slide do prologo 2026 (compartilhado com PrologoMixin)

import threading
import json
from flask import render_template, session as flask_session, make_response
from src.Maps import ROTA_BG_2026, IMG_PERSONS
from src.audio_config import AUDIO_SETTINGS
from src.agents import obter_do_pool, adicionar_ao_pool, gerar_fala, preaquecer_replicas, LLMFallbackError


class RendererMixin:
    """Metodos de renderizacao de templates. Herda estado de DiretorNarrativo."""

    # ------------------------------------------------------------------ #
    # HELPERS DE CALCULO                                                   #
    # ------------------------------------------------------------------ #

    def _calcular_bg_src(self, ano):
        if ano == 2026:
            historico = self.motor.estado.get("historico_rotas", [])
            rota = next((r for r in reversed(historico) if r in ROTA_BG_2026), None)
            return f"/static/img/{ROTA_BG_2026.get(rota, 'bg_2026')}.webp"
        return f"/static/img/bg_{ano}.webp"

    def _spotlight_for_agente(self, agente_raw):
        agente = agente_raw.replace("ID_", "")
        if agente == "Vagner":
            return dict(personagem_foco="Vagner",
                        img_esq_src="/static/img/vagner.webp", ator_esq_foco=True,
                        mostra_npc=True, npc_eh_foco=False,
                        img_npc_src="/static/img/gerente.webp")
        nome_img = IMG_PERSONS.get(agente, agente.lower())
        return dict(personagem_foco=agente,
                    img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                    mostra_npc=True, npc_eh_foco=True,
                    img_npc_src=f"/static/img/{nome_img}.webp")

    def _sub_curador(self, texto: str) -> str:
        """Resolve {curador_nome} e substitui referências nominais ao curador se necessário."""
        flags = self.motor.estado.get("flags", {})
        curador = flags.get("curador_nome", "Maurício")
        texto = texto.replace("{curador_nome}", curador)
        if not flags.get("mauricio_saiu"):
            return texto
        texto = texto.replace("Maurício", "Marcos").replace("Mauricio", "Marcos")
        texto = texto.replace("o Maurício", "o Marcos").replace("do Maurício", "do Marcos")
        return texto

    def _preparar_fala_com_typing(self, texto_html, nome_personagem=None):
        """Helper cirúrgico para formatar o HTML com alvo de digitação e registrar o comando UI."""
        texto_html = self._sub_curador(texto_html)
        self._ui_commands.append({
            "action": "typeText",
            "args": {
                "elementId": "fala-typing-target",
                "fullText": texto_html,
                "speed": 25,
                "typingVolume": AUDIO_SETTINGS.get("keyboard_volume", 0.4)
            }
        })
        nome_html = f"<p class='nome-personagem'>{nome_personagem}</p>" if nome_personagem else ""
        return f"{nome_html}<p class='fala-dialogo' id='fala-typing-target'></p>"

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
        contexto  = self._sub_curador(contexto)
        argumento = self._sub_curador(argumento)
        fala = obter_do_pool(pool_key)
        if not fala:
            try:
                fala = gerar_fala(agente_id, contexto, ano, temperatura, argumento=argumento)
                adicionar_ao_pool(pool_key, fala)
            except LLMFallbackError:
                # Cota esgotada: exibe o texto do script, não salva no pool.
                fala = argumento
        fala_personalizada = fala.replace("Gerente", self.nome_jogador)
        fala_html = fala_personalizada.replace(chr(10), "<br>")
        return self._preparar_fala_com_typing(fala_html, agente_nome)

    def _render_game_ui(self, texto_html, opcoes_html, spotlight, ano,
                        bg_src=None, estado=None):
        """Wrapper único para render_template('game_ui.html') retornando Response com comandos UI."""
        if bg_src is None:
            bg_src = self._calcular_bg_src(ano)
        est = estado if estado is not None else self.motor.estado
        html = render_template(
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
            moral_equipe=est.get("moral_equipe", 70),
        )
        response = make_response(html)
        if hasattr(self, '_ui_commands') and self._ui_commands:
            triggers = {}
            # Preserva triggers existentes no header HX-Trigger se houver
            if "HX-Trigger" in response.headers:
                try: triggers = json.loads(response.headers["HX-Trigger"])
                except: pass
            triggers["ui_commands"] = self._ui_commands
            response.headers["HX-Trigger"] = json.dumps(triggers)
            self._ui_commands = [] # Limpa o buffer para a próxima interação
        return response

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
                texto_html = self._preparar_fala_com_typing(
                    evt_atual["contexto_ia"].replace(chr(10), "<br>"), "Sistema")
                opcoes_html = ("<button class='btn-opcao' hx-post='/api/interagir' "
                               "hx-vals='{\"choice\": 0}' "
                               "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>")
                spotlight = dict(personagem_foco="Sistema",
                                 img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
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
            agente_id   = self.motor._resolver_agente(evt_atual["agente_foco"])
            agente_nome = agente_id.replace("ID_", "")
            fala        = obter_do_pool(evt_id)
            if fala:
                # Pool hit: renderização instantânea; substitui placeholder pelo nome real.
                fala_personalizada = fala.replace("Gerente", self.nome_jogador)
                fala_html  = fala_personalizada.replace(chr(10), "<br>")
                texto_html = self._preparar_fala_com_typing(fala_html, agente_nome)
                # Pré-aquece réplicas em background — SSE não é disparado no pool hit,
                # então o warming nunca aconteceria sem este disparo explícito.
                threading.Thread(
                    target=preaquecer_replicas, args=(evt_atual,), daemon=True
                ).start()
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
            texto_html = self._preparar_fala_com_typing(texto_raw.replace(chr(10), "<br>"), "Sistema")
        elif self.motor.estado.get("texto_gerente_pendente"):
            # Fala do Gerente: exibe fala_gerente ou argumento_gerente sem chamar LLM
            texto_raw  = dados.get("texto") or ""
            texto_html = self._preparar_fala_com_typing(
                texto_raw.replace(chr(10), "<br>"), self.nome_jogador)
        elif self.motor.estado.get("texto_treplica_pendente"):
            agente_atual  = self.motor.estado.get("agente_atual", "Vagner")
            treplica_val  = self.motor.estado.get("texto_treplica_pendente", "")
            # "_pending_" = sentinel LLM (1999 e 2026 rotas simples).
            # Texto estático só é exibido diretamente quando agente_atual=="Sistema"
            # E o valor não é o sentinel (formato legado de tréplicas multi-personagem).
            if agente_atual == "Sistema" and treplica_val != "_pending_":
                texto_raw  = dados.get("texto") or ""
                texto_html = self._preparar_fala_com_typing(texto_raw.replace(chr(10), "<br>"))
            else:
                # LLM gera a tréplica para 1999 e 2026
                texto_html = self._renderizar_fala_llm(
                    contexto    = evt_atual.get("contexto_ia", "") if evt_atual else "",
                    agente_id   = self.motor._resolver_agente("ID_" + agente_atual),
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
                texto_html = self._preparar_fala_com_typing(texto_raw.replace(chr(10), "<br>"), agente_nome)
            else:
                # Réplica 1999: contexto_ia como cena + fala_gerente como gatilho → gerar_fala síncrono com pool
                evt_id    = evt_atual.get("id", "") if evt_atual else ""
                rota_idx  = self.motor.estado["rota_pendente_idx"]
                rota      = (evt_atual["rotas_principais"][rota_idx]
                             if evt_atual and "rotas_principais" in evt_atual else {})
                pool_key  = f"{evt_id}:replica:{rota_idx}"
                agente_id = self.motor._resolver_agente(
                    evt_atual.get("agente_foco", "ID_Vagner") if evt_atual else "ID_Vagner")
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
            texto_html = self._preparar_fala_com_typing(texto_raw.replace(chr(10), "<br>"))
        opcoes_html = "".join(
            f"<button class='btn-opcao' hx-post='/api/interagir' "
            f"hx-vals='{{\"choice\": {idx}}}' "
            f"hx-target='#ui-jogo' hx-swap='innerHTML'>{self._sub_curador(opcao_txt)}</button>"
            for idx, opcao_txt in enumerate(dados["opcoes"])
        )

        personagem_foco = dados.get("personagem", "Sistema")
        if personagem_foco == "Sistema":
            spotlight = dict(personagem_foco="Sistema",
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                             mostra_npc=False, npc_eh_foco=False, img_npc_src="")
        elif personagem_foco == "Vagner":
            spotlight = dict(personagem_foco="Vagner",
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=True,
                             mostra_npc=True, npc_eh_foco=False,
                             img_npc_src="/static/img/gerente.webp")
        else:
            spotlight = dict(personagem_foco=personagem_foco,
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                             mostra_npc=True, npc_eh_foco=True,
                             img_npc_src=f"/static/img/{personagem_foco.lower()}.webp")

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
            agente_id_resolvido = self.motor._resolver_agente(d["agente"])
            agente = agente_id_resolvido.replace("ID_", "")
            texto_html = self._preparar_fala_com_typing(d['fala'], agente)
            self._passo_dialogo_evento += 1
            opcoes_html = btn_continuar
            spotlight = self._spotlight_for_agente(agente_id_resolvido)
        else:
            texto_html = ""
            opcoes_html = "".join(
                f"<button class='btn-opcao' hx-post='/api/interagir' "
                f"hx-vals='{{\"choice\": {idx}}}' "
                f"hx-target='#ui-jogo' hx-swap='innerHTML'>{self._sub_curador(opcao_txt)}</button>"
                for idx, opcao_txt in enumerate(dados["opcoes"])
            )
            spotlight = dict(personagem_foco="Sistema",
                             img_esq_src="/static/img/vagner.webp", ator_esq_foco=False,
                             mostra_npc=False, npc_eh_foco=False, img_npc_src="")

        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano,
                                    estado=estado_barras)

    # ------------------------------------------------------------------ #
    # RENDERIZACAO DE RESULTADO FINAL                                      #
    # ------------------------------------------------------------------ #

    def _renderizar_apresentacao_marcos(self):
        """Tela de boas-vindas ao Marcos, exibida uma única vez após a saída do Maurício."""
        texto = (
            "Marcos assume o posto. Aos 28 anos e criado na vizinhança, ele traz um olhar equilibrado: "
            "um cinéfilo pragmático que entende a locadora como um ecossistema onde curadoria e lucro precisam coexistir."
            "Diferente de seu antecessor, ele é flexível e observador, mas não hesita em usar argumentos afiados se sentir que a saúde do negócio está em risco."
            "Marcos agora é o novo estagiário da locadora."
        )
        texto_html = self._preparar_fala_com_typing(texto, "Sistema")
        opcoes_html = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-vals='{\"choice\": 0}' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Continuar</button>"
        )
        spotlight = dict(
            personagem_foco="Marcos",
            img_esq_src="/static/img/vagner.webp",
            ator_esq_foco=False,
            mostra_npc=True,
            npc_eh_foco=True,
            img_npc_src="/static/img/marcos.webp",
        )
        return self._render_game_ui(
            texto_html, opcoes_html, spotlight,
            ano=1999,
            estado=self.motor.estado,
        )

    # Mensagens de alerta por crise — Vagner avisa o gerente antes do confronto
    _ALERTAS_CRISE = {
        "ultimato_leila_tracao":       "A Leila pediu pra falar com você. Parece que ela tomou uma decisão.",
        "ultimato_mauricio_acervo":    "O Maurício tá com as coisas dele ali. Ele quer conversar agora.",
        "ultimato_marcos_acervo":      "O Marcos parou tudo e quer uma conversa séria. É sobre o acervo.",
        "ultimato_vagner_operacional": "Chefe, eu preciso falar com você. Não pode esperar.",
        "ultimato_moral_equipe":       "A equipe parou. Eles querem uma reunião com você agora.",
        "ultimato_advogado_caixa":     "Chefe, tem um problema sério no caixa. Você precisa ver isso.",
    }

    def _renderizar_crise_alerta(self):
        """Tela intermediária: Vagner alerta o gerente antes do evento de crise."""
        est = self.motor.estado
        crise_id = est.get("crise_ativa_id", "")
        msg = self._ALERTAS_CRISE.get(crise_id, "Chefe, tem uma situação. Você precisa ir lá.")

        # Vagner fala, gerente ouve — spotlight padrão Vagner
        texto_html = self._preparar_fala_com_typing(msg, "Vagner")
        opcoes_html = (
            "<button class='btn-opcao' hx-post='/api/interagir' "
            "hx-vals='{\"choice\": 0}' "
            "hx-target='#ui-jogo' hx-swap='innerHTML'>Atender</button>"
        )
        spotlight = dict(
            personagem_foco="Vagner",
            img_esq_src="/static/img/vagner.webp", ator_esq_foco=True,
            mostra_npc=True, npc_eh_foco=False,
            img_npc_src="/static/img/gerente.webp",
        )
        evt_atual = self.motor.obter_evento_atual()
        ano = evt_atual.get("ano", 2026) if evt_atual else 2026
        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano=ano, estado=est)

    def _renderizar_game_over(self):
        """Tela de game over contextualizada: fundo da era atual, NPC visível, texto narrativo."""
        est = self.motor.estado

        # Determina o ano atual
        evt_atual = self.motor.obter_evento_atual()
        ano = evt_atual.get("ano", 1999) if evt_atual else 1999

        # Determina o NPC responsável pela crise
        agente_nome = est.get("agente_atual", "Vagner")
        if not agente_nome or agente_nome == "Sistema":
            agente_nome = "Vagner"
        agente_id_resolvido = self.motor._resolver_agente("ID_" + agente_nome)
        agente_nome_final = agente_id_resolvido.replace("ID_", "")

        nome_jogador = getattr(self, "nome_jogador", "Gerente")

        texto_alerta = (
            f"⚠ SITUAÇÃO CRÍTICA — {agente_nome_final.upper()}<br><br>"
            f"Os acontecimentos recentes criaram um desconforto sério entre "
            f"<strong>{nome_jogador}</strong> e <strong>{agente_nome_final}</strong>.<br><br>"
            f"Essa situação é crítica e precisa ser resolvida com cautela. "
            f"Se nada mudar, o futuro do <strong>{nome_jogador}</strong> "
            f"na locadora estará em risco."
        )
        texto_html = self._preparar_fala_com_typing(texto_alerta, "Sistema")

        opcoes_html = (
            "<button class='btn-opcao' onclick=\"window.location.href='/'\""
            " style='background: var(--btn-hover-bg, #c8692a);'>"
            "RECONECTAR SISTEMA</button>"
        )

        spotlight = self._spotlight_for_agente(agente_id_resolvido)

        return self._render_game_ui(
            texto_html, opcoes_html, spotlight,
            ano=ano,
            estado=est,
        )

    def _renderizar_fim_de_jogo(self):
        est = self.motor.estado
        caixa        = est.get("caixa",  0)
        tracao       = est.get("tracao", 0)
        acervo       = est.get("acervo", 0)
        stress       = est.get("stress", 0)
        moral_equipe = est.get("moral_equipe", 70)
        mult         = est.get("dificuldade_mult", 1.0)
        dificuldade  = est.get("dificuldade_nome", "BETA")
        score_base   = caixa + tracao + acervo - stress + moral_equipe
        score_total  = int(score_base * mult)

        if score_total >= 400:
            classificacao = "LENDARIO - A locadora entrou para a historia!"
        elif score_total >= 300:
            classificacao = "EXCELENTE - Uma gestao de mao cheia!"
        elif score_total >= 200:
            classificacao = "BOM - Sobrevivemos a virada do milenio."
        elif score_total >= 130:
            classificacao = "REGULAR - Deu pra segurar as pontas."
        else:
            classificacao = "DIFICIL - Mal chegamos ao fim."

        return render_template(
            "fim_de_jogo.html",
            caixa=caixa, tracao=tracao, acervo=acervo, stress=stress,
            moral_equipe=moral_equipe,
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

        _img_esq = img_esq_src if img_esq_src is not None else "/static/img/vagner.webp"
        _ator_esq = ator_esq_foco if ator_esq_foco is not None else vagner_foco

        spotlight = dict(personagem_foco=personagem_foco,
                         img_esq_src=_img_esq, ator_esq_foco=_ator_esq,
                         mostra_npc=npc_visivel, npc_eh_foco=npc_foco,
                         img_npc_src=npc_img)
        return self._render_game_ui(texto_html, opcoes_html, spotlight, ano=2026,
                                    bg_src="/static/img/bg_2026.webp")
