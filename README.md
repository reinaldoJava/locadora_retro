# 🏗️ Documento de Arquitetura e Infraestrutura: Locadora Retrô (MVP)

## 1. Visão Geral do Sistema
O MVP do jogo **Locadora Retrô** é construído sobre uma arquitetura leve, focada na narrativa dinâmica gerada por Inteligência Artificial (Agentes) e sustentada por um motor de regras estático (Matemática do Jogo). 

A aplicação foi desenhada para correr inicialmente no Terminal (CLI), podendo ser facilmente escalada para um frontend web simples (como o Streamlit) no futuro.

---

## 2. Stack Tecnológica (Tech Stack)
* **Linguagem Principal:** Python 3.10+
* **Integração de IA:** API REST (OpenAI GPT-4o-mini, Anthropic Claude ou Google Gemini).
* **Armazenamento de Dados (Local):** Ficheiros `.json` (Matriz de Eventos e Interstícios).
* **Gestão de Variáveis de Ambiente:** `python-dotenv` (para proteger as chaves de API).

---

## 3. Estrutura de Diretórios (Folder Structure)
Para manter o código limpo e modularizado, a infraestrutura deve seguir a seguinte topologia de pastas:

```text
locadora_retro_mvp/
│
├── data/                       # Camada de Dados (Base de Dados Local)
│   ├── eventos.json            # Matriz com os 10 dias, contextos e impactos matemáticos
│   └── intersticios.json       # Textos fixos de transição narrativa (ex: Salto no Tempo)
│
├── src/                        # Camada de Lógica (Motor do Jogo)
│   ├── __init__.py
│   ├── main.py                 # Ponto de entrada (Core Loop do Jogo)
│   ├── engine.py               # Gestor de Estado (Atualiza barras, verifica Game Over)
│   └── agents.py               # Integração com a API da IA (Prompt Builder)
│
├── .env                        # Ficheiro oculto com as credenciais (ex: OPENAI_API_KEY=sk-...)
├── .gitignore                  # Ficheiros ignorados pelo Git (ignorar .env)
├── requirements.txt            # Dependências do projeto (ex: openai, python-dotenv)
└── README.md                   # Documentação do projeto# locadora_retro
