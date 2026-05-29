# 📼 Locadora Retrô — Demo: Video Locadora Simulation

Jogo narrativo web ambientado em uma videolocadora em 1999, com salto temporal para 2026. O jogador assume o papel de gerente e toma decisões que afetam cinco atributos vitais ao longo de múltiplos dias.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.10+ / Flask + Gunicorn (1 worker, 8 threads) |
| Deploy | Google Cloud Run |
| Orquestração UI | HTMX 1.9.10 (fragmentos HTML + headers `HX-Trigger`) |
| Frontend | Vanilla JS ES Modules (`motor_shell.js`, `audio_utils.js`, `ui_effects.js`) |
| Templates | Jinja2 |
| IA | Google Gemini via API (falas dinâmicas dos NPCs) |
| Persistência | Flask Session (estado volátil) + Firestore (pool de falas LLM) + JSON estático |
| Áudio | Web Audio API com cross-fade e pool de sons de teclado |

---

## Arquitetura

### Padrão de Sessão (Stateless HTTP)

O `DiretorNarrativo` é reconstruído a cada request a partir de um dict serializado na sessão Flask. Nenhum objeto Python persiste entre requests.

```
request → _load_diretor_from_data(session['game_state_data'])
             → DiretorNarrativo + Engine reconstruídos
             → lógica executada
             → _extract_data_from_diretor(diretor)
                → session['game_state_data'] atualizado
```

### DiretorNarrativo — Padrão Mixin

`DiretorNarrativo` herda quatro mixins, cada um responsável por um domínio do jogo:

| Mixin | Responsabilidade |
|---|---|
| `RendererMixin` | Renderiza templates: `game_ui.html`, `fim_de_jogo.html`, `game_over.html` |
| `CinematicMixin` | Transição inicial (SISTEMA CARREGADO → INICIAR SISTEMA) e virada 1999→2026 (12 passos) |
| `PrologoMixin` | Prólogo 2026, encruzilhada de rotas e buffer de diálogos sequenciais |
| `IntroMixin` | Carrossel de slides da intro (`/api/avancar-intro-slide`) |

O ponto de entrada único é `proximo_passo(escolha_usuario)`, que roteia para o mixin correto com base no estado atual.

### Pipeline de Gameplay (`decision_pipeline.py`)

Cada request a `/api/interagir` executa o pipeline:

```
Hydrate → FSM (proximo_passo) → Crisis Check → Commit
```

O `GamePipeline` recebe `hydrate_fn`, `commit_fn` e `crisis_fn` por injeção de dependência, mantendo o módulo desacoplado do Flask.

### Protocolo HX-Trigger (Backend → Frontend)

O backend envia comandos de UI no header `HX-Trigger` de cada resposta HTMX. O `motor_shell.js` recebe e despacha via `uiActionMap`:

```json
HX-Trigger: {
  "ui_commands": [
    { "action": "typeText",  "args": { "elementId": "fala-typing-target", "fullText": "...", "speed": 25 } },
    { "action": "playAudio", "args": { "id": "trilha-sonora-1999", "acao": "trocar_trilha", "src": "...", "volume": 0.3 } }
  ]
}
```

**Ações disponíveis:** `typeText`, `skipCurrentTyping`, `playAudio`, `fadeOutMusic`, `animacaoTerminal`, `loopAutomatico`, `esperarVideo`, `playVideo`, `showElementById`.

### Arquitetura de Páginas

| Página | Rota | Container HTMX | Fase |
|---|---|---|---|
| `intro.html` | `GET /` | `#intro-container` | Login + slides da intro |
| `index.html` | `GET /jogo` | `#ui-jogo` | Toda a fase de gameplay |

---

## Fluxo de Cenas (End-to-End)

```
GET /
  └─ intro.html (input do nome do jogador)
       │
       ▼ POST /api/iniciar-intro
  intro_slide.html (slides do elenco)
       │
       ▼ POST /api/avancar-intro-slide (último slide)
  HX-Redirect: /jogo
       │
GET /jogo  ──► index.html  ──► hx-trigger="load"
       │
       ▼ POST /api/iniciar-game-transition
  cinematic_transition_placeholder.html  (SISTEMA CARREGADO)
       │
       ▼ [usuário clica INICIAR SISTEMA]
  cinematic_transition_animation_placeholder.html  (GIF terminal)
       │
       ▼ POST /api/animacao-concluida
  game_ui.html  ◄───────────────────────────────────────┐
  (gameplay 1999: eventos dia1–diaV)                    │
       │                                                 │
       ▼  [virada 1999→2026]                            │
  cinematic_1999_to_2026.html (12 passos:               │
    contagem regressiva, terminal, wormhole.mp4)         │
       │                                                 │
       ▼                                                 │
  Prólogo 2026 → Encruzilhada (4 rotas A/B/C/D)        │
       │                                                 │
  game_ui.html (eventos 2026 por rota) ─────────────────┘
       │
       ▼  [crise detectada]
  game_over.html (alerta — botão ATENDER)
       │
       ▼  [evento de crise: ultimato do NPC]
  game_ui.html  (jogador resolve ou perde a crise)
       │
       ├─ vitória → continua gameplay
       └─ derrota → game_over.html (GAME OVER + RECONECTAR SISTEMA → /reiniciar)
       │
       ▼  [score final]
  fim_de_jogo.html
```

---

## Atributos do Jogo

| Atributo | Início | Crise se… | Crise disparada |
|---|---|---|---|
| **Caixa** | 100 | ≤ 0 | Vagner descobre saldo zerado |
| **Tração** | 50 | ≤ 10 | Ultimato da Leila |
| **Acervo** | 50 | ≤ 20 | Ultimato do Maurício / Marcos |
| **Stress** | 0 | ≥ 90 | Ultimato do Vagner (operacional) |
| **Moral Equipe** | 70 | ≤ 20 | Ultimato coletivo |

> Game over automático: stress ≥ 150 ou `game_over_forcado`. Segunda ocorrência da mesma crise = game over direto.

### Balanceamento Dinâmico

`pressao` (1.0–2.0): multiplicador que amplifica deltas negativos quando o jogador está confortável, e recua quando está em dificuldade. Calculado após cada decisão com base em quantas das 5 métricas estão em zona segura.

### Perfis de Jogador

`calcular_perfil()` classifica o gerente em 6 arquétipos (Executor, Coach, Diplomata, Guerreiro, Curador, Estrategista) com base no padrão de decisões ao longo do jogo.

---

## Sistema de Crises

Fluxo de uma crise:

```
Limiar atingido após escolha do jogador
    → _verificar_e_injetar_crise() seta _crise_alerta_pendente = True
    → Próxima interação: game_over.html — alerta dramático (botão ATENDER)
    → Jogador clica ATENDER: evento de crise (ultimato NPC)
    → Jogador escolhe resposta → vitória ou game over
    → Segunda ocorrência da mesma crise = game over automático
```

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Renderiza `intro.html` |
| `GET` | `/reiniciar` | Limpa sessão Flask e redireciona para `/` |
| `GET` | `/jogo` | Renderiza `index.html` (auto-dispara `/api/iniciar-game-transition`) |
| `POST` | `/api/iniciar-intro` | Salva nome do jogador, retorna primeiro slide |
| `POST` | `/api/avancar-intro-slide` | Avança slide; no último emite `HX-Redirect: /jogo` |
| `POST` | `/api/iniciar-game-transition` | Inicia cinemática de entrada (passo 1) |
| `POST` | `/api/transicao-para-game-1999` | Overlay do terminal GIF (passo 2) |
| `POST` | `/api/animacao-concluida` | Notificado pelo frontend ao fim de animações |
| `POST` | `/api/interagir` | Processa escolha do jogador (pipeline principal) |
| `GET` | `/api/fala-stream` | SSE: streaming da fala do NPC via Gemini |
| `POST` | `/api/salvar_placar` | Persiste score final no Firestore |
| `GET` | `/api/placar` | Retorna ranking dos melhores scores |

---

## Estrutura de Diretórios

```
locadora-retro/
│
├── app.py                           # Rotas Flask + gerenciamento de sessão + injeção de crise
├── Dockerfile
├── requirements.txt
│
├── data/                            # Dados estáticos do jogo (JSON)
│   ├── eventos_1999.json            # 12 eventos do ciclo 1999
│   ├── eventos_2026.json            # Encruzilhada (dia 7)
│   ├── evento_2026_gatilho_rota_A/B/C/D.json  # Eventos por rota 2026
│   ├── evento_salto_temporal.json   # Prólogo e cinemática da virada
│   ├── intro.json                   # Roteiro dos slides de apresentação
│   ├── game_over.json               # 6 eventos de crise (ultimatos dos NPCs)
│   └── inicializacao_game.json      # Estado inicial e equipe
│
├── src/                             # Lógica de negócio
│   ├── narrative_director.py        # DiretorNarrativo + roteamento de cenas
│   ├── renderer_mixin.py            # Renderização de gameplay, crises e game over
│   ├── cinematic_mixin.py           # Cinemática de entrada e virada de era
│   ├── prologo_mixin.py             # Prólogo 2026, encruzilhada e diálogos
│   ├── intro_mixin.py               # Slides de intro
│   ├── engine.py                    # FSM: métricas, escolhas, pressão dinâmica
│   ├── decision_pipeline.py         # Pipeline stateless: Hydrate→FSM→Crisis→Commit
│   ├── agents.py                    # Integração Gemini (falas LLM) + pool Firestore
│   ├── audio_config.py              # Configuração centralizada de áudio
│   ├── Maps.py                      # Mapeamentos: backgrounds, spotlight por agente
│   └── utils.py                     # Formatação de diálogo e data pt-BR
│
├── static/
│   ├── css/style.css                # Sistema de temas (tema-a/b/c), efeito CRT
│   ├── js/
│   │   ├── motor_shell.js           # Dispatcher HX-Trigger → uiActionMap
│   │   ├── ui_effects.js            # typeText, animacaoTerminal, playVideo (fast-start)
│   │   └── audio_utils.js           # BGM, SFX, pool de teclas, desbloqueio autoplay
│   ├── audio/                       # Trilhas e efeitos sonoros
│   ├── img/                         # Backgrounds e sprites de personagens
│   └── video/
│       └── wormhole.mp4             # Cinemática de virada (H.264, fast-start, 5.9MB)
│
├── templates/
│   ├── intro.html                   # Página de entrada (rota /)
│   ├── index.html                   # Página do jogo (rota /jogo)
│   ├── intro_slide.html             # Fragmento: slide individual da intro
│   ├── cinematic_transition_placeholder.html
│   ├── cinematic_transition_animation_placeholder.html
│   ├── cinematic_1999_to_2026.html  # Virada de era (countdown + wormhole)
│   ├── game_ui.html                 # UI principal de gameplay
│   ├── fim_de_jogo.html             # Tela de vitória com placar final
│   └── game_over.html               # Overlay dramático: alerta de crise + game over
│
└── mapa_completo_pontuacao_jogo.md  # Design doc completo de balanceamento
```

---

## Como Rodar Localmente

```bash
pip install -r requirements.txt
python app.py
```

Acesse: `http://localhost:5000`

> **Variáveis de ambiente necessárias:** `GEMINI_API_KEY`, `FIRESTORE_PROJECT_ID` (opcional para pool de falas).
