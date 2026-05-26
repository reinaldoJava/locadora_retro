# HANDOFF — Locadora Retrô

Documento de continuidade entre sessões. Lê este arquivo + `DEEP_DIVE.md` antes de continuar.

---

## CONTEXTO DO PROJETO

Jogo narrativo web (Flask + HTMX + JS módulos) ambientado em uma locadora de filmes em 1999, com salto temporal para 2026. Três NPCs como barras vitais:

- **Maurício** (Integridade do Acervo)
- **Leila** (Tração & Hype)
- **Vagner** (Stress Operacional — invertida)

Mais o **Caixa** (recurso material). Detalhes completos do design em `DEEP_DIVE.md` (raiz do workspace Cowork, não no repo).

---

## STACK / ARQUITETURA REAL DO CÓDIGO

- **Backend**: Flask (`app.py`). Sessão guarda o estado serializado do `DiretorNarrativo`.
- **Orquestrador narrativo**: `src/narrative_director.py` (`DiretorNarrativo`). Decide qual template renderizar e quais `ui_commands` mandar para o frontend via header `HX-Trigger`.
- **Engine de regras**: `src/engine.py` (não inspecionado em profundidade ainda).
- **Frontend**: HTMX 1.9.10 + módulo ES `static/js/motor_shell.js`. Comandos UI vêm do backend como JSON no header `HX-Trigger` e são despachados por um `uiActionMap` (`typeText`, `animacaoTerminal`, `playAudio`, `loopAutomatico`, `esperarVideo`, `playVideo`, `showElementById`).
- **Áudio**: `static/js/audio_utils.js` + `src/audio_config.py`. Sons de tecla, click, BGM com fade.
- **Templates principais**:
  - `templates/intro.html` — entrada (`/`), input do nome do jogador.
  - `templates/intro_slide.html` — slides da intro.
  - `templates/cinematic_transition_placeholder.html` — tela "SISTEMA CARREGADO" + botão `#btn-iniciar-sistema`.
  - `templates/cinematic_transition_animation_placeholder.html` — overlay do GIF `terminal_bg_shutdown.gif`.
  - `templates/game_ui.html` — UI do gameplay.
  - `templates/cinematic_1999_to_2026.html` — virada de era.
  - `templates/index.html` — fallback (rota `/jogo`), **não é o fluxo principal**.

---

## FLUXO DE CENAS REAL (END-TO-END)

```
GET /                         → intro.html  (input do nome)
POST /api/iniciar-intro       → iniciar_intro() → renderiza primeiro slide em #intro-container
POST /api/avancar-intro-slide → avancar_intro_slide() → próximo slide; no último, chama start_game_transition
  → start_game_transition(): _initial_game_transition_step = 1
      → renderiza cinematic_transition_placeholder.html (SISTEMA CARREGADO + botão escondido)
      → HX-Trigger: typeText("SISTEMA CARREGADO") → ao terminar: showElementById("btn-iniciar-sistema")

[USER CLICA EM "INICIAR SISTEMA"]
  → delegated click handler em motor_shell.js → htmx.ajax POST /api/transicao-para-game-1999 (target: body, swap: innerHTML)
  → start_game_1999_sequence(): _initial_game_transition_step = 2
      → renderiza cinematic_transition_animation_placeholder.html (overlay do GIF)
      → HX-Trigger: animacaoTerminal(tempo_ms=3000) + playAudio(trilha 1999)

[3000ms depois]
  → setTimeout dispara CustomEvent 'animacao_terminal_concluida'
  → handler posta /api/animacao-concluida
  → handle_animacao_concluida() → _initial_game_transition_step = 3 → proximo_passo()
      → step 3: renderiza game_ui.html (gameplay 1999)

[gameplay 1999 → vira para 2026]
  → _orquestrar_virada_2026() com 12 passos cinematográficos (contagem regressiva, parabéns, terminal, wormhole video, carrega era 2026)
```

---

## BUG RESOLVIDO NESTA SESSÃO

**Sintoma:** após clicar em "INICIAR SISTEMA", o `terminal_bg_shutdown.gif` não aparecia.

**Causa raiz (dois pontos compondo o bug):**

1. Template `templates/cinematic_transition_animation_placeholder.html` renderizava o `<div id="terminal-overlay">` já com `class="layout-oculto"`. A regra `#terminal-overlay.layout-oculto` em `static/css/style.css` (especificidade 110 + `!important`) aplicava `visibility: hidden`. Quando o JS removia a classe, a transition `visibility 1.19s` mantinha o elemento invisível (visibility é propriedade discreta; comportamento depende do navegador e da spec).

2. O mesmo bloco CSS tinha o typo `opacity: 10` (clampa para 1). Como o estado base do `#terminal-overlay` também é `opacity: 1`, não havia mudança de opacity para a transition "puxar" — restava só a transition de visibility (a problemática). Comentário no CSS dizia "Fade out", confirmando que era typo.

**Fix aplicado (2 edits):**

- `templates/cinematic_transition_animation_placeholder.html`: removido `class="layout-oculto"` do `<div id="terminal-overlay">`. O div nasce visível assim que entra no DOM.
- `static/css/style.css` linha 313: `opacity: 10` → `opacity: 0`. Fade-out real (1 → 0) ao final dos 3000ms quando JS recoloca a classe.

Nenhum código JS ou Python foi alterado.

---

## DEFINIÇÕES AINDA PENDENTES (de DEEP_DIVE.md seção 12)

1. Caixa inicial e custos numéricos das tasks
2. Quantidade de dias em 1999 e 2026
3. Quantas variações de game over específicas
4. Mecânica do "loop temporal" em 2026 (metáfora ou gameplay real)
5. Save/load entre sessões
6. Balanceamento das barras (playtesting)
7. Outros itens em `DEEP_DIVE.md` seção 12

---

## ARQUIVOS TOCADOS NESTA SESSÃO

- `templates/cinematic_transition_animation_placeholder.html` (1 linha)
- `static/css/style.css` (1 linha)
- `HANDOFF.md` (este arquivo — novo)
- `DEEP_DIVE.md` (criado anteriormente na pasta do Cowork, fora do repo)

---

## REGRAS DE TRABALHO QUE O USUÁRIO ESTABELECEU

- Postura de Staff/Senior Software Engineer.
- Sem elogios, sem comentários supérfluos. Foco no que importa.
- Economizar tokens.
- Correções devem ser **cirúrgicas**: o mínimo de linhas alteradas para resolver o problema; nada de refatoração oportunista.
- Pedir contexto adicional (código, console, paths) quando não houver evidência suficiente.

---

## PRÓXIMOS PASSOS PROVÁVEIS

- Validar visualmente o fix do GIF no navegador.
- Continuar implementação/balanceamento das tasks de 1999.
- Definir os itens da seção 12 do `DEEP_DIVE.md`.
- Investigar se existem bugs semelhantes em `#video-wormhole.layout-oculto` (style.css linha ~282) que tam