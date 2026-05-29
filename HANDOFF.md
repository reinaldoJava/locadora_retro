# HANDOFF — Locadora Retrô

Documento de continuidade entre sessões. Lê este arquivo antes de continuar qualquer trabalho no projeto.

---

## CONTEXTO DO PROJETO

Jogo narrativo web (Flask + HTMX + JS Modules) ambientado em uma videolocadora em 1999, com salto temporal para 2026. O jogador assume o papel de gerente e toma decisões que afetam cinco NPCs/métricas:

- **Vagner** — Stress Operacional (invertida: stress alto = ruim)
- **Leila** — Tração & Hype
- **Maurício / Marcos** — Integridade do Acervo (Marcos substitui Maurício se `mauricio_saiu = true`)
- **Caixa** — recurso financeiro
- **Moral Equipe** — coesão da equipe

Deploy: **Google Cloud Run** · LLM: **Gemini API** · Pool de falas: **Firestore**

---

## STACK / ARQUITETURA REAL

- **Backend**: `app.py` (Flask). Sessão Flask serializa o `DiretorNarrativo` inteiro a cada request.
- **Pipeline**: `src/decision_pipeline.py` (`GamePipeline`). Etapas: Hydrate → FSM → Crisis → Render → Commit.
- **Orquestrador narrativo**: `src/narrative_director.py` (`DiretorNarrativo` + 4 mixins).
- **Engine de regras**: `src/engine.py` — FSM de estados, métricas, balanceamento dinâmico (`pressao`), perfis de jogador (`calcular_perfil`).
- **Agentes LLM**: `src/agents.py` — Gemini com pool Firestore. `LLMFallbackError` exibe texto do script sem salvar no pool.
- **Frontend**: HTMX 1.9.10 + `motor_shell.js`. Comandos UI chegam como JSON no header `HX-Trigger`.

---

## FLUXO DE CENAS

```
GET /  →  intro.html  →  slides da intro  →  HX-Redirect: /jogo
GET /jogo  →  index.html  →  hx-trigger="load"  →  POST /api/iniciar-game-transition
  → "SISTEMA CARREGADO" (typeText) → [clica INICIAR] → GIF terminal (animacaoTerminal 3s)
  → POST /api/animacao-concluida → gameplay 1999

[gameplay 1999: eventos dia1-diaV, 12 eventos no total]
  → virada cinematográfica (12 passos: contagem, terminal, wormhole.mp4)
  → prólogo 2026 → encruzilhada (4 rotas: A estúdio / B liquidação / C detox / D cine-pub)
  → eventos 2026 por rota

[qualquer momento: limiar de crise atingido]
  → _verificar_e_injetar_crise() → _crise_alerta_pendente = True
  → game_over.html (overlay dramático, botão ATENDER)
  → evento de crise (ultimato do NPC) → vitória ou derrota

[fim do jogo]
  → fim_de_jogo.html (score + perfil do jogador)
  → game_over definitivo → game_over.html (RECONECTAR SISTEMA → GET /reiniciar)

GET /reiniciar  →  session.clear()  →  redirect GET /
```

---

## SISTEMA DE CRISES

**6 crises em `data/game_over.json`:**

| ID | Agente | Limiar |
|---|---|---|
| `ultimato_advogado_caixa` | Vagner | Caixa ≤ 0 |
| `ultimato_vagner_operacional` | Vagner | Stress ≥ 90 |
| `ultimato_mauricio_acervo` | Maurício | Acervo ≤ 20 |
| `ultimato_marcos_acervo` | Marcos | Acervo ≤ 20 (quando Maurício saiu) |
| `ultimato_leila_tracao` | Leila | Tração ≤ 10 |
| `ultimato_moral_equipe` | Vagner | Moral Equipe ≤ 20 |

**Fluxo completo de crise:**
1. `_verificar_e_injetar_crise()` seta `crise_ativa_evento` + `_crise_alerta_pendente = True`
2. `proximo_passo()` intercepta: `_crise_alerta_exibida = False` → mostra alerta (overlay `game_over.html`, botão ATENDER)
3. Jogador clica ATENDER: `_crise_alerta_exibida = True` → na próxima request, limpa flags e exibe evento de crise
4. Jogador resolve → vitória (impactos aplicados) ou derrota (`game_over_forcado = True`)
5. Segunda ocorrência da mesma crise → game over automático

**Estados no `motor.estado` envolvidos:**
- `crise_ativa_evento` — dict do evento de crise ativo
- `crise_ativa_id` — ID string da crise
- `_crise_alerta_pendente` — bool: alerta pendente de exibição
- `_crise_alerta_exibida` — bool: alerta já mostrado, aguarda ATENDER
- `crises_usadas` — list: IDs de crises já disparadas
- `game_over_forcado` — bool: derrota imediata

---

## BALANCEAMENTO DINÂMICO

- **`pressao`** (1.0–2.0): amplifica deltas negativos quando o jogador está confortável (5/5 métricas seguras → +0.1), recua quando está em dificuldade (≤2/5 → -0.1).
- **`dificuldade_mult`** (×0.6/×1.0/×1.5): VHS/BETA/LASER DISC.
- **`_METRICAS_INVERSAS = {"stress"}`**: delta positivo de stress é tratado como "ruim" para fins de pressão.

---

## FALAS LLM — MECANISMO

1. **Pool hit** (Firestore): renderização instantânea, `typeText` com a fala.
2. **Pool miss (1999)**: placeholder SSE → `/api/fala-stream` → Gemini streaming → salva no pool.
3. **Pool miss (2026)**: `gerar_fala()` síncrono → pool.
4. **LLM falhou** (`LLMFallbackError`): usa `argumento` do script, NÃO salva no pool, loga erro.

**Agentes e `max_tokens`:**
| Agente | Temperature | max_tokens |
|---|---|---|
| Leila | 0.49 | 110 |
| Maurício | 0.31 | 110 |
| Marcos | 0.31 | 110 |
| Vagner | 0.40 | 100 |
| Vagner (financeiro) | 0.10 | 80 |

Todos os agentes têm instrução: **"CRÍTICO: escreva frases curtas e SEMPRE termine com um ponto final."**

---

## MEMÓRIA NARRATIVA — FLAGS

`estado["flags"]` persiste entre eventos. Flags escritas por `escreve_flags` nos sub-eventos de 1999, lidas como `[Memória] ...` nos eventos 2026.

| Flag | Gerada em | Efeito em 2026 |
|---|---|---|
| `mauricio_saiu` | Dia5-C2 | Substitui Maurício por Marcos em todos os eventos |
| `acervo_cult_comprado` | DiaX-A | Lembrete em cinemateca e clone retro |
| `acervo_cult_negado` | DiaX-B | Lembrete negativo nos mesmos eventos |
| `acervo_cult_consignado` | DiaX-B2 | Consignação: 50% por locação, zero upfront |
| `leila_puniu_cliente` | DiaW-A | Lembrete de rigor na autenticidade |
| `leila_absorveu_prejuizo` | DiaW-B | Lembrete de flexibilidade |
| `priorizou_faturamento` | DiaY-A | Histórico de atender clientes de alto ticket |
| `priorizou_tracao` | DiaY-B | Histórico de priorizar volume jovem |
| `acervo_dublado` | DiaV-A | Estratégia comercial |
| `acervo_legendado` | DiaV-B | Aposta cultural |

---

## WORMHOLE — VIDEO

`static/video/wormhole.mp4` — H.264 Main L3.1, yuv420p, 720×1280, AAC stereo.

**Fix aplicado:** remuxado com `-movflags faststart` (moov atom no início). Necessário para streaming mobile.

**Fallback de autoplay mobile:** se `NotAllowedError` → tenta muted. Se muted falhar → `dispatchEvent(ended)` → avança.

---

## EVENTOS 1999 — CAMPO DE NOMES

Todos os eventos usam os campos canônicos que o engine lê:

| Campo | Usado por |
|---|---|
| `pushback_vagner` | `formatar_para_frontend()` linha 124 — texto do NPC após escolha da rota |
| `resolucao_agente` | `processar_escolha()` — tréplica do NPC após sub-opção |
| `resolucao_vagner` | idem (fallback legacy) |
| `argumento_gerente` | fallback de tréplica quando LLM falha |

> ⚠️ Campos `pushback_leila`, `pushback_mauricio`, `resolucao_leila` etc. eram bugs — **já corrigidos** (renomeados para os canônicos via script em maio/2026).

---

## REGRAS DE TRABALHO

- Postura **Staff/Senior Software Engineer + Arquiteto**.
- Correções **cirúrgicas**: mínimo de linhas alteradas.
- **Sem refatoração oportunista**.
- Em caso de dúvida: **perguntar antes de alterar**.
- Economizar tokens: pedir o documento/código quando precisar.

---

## ARQUIVOS-CHAVE E SUAS RESPONSABILIDADES

| Arquivo | O que faz |
|---|---|
| `app.py` | Rotas Flask, serialização de sessão, `_verificar_e_injetar_crise()` |
| `src/decision_pipeline.py` | Pipeline stateless: Hydrate→FSM→Crisis→Commit |
| `src/narrative_director.py` | `proximo_passo()`: roteamento principal + interceptação de crise/alerta |
| `src/renderer_mixin.py` | `_renderizar_gameplay()`, `_renderizar_crise_alerta()`, `_renderizar_game_over()` |
| `src/engine.py` | `processar_escolha()`, `formatar_para_frontend()`, `_atualizar_pressao()`, `calcular_perfil()` |
| `src/agents.py` | `gerar_fala()`, `LLMFallbackError`, pool Firestore |
| `src/prologo_mixin.py` | `_orquestrar_encruzilhada_2026()` (4 passos: narrador → discurso → opções → rota) |
| `data/game_over.json` | 6 eventos de crise com ultimatos, sub-opções e resultados |
| `data/eventos_1999.json` | 12 eventos de 1999 com rotas, pushbacks e impactos |
| `static/js/ui_effects.js` | `playVideo()` com fallback muted, `esperarVideo()` com fallback 10s |
| `templates/game_over.html` | Overlay dramático reutilizado por alerta (ATENDER) e game over (RECONECTAR) |
