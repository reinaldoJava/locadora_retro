# src/narrative_director.py
# Coordenador central — estado e roteamento.
# Toda logica especifica vive nos mixins correspondentes.
import json
from pathlib import Path

from src.renderer_mixin  import RendererMixin
from src.cinematic_mixin import CinematicMixin
from src.prologo_mixin   import PrologoMixin
from src.intro_mixin     import IntroMixin


class DiretorNarrativo(RendererMixin, CinematicMixin, PrologoMixin, IntroMixin):
    """
    Coordenador narrativo do jogo.

    Estado centralizado aqui; comportamento distribuido nos mixins:
      RendererMixin  — renderizacao de templates (game_ui, fim de jogo, game over)
      CinematicMixin — transicao inicial e virada cinematica 1999 -> 2026
      PrologoMixin   — prologo 2026, encruzilhada e sequenciamento de dialogos
      IntroMixin     — sequencia de slides da intro
    """

    def __init__(self, engine_instance):
        self.motor = engine_instance

        # --- Estado cinematico ---
        self._initial_game_transition_step = 0
        self.passo_cinematico = 0

        # --- Estado da intro ---
        self.nome_jogador = "Gerente"
        self.slide_atual = 0
        self.roteiro_intro = []

        # --- Estado do prologo / 2026 ---
        self.passo_prologo_2026 = 0
        self.passo_encruzilhada_2026 = 0
        self.rota_escolhida_id = None
        self._passo_dialogo_evento = 0
        self._ultimo_evento_dialogo_id = ""

        # --- Dados estaticos carregados uma vez ---
        base = Path(__file__).resolve().parent.parent / "data"

        with open(base / "intro.json", "r", encoding="utf-8") as f:
            self._roteiro_intro_base = json.load(f)

        with open(base / "evento_salto_temporal.json", "r", encoding="utf-8") as f:
            self._roteiro_salto_temporal = json.load(f)

    # ------------------------------------------------------------------ #
    # PONTO DE ENTRADA UNICO                                               #
    # ------------------------------------------------------------------ #

    def _aplicar_impactos_crise_vitoria(self):
        """Aplica os impactos numericos apos resolucao vitoriosa de uma crise."""
        crise_id = self.motor.estado.get("crise_ativa_id", "")
        est = self.motor.estado
        if crise_id == "ultimato_leila_tracao":
            est["tracao"] = min(100, est.get("tracao", 0) + 40)
            est["caixa"]  = max(0, int(est.get("caixa", 0) * 0.80))
        elif crise_id == "ultimato_mauricio_acervo":
            est["acervo"] = min(100, est.get("acervo", 0) + 30)
            est["stress"] = max(0, est.get("stress", 0) - 10)
        elif crise_id == "ultimato_vagner_operacional":
            est["stress"] = max(0, est.get("stress", 0) - 60)
            est["caixa"]  = max(0, est.get("caixa", 0) - 3000)
        elif crise_id == "ultimato_advogado_caixa":
            est["caixa"]  = max(0, est.get("caixa", 0) + 2000)
            est["tracao"] = max(0, est.get("tracao", 0) - 15)
        est["crise_ativa_id"] = None

    def proximo_passo(self, escolha_usuario=None):
        """Roteia para o mixin correto conforme o estado atual do jogo."""

        if self.motor.verificar_game_over():
            return self._renderizar_game_over()

        if self.passo_prologo_2026 > 0:
            return self._orquestrar_prologo_2026(escolha_usuario)

        if self.passo_encruzilhada_2026 > 0:
            return self._orquestrar_encruzilhada_2026(escolha_usuario)

        if escolha_usuario is not None:
            self.motor.processar_escolha(escolha_usuario)

        # Verifica se uma crise foi resolvida neste passo
        if self.motor.estado.pop("crise_resolvida", False):
            resultado = self.motor.estado.get("crise_resultado", "game_over")
            self.motor.estado["crise_resultado"] = None
            if resultado == "game_over":
                self.motor.estado["game_over_forcado"] = True
                return self._renderizar_game_over()
            # vitoria: aplica penalidades numericas
            self._aplicar_impactos_crise_vitoria()

        if self._initial_game_transition_step and self._initial_game_transition_step > 0:
            return self._orquestrar_initial_game_transition()

        dados_motor = self.motor.formatar_para_frontend()

        if dados_motor.get("virada_1999") or self.passo_cinematico > 0:
            return self._orquestrar_virada_2026(dados_motor)

        if dados_motor.get("fim"):
            return self._renderizar_fim_de_jogo()

        return self._renderizar_gameplay(dados_motor)
