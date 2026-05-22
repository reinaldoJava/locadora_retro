# 📼 Locadora Retrô: Gerente de Duas Eras

Jogo narrativo web ambientado em uma videolocadora em 1999, com salto temporal para 2026. O jogador assume o papel de gerente e toma decisões que afetam quatro atributos vitais ao longo de 10 dias.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.10+ / Flask |
| Orquestração UI | HTMX 1.9.10 (fragmentos HTML + headers `HX-Trigger`) |
| Frontend | Vanilla JS ES Modules (`motor_shell.js`, `audio_utils.js`, `ui_effects.js`) |
| Templates | Jinja2 |
| IA local | Ollama (`qwen2.5-instruct`) |
| Persistência | Flask Session (estado volátil) + JSON estático (dados do jogo) |
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

### Protocolo HX-Trigger (Backend → Frontend)

O backend envia comandos de UI no header `HX-Trigger` de cada resposta HTMX. O `motor_shell.js` recebe e despacha via `uiActionMap`:

```json
HX-Trigger: {
  "ui_commands": [
    { "action": "typeText",  "args": { "elementId": "system-message", "fullText": "SISTEMA CARREGADO", "speed": 40, "postTypingCommand": { "action": "showElementById", "args": { "elementId": "btn-iniciar-sistema" } } } },
    { "action": "playAudio", "args": ["trilha-sonora-1999", "/static/audio/Game_1999.mp3", 0.3, true] }
  ]
}
```

**Ações disponíveis:** `typeText`, `skipCurrentTyping`, `playAudio`, `fadeOutMusic`, `animacaoTerminal`, `loopAutomatico`, `esperarVideo`, `playVideo`, `showElementById`.

### Arquitetura de Páginas

O jogo usa duas páginas HTML distintas, cada uma com seu container alvo:

| Página | Rota | Container HTMX | Fase |
|---|---|---|---|
| `intro.html` | `GET /` | `#intro-container` | Login + slides da intro |
| `index.html` | `GET /jogo` | `#ui-jogo` | Toda a fase de gameplay |

A transição entre páginas usa `HX-Redirect: /jogo` no último slide da intro, garantindo que `#ui-jogo` exista antes de qualquer conteúdo cinematográfico tentar fazer swap nele.

---

## Fluxo de Cenas (End-to-End)

```
GET /
  └─ intro.html (input do nome do jogador)
       │
       ▼ POST /api/iniciar-intro
  intro_slide.html (slides do elenco, N passos)
       │
       ▼ POST /api/avancar-intro-slide (último slide)
  HX-Redirect: /jogo
       │
GET /jogo  ──► index.html  ──► hx-trigger="load"
       │
       ▼ POST /api/iniciar-game-transition
  cinematic_transition_placeholder.html
  (HX-Trigger: typeText "SISTEMA CARREGADO" → showElementById "btn-iniciar-sistema")
       │
       ▼ [usuário clica INICIAR SISTEMA]  POST /api/transicao-para-game-1999
  cinematic_transition_animation_placeholder.html
  (HX-Trigger: animacaoTerminal 3000ms + playAudio trilha-sonora-1999)
       │
       ▼ POST /api/animacao-concluida
  game_ui.html  ◄──────────────────────────────────────────────┐
  (gameplay 1999: dias 1–6)                                     │
       │                                                        │
       ▼ [virada 1999→2026]  _orquestrar_virada_2026()         │
  cinematic_1999_to_2026.html (12 passos: contagem, terminal,  │
  wormhole, carrega 2026)                                       │
       │                                                        │
       ▼                                                        │
  game_ui.html  (prólogo 2026 → encruzilhada → dias 8–10) ─────┘
       │
       ▼ [score final]
  fim_de_jogo.html  ou  game_over.html
       │
       ▼ [JOGAR NOVAMENTE]  GET /  (reseta sessão)
```

---

## Atributos do Jogo

| Atributo | Descrição | Condição de Game Over |
|---|---|---|
| **Caixa** | Recurso financeiro da locadora | Caixa ≤ 0 |
| **Stress** | Pressão operacional sobre o gerente | Stress ≥ 100 |
| **Acervo** | Integridade e reputação do catálogo | Acervo ≤ 0 |
| **Tração** | Engajamento e hype da clientela | Tração ≤ 0 |

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Reseta estado e renderiza `intro.html` |
| `GET` | `/jogo` | Renderiza `index.html` (auto-dispara `/api/iniciar-game-transition` via `hx-trigger="load"`) |
| `POST` | `/api/iniciar-intro` | Salva nome do jogador, retorna primeiro slide da intro |
| `POST` | `/api/avancar-intro-slide` | Avança slide; no último emite `HX-Redirect: /jogo` |
| `POST` | `/api/iniciar-game-transition` | Inicia a cinemática de entrada (passo 1) |
| `POST` | `/api/transicao-para-game-1999` | Exibe overlay do terminal GIF (passo 2) |
| `POST` | `/api/animacao-concluida` | Notificado pelo frontend ao fim de animações; avança estado |
| `POST` | `/api/interagir` | Processa escolha do jogador e retorna próximo estado do jogo |

---

## Estrutura de Diretórios

```
locadora-retro/
│
├── app.py                           # Rotas Flask + gerenciamento de sessão
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── data/                            # Dados estáticos do jogo (JSON)
│   ├── eventos_1999.json            # 6 eventos do ciclo 1999
│   ├── eventos_2026.json            # Encruzilhada (dia 7)
│   ├── evento_2026_gatilho_rota_A/B/C/D.json  # Eventos dias 8-10 por rota
│   ├── evento_salto_temporal.json   # Prólogo e cinemática da virada
│   ├── intro.json                   # Roteiro dos slides de apresentação
│   ├── inicializacao_game.json      # Estado inicial e equipe
│   ├── game_over.json               # Textos de derrota por condição
│   └── nao_canonico.json            # Textos dramáticos de transição
│
├── src/                             # Lógica de negócio
│   ├── narrative_director.py        # DiretorNarrativo (orquestrador + mixins)
│   ├── renderer_mixin.py            # Renderização de templates de gameplay
│   ├── cinematic_mixin.py           # Cinemática de entrada e virada de era
│   ├── prologo_mixin.py             # Prólogo 2026, encruzilhada e diálogos
│   ├── intro_mixin.py               # Slides de intro e redirect para /jogo
│   ├── engine.py                    # Máquina de estados: atributos e escolhas
│   ├── agents.py                    # Integração Ollama (falas dinâmicas de NPC)
│   ├── audio_config.py              # Configuração centralizada de assets de áudio
│   ├── utils.py                     # Formatação de diálogo e data pt-BR
│   ├── Maps.py                      # Mapeamentos: backgrounds, spotlight por agente
│   ├── main.py                      # Protótipo CLI (testes sem Flask)
│   └── tests/                       # Testes de Engine por dia/rota
│
├── static/
│   ├── css/style.css                # Sistema de temas (tema-a/b/c), efeito CRT
│   ├── js/
│   │   ├── motor_shell.js           # Dispatcher HX-Trigger → uiActionMap
│   │   ├── ui_effects.js            # typeText, animacaoTerminal, controles de vídeo
│   │   └── audio_utils.js           # BGM, SFX, pool de teclas, desbloqueio autoplay
│   ├── audio/                       # Trilhas, efeitos e sons de teclado
│   ├── img/                         # Backgrounds, sprites de personagens
│   └── video/                       # wormhole.mp4 (cinemática de virada)
│
├── templates/
│   ├── intro.html                   # Página de entrada (rota /)
│   ├── index.html                   # Página do jogo (rota /jogo)
│   ├── intro_slide.html             # Fragmento: slide individual da intro
│   ├── cinematic_transition_placeholder.html       # "SISTEMA CARREGADO"
│   ├── cinematic_transition_animation_placeholder.html  # Overlay GIF terminal
│   ├── cinematic_1999_to_2026.html  # Virada de era (countdown + wormhole)
│   ├── game_ui.html                 # UI principal de gameplay
│   ├── fim_de_jogo.html             # Tela de vitória com placar final
│   └── game_over.html               # Tela de derrota
│
└── arquitetura.html / arquitetura.svg  # Diagramas arquiteturais interativos
```

---

## Como Rodar

### Com Docker (recomendado)

**1. Subir os containers:**
```bash
docker-compose up --build
```

**2. Baixar o modelo de IA (nova aba de terminal):**
```bash
docker exec locadora_ollama ollama pull qwen2.5
```

**3. Acessar:**
```
http://localhost:5000
```

### Sem Docker

```bash
pip install -r requirements.txt

# Ollama deve estar rodando localmente na porta 11434
ollama pull qwen2.5

python app.py
```

> `src/main.py` é um protótipo CLI para testar a Engine sem o Flask. Não faz parte do servidor web.
