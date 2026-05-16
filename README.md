
---

```markdown
# 📼 Documento de Arquitetura: Locadora Retrô (MVP)

## 1. Visão Geral do Sistema
O MVP do jogo **Locadora Retrô** é uma experiência narrativa de gerenciamento ambientada em uma locadora de vídeo na virada do milênio (1999/2026). O jogador assume o papel do **Gerente** e deve equilibrar as demandas da equipe, a integridade do acervo e o fluxo de caixa.

**Evolução da Arquitetura:** A aplicação foi inicialmente desenhada para rodar no Terminal (CLI), mas evoluiu para um sistema Web robusto com interface inspirada em Visual Novels, sustentada por um motor de regras matemático e diálogos dinâmicos gerados por IA (Agentes).

---

## 2. Stack Tecnológica (Tech Stack)
* **Backend:** Python 3.10+ com **Flask**.
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla) com Fetch API nativa.
* **Integração de IA (Local):** Agentes alimentados pelo **Ollama** rodando localmente (Modelo `llama3.2:1b`).
* **Armazenamento de Dados:** Ficheiros `.json` (Matriz de Eventos e Interstícios).
* **Infraestrutura/DevOps:** Docker e Docker Compose.

---

## 3. Estrutura de Diretórios
A infraestrutura foi reorganizada para suportar a nova interface Web sem perder a modularização do motor de regras.

```text
locadora_retro/
│
├── app.py                      # PONTO DE ENTRADA ATUAL: Roteador principal e APIs Flask
├── docker-compose.yml          # Orquestração dos containers (Web App + Ollama)
├── requirements.txt            # Dependências do projeto (Flask, requests, etc.)
│
├── data/                       # Camada de Dados (Base de Dados Local)
│   ├── eventos.json            # Matriz com dias, contextos e impactos matemáticos
│   └── intersticios.json       # Textos fixos de transição narrativa
│
├── src/                        # Camada de Lógica (Motor do Jogo)
│   ├── main.py                 # ⚠️ (DESCONTINUADO) Antigo ponto de entrada para testes via terminal
│   ├── engine.py               # Gestor de Estado (Atualiza barras, verifica Game Over)
│   └── agents.py               # Prompt Builder e comunicação com o Ollama
│
├── static/                     # Assets Frontend (Públicos)
│   └── img/
│       ├── bg_intro.png, terminal_bg.gif, vhs_insert.gif
│       └── gerente.png, leila.png, mauricio.png, vagner.png
│
└── templates/                  # Views (Onde o Flask lê o HTML)
    ├── intro.html              # Onboarding e apresentação de elenco
    └── index.html              # Jogo principal (Motor de cenas)

```

---

## 4. Principais Funcionalidades do Motor Web

### Onboarding Imersivo (Máquina de Estados)

* **Ato 1 (Terminal):** Interface retrô para captura do nome do jogador.
* **Ato 2 (Transição):** Feedback visual de carregamento (VHS) com sincronização silenciosa via backend para criação de sessão (`Flask Session`).
* **Ato 3 (Apresentação):** Carrossel dinâmico apresentando a equipe com sobreposição 3D (z-index) e injeção do nome do jogador no texto.

### Motor de Diálogos Dinâmico

* **Parser Inteligente:** Lê textos brutos gerados pela IA e identifica automaticamente o emissor (ex: `VAGNER: texto`), buscando a imagem correta sem *hardcoding*.
* **Efeito de Foco (Pergaminho):** O sistema acende o personagem que está falando no momento e ofusca o inativo, mantendo o histórico da conversa na tela.

---

## 5. Endpoints da API (Flask)

* `GET /`: Rota raiz, limpa sessões antigas e renderiza a intro (`intro.html`).
* `GET /jogo`: Rota protegida da engine principal (exige sessão ativa). Renderiza o jogo (`index.html`).
* `POST /api/iniciar-sessao`: Recebe o nome do jogador do frontend e salva na sessão do Flask.
* `GET /api/proximo-evento`: Retorna o JSON com o roteiro processado, personagens e opções do dia.
* `POST /api/escolha`: Processa a decisão tomada pelo jogador, aciona o motor de consequências matemático e gera o próximo contexto via IA.

---

## 6. Como Rodar a Aplicação (Instalação e Execução)

O projeto foi conteinerizado para facilitar a execução local do backend Python em conjunto com a IA do Ollama.

**Nota Importante:** O arquivo `src/main.py` era utilizado apenas para testes básicos via terminal e foi **descontinuado**. Todo o ecossistema agora é inicializado e servido pelo `app.py`.

### Passo a Passo

**1. Construir e subir os containers (Web App + Ollama):**
Na raiz do projeto, execute:

```bash
docker-compose up --build

```

*(Deixe este terminal aberto rodando os logs)*

**2. Baixar o modelo de IA no container do Ollama:**
Abra uma **nova aba de terminal** e execute o comando abaixo para realizar o *pull* do modelo de linguagem:

```bash
docker exec locadora_ollama ollama pull qwen2.5
```

**3. Acessar o Jogo:**
Quando o download do modelo terminar e o Flask estiver rodando, abra o seu navegador de preferência e acesse:

```text
http://localhost:5000

```

**TODO LIST**
- não está aparecendo a transição de 1999 para 2000 e 2026.
- Ajustar os textos de 2026.
- Trocar background de 2026. Um para cada subtipo que a pessoa escolher.
- Aparecer o os scores ao final de cada dia.
- Melhorar a mecânica de score geral do game.
- Fazer com que IA crie mais algumas novas tarefas.
- Fazer um balanceamento melhor de todos os textos do game.