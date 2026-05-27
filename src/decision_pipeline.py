# src/decision_pipeline.py
# Pipeline explícito de processamento de uma interação de gameplay.
#
# Etapas por requisição em /api/interagir:
#   1. Hydrate  — reconstrói DiretorNarrativo a partir do estado da sessão
#   2. FSM      — processa escolha do jogador (transição de estado)
#   3. Rules    — calcula impactos nas métricas (encapsulado em proximo_passo)
#   4. AI       — busca texto no pool ou gera via Gemini (encapsulado em proximo_passo)
#   5. Crisis   — verifica limiares e injeta evento de crise se necessário
#   6. Render   — gera o próximo frame HTML via DiretorNarrativo
#   7. Commit   — persiste o novo estado de volta na sessão
#
# O GamePipeline recebe hydrate/commit/crisis como injeção de dependência,
# mantendo o módulo desacoplado do Flask e testável sem contexto HTTP.

from __future__ import annotations
import traceback
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.narrative_director import DiretorNarrativo


class GamePipeline:
    """Pipeline stateless de processamento de gameplay.

    Instanciado uma vez no module-level do app.py e reutilizado em todas
    as requisições — não guarda estado entre chamadas.
    """

    def __init__(
        self,
        hydrate_fn: Callable[[], "DiretorNarrativo"],
        commit_fn:  Callable[["DiretorNarrativo"], None],
        crisis_fn:  Callable[["DiretorNarrativo"], None],
    ):
        """
        hydrate_fn : () → DiretorNarrativo       (lê sessão Flask)
        commit_fn  : (DiretorNarrativo) → None   (grava sessão Flask)
        crisis_fn  : (DiretorNarrativo) → None   (verifica e injeta crise)
        """
        self._hydrate = hydrate_fn
        self._commit  = commit_fn
        self._crisis  = crisis_fn

    # ------------------------------------------------------------------ #
    # Pipeline principal — POST /api/interagir                            #
    # ------------------------------------------------------------------ #

    def run(self, escolha: int | None):
        """Executa o pipeline completo para uma interação do jogador.

        FSM + Rules + AI + Render estão encapsulados em proximo_passo().
        Crisis é verificado separadamente pós-escolha para não contaminar
        o frame de resposta do passo atual.
        """
        # 1. Hydrate
        diretor: DiretorNarrativo = self._hydrate()

        # 2-4. FSM + Rules + AI + 6. Render
        response = diretor.proximo_passo(escolha)

        # 5. Crisis (somente quando há escolha explícita do jogador)
        if escolha is not None:
            self._crisis(diretor)

        # 7. Commit
        self._commit(diretor)

        return response

    def run_safe(self, escolha: int | None):
        """run() com fallback: em erro, re-renderiza o frame atual sem avançar."""
        try:
            return self.run(escolha)
        except Exception as exc:
            print(f"[GamePipeline] ERRO em run(): {exc}\n{traceback.format_exc()}", flush=True)
            return self._fallback_render()

    # ------------------------------------------------------------------ #
    # Pipeline simplificado — demais rotas de gameplay                    #
    # ------------------------------------------------------------------ #

    def run_action(self, action_fn: Callable[["DiretorNarrativo"], object]):
        """Hydrate → action → Commit. Para rotas sem escolha do jogador.

        Não injeta crise (ações cinematicas/de transição não disparam crises).

        Uso:
            return _pipeline.run_action(lambda d: d.handle_animacao_concluida())
        """
        diretor: DiretorNarrativo = self._hydrate()
        response = action_fn(diretor)
        self._commit(diretor)
        return response

    # ------------------------------------------------------------------ #
    # Fallback interno                                                     #
    # ------------------------------------------------------------------ #

    def _fallback_render(self):
        """Tenta re-renderizar o frame atual sem avançar o estado."""
        from flask import make_response
        try:
            diretor = self._hydrate()
            dados   = diretor.motor.formatar_para_frontend()
            return make_response(diretor._renderizar_gameplay(dados))
        except Exception:
            return make_response(
                "<p style='color:red'>Erro interno. Recarregue a página.</p>", 500
            )
