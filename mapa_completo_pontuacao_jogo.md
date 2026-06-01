# Mapa Completo de Pontuação — Locadora Retrô
**Versão 4.0** | Balanceamento dinâmico (`pressao`), perfis de jogador, sistema de crises reestruturado com alerta intermediário, textos de NPCs corrigidos, wormhole fast-start

---

## Estado Inicial

| Métrica       | Valor Inicial | Crise se…  | Game Over automático | Crise disparada                    |
|---------------|--------------|------------|----------------------|------------------------------------|
| Caixa         | 100          | ≤ 0        | —                    | Vagner descobre saldo zerado       |
| Tração        | 50           | ≤ 10       | —                    | Ultimato da Leila                  |
| Acervo        | 50           | ≤ 20       | —                    | Ultimato do Maurício / Marcos      |
| Stress        | 0            | ≥ 90       | ≥ 150                | Ultimato do Vagner (operacional)   |
| Moral Equipe  | 70           | ≤ 20       | —                    | Ultimato coletivo                  |

> **Regra:** métricas são sempre `max(0, valor)` — não ficam negativas.
> Dificuldade multiplica todos os deltas: VHS ×0.6 · BETA ×1.0 · LASER DISC ×1.5.
> Score final = `(caixa + tração + acervo - stress + moral_equipe) × dificuldade_mult`
> **Pressão dinâmica:** `pressao` (1.0–2.0) amplifica deltas negativos quando ≥3 métricas em zona segura.

---

## Mudanças v4.0 em relação à v3.5

| # | Mudança | Arquivo(s) afetado(s) |
|---|---------|-----------------------|
| 1 | Threshold crise stress: 150 → 90 (game over automático permanece ≥150) | app.py |
| 2 | Balanceamento dinâmico `pressao` (1.0–2.0) amplificando deltas ruins | engine.py |
| 3 | `calcular_perfil()` — 6 arquétipos de jogador | engine.py |
| 4 | Sistema de crises reestruturado: alerta intermediário (`game_over.html`) antes do ultimato | narrative_director.py, renderer_mixin.py |
| 5 | `_crise_alerta_pendente` + `_crise_alerta_exibida` no estado do engine | engine.py, narrative_director.py |
| 6 | DiaX-B2 reescrito: "Ciclo de Vida" → "Consignação" (flag `acervo_cult_consignado`) | eventos_1999.json |
| 7 | `game_over.json`: textos reescritos, Advogado substituído por Vagner, duplicate keys corrigidos | data/game_over.json |
| 8 | 34 campos com nomes errados em eventos 1999 corrigidos (`pushback_leila` → `pushback_vagner` etc.) | eventos_1999.json |
| 9 | `pula_se_flag: mauricio_saiu` adicionado ao DiaV | eventos_1999.json |
| 10 | `GET /reiniciar`: limpa sessão Flask antes de redirecionar para intro | app.py |
| 11 | `wormhole.mp4` remuxado com fast-start (moov atom no início) | static/video/ |
| 12 | Fallback muted para autoplay mobile no playVideo | static/js/ui_effects.js |
| 13 | `max_tokens` aumentado e instrução anti-corte nos agentes LLM | src/agents.py |
| 14 | Encruzilhada 2026: discurso do gerente separado das 4 opções (passo extra) | src/prologo_mixin.py |

---

## Mudanças v3.0 em relação à v2.0

| # | Mudança                                    | Arquivo(s) afetado(s)                         |
|---|--------------------------------------------|-----------------------------------------------|
| 1 | Threshold stress game-over 1000 → 150      | engine.py                                     |
| 2 | Nova métrica `moral_equipe` (início: 70)   | engine.py, renderer_mixin.py, game_ui.html    |
| 3 | Crise de Moral (limiar ≤ 20)              | game_over.json, app.py, narrative_director.py |
| 4 | Escala 2026 normalizada: caixa ÷250        | evento_2026_gatilho_rota_A/B/C/D.json         |
| 5 | Impactos negativos 1999 escalados ×1.5     | eventos_1999.json                             |
| 6 | `moral_equipe` adicionado a decisões-chave | eventos_1999.json + 4 JSONs de 2026           |
| 7 | Score inclui moral_equipe; limiares ajustados | renderer_mixin.py, fim_de_jogo.html        |

---

## Eventos 1999

### Dia 1 — Multa Dona Sônia (Agente: Vagner)
*Cobrar ou perdoar a multa de R$15 de uma cliente fiel.*

| Rota | Sub | Foco                        | Caixa | Tração | Acervo | Stress | Moral |
|------|-----|-----------------------------|------:|-------:|-------:|-------:|------:|
| A    | A1  | Precedente / Cultura        |  +15  |  -15   |   0    |   -5   |   0   |
| A    | A2  | Fluxo de Caixa              |  +30  |  -30   |   0    |    0   |  -5   |
| B    | B1  | LTV — Lifetime Value        |  -15  |  +25   |   0    |    0   |  +5   |
| B    | B2  | Marketing de Comunidade     |  -15  |  +15   |   0    |  -10   |   0   |
| C    | C1  | Custo Afundado / Giro       |  +20  |  +10   |  +15   |    0   |   0   |
| C    | C2  | Psicologia de Consumo       |  +15  |  +20   |   0    |  -10   |   0   |

**Melhor para caixa:** A2 (+30, mas moral -5 e tração -30) · **Melhor para tração:** B1 (+25) · **Melhor geral:** C1 (triplo positivo)

---

### Dia 2 — Comprar Matrix (Agente: Vagner)
*Orçamento de R$2.000: tudo em lançamento, catálogo ou fusão de estoque.*

| Rota | Sub | Foco                        | Caixa | Tração | Acervo | Stress |
|------|-----|-----------------------------|------:|-------:|-------:|-------:|
| A    | A1  | Payback e Desmobilização    |  +20  |  +20   |  -15   |  +15   |
| A    | A2  | Market Share / CAC          |  -15  |  +25   |  +10   |   -5   |
| B    | B1  | Long Tail / Receita Recorr. |    0  |   -8   |  +30   |  -10   |
| B    | B2  | Escassez + Cross-Sell       |  +10  |  -20   |  +20   |  +20   |
| C    | C1  | ROI Extremo / Nicho         |  +15  |  +20   |  +25   |  +30   |
| C    | C2  | Redução de CapEx            |  +30  |  -15   |  +15   |    0   |

**Melhor para caixa:** C2 (+30) · **Melhor para acervo:** B1 (+30) · **Pior para stress:** C1 (+30)

---

### Dia 3 — Blockbuster Chegou (Agente: Vagner)
*Competição direta, diferenciação por nicho ou assinatura mensal.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress |
|------|-----|------------------------------|------:|-------:|-------:|-------:|
| A    | A1  | Dumping de Curto Prazo       |  -45  |  +25   |   -8   |  +30   |
| A    | A2  | Loss Leader / Produto Isca   |  +15  |  +15   |   0    |  +15   |
| B    | B1  | B2B / Lote Institucional     |  +20  |  -15   |  +10   |   -5   |
| B    | B2  | Boutique / Upsell Curadoria  |    0  |   -8   |  +20   |   -5   |
| C    | C1  | Assinatura MRR               |  +25  |  +15   |  +10   |  -10   |
| C    | C2  | Efeito Lock-in               |  +10  |  +30   |   0    |  +20   |

**Maior risco:** A1 (caixa -45, stress +30) · **Melhor para tração:** C2 (+30) · **Melhor para caixa:** C1 (+25)

---

### Dia 4 — Aparelho de DVD (Agente: Vagner)
*Adotar a novidade, recusar ou fazer teste parcial.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress |
|------|-----|------------------------------|------:|-------:|-------:|-------:|
| A    | A1  | Hardware as a Service        |  -30  |  +20   |   0    |  +15   |
| A    | A2  | Efeito Halo / Isca de Tráfego|  -15  |  +25   |  +10   |    0   |
| B    | B1  | Comoditização / P&D Terceiro |    0  |  -15   |   0    |  -20   |
| B    | B2  | Custo de Oportunidade CAPEX  |  +15  |  -15   |  +20   |  -15   |
| C    | C1  | Data Gathering / Pesquisa    |   -8  |  +15   |   0    |  +15   |
| C    | C2  | Ancoragem Psicológica        |   -8  |  +20   |   0    |    0   |

**Melhor para stress:** B1 (-20) · **Melhor para acervo:** B2 (+20) · **Melhor para tração:** A2 (+25)

---

### Dia 5 — Oferta pra Maurício (Agente: Vagner)
*Cobrir proposta da Blockbuster, dar skin in the game ou deixar ele ir.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress | Moral |
|------|-----|------------------------------|------:|-------:|-------:|-------:|------:|
| A    | A1  | Custo de Turnover            |  -30  |  +20   |   0    |  +15   |  +10  |
| A    | A2  | Defesa de Base / NDA Informal|  -15  |  +20   |   0    |  -20   |  +10  |
| B    | B1  | Profit Sharing / PLR         |    0  |  +10   |  +20   |  -20   |  +15  |
| B    | B2  | Intraempreendedorismo        |  -15  |  +20   |  +10   |  -20   |  +10  |
| C    | C1  | Sistematização / Processo    |    0  |  -30   |   0    |  +30   |  -10  |
| C    | C2  | Reestruturação / Demissão    |  +15  |  -30   |  -15   |  -10   |  -25  |

**Melhor para moral:** B1 (+15) · **Pior para moral:** C2 (-25) · **Único positivo triplo:** B1

> ⚠️ **C2 é o gatilho narrativo de maior consequência do jogo.** Além dos impactos de métrica, escreve `mauricio_saiu: true` — Maurício pede as contas para ir à Blockbuster, substituindo-o por **Marcos (Estagiário)** em todos os eventos 2026 subsequentes.

---

### Dia 6 — Layout de Doces (Agente: Maurício)
*Leila quer doces nas prateleiras; Maurício quer organização.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress | Moral |
|------|-----|------------------------------|------:|-------:|-------:|-------:|------:|
| A    | A1  | Psicologia de Consumo        |  +20  |  +10   |   0    |  +15   |  +5   |
| A    | A2  | Matemática de Margem         |  +25  |  -20   |  -15   |  +15   |   0   |
| B    | B1  | Prevenção de Perdas          |    0  |    0   |  +10   |  +22   |   0   |
| B    | B2  | Posicionamento Premium       |  -15  |  +20   |   0    |  -10   |  +5   |
| C    | C1  | Trade Marketing / Permuta    |  +20  |  +10   |   0    |  -20   |  +10  |
| C    | C2  | Teste A/B de Baixo Custo     |    0  |  +15   |   0    |  +15   |   0   |

**Melhor equilíbrio:** C1 (caixa +20, tração +10, stress -20, moral +10)

---

### Dia 12 — Fita Mastigada do Roberto (Agente: Leila)
*Cliente VIP danificou a fita. Cobrar, perdoar ou resolver administrativamente.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress |
|------|-----|------------------------------|------:|-------:|-------:|-------:|
| A    | A1  | Análise Técnico-Visual       |  +50  |  -15   |  +20   |  +15   |
| A    | A2  | Divisão Amigável de Prejuízo |  +25  |   +5   |  +20   |    0   |
| B    | B1  | Fidelização / Clube Ouro     |  +35  |  +20   |  -15   |   -5   |
| B    | B2  | Venda Casada / Combo Culpa   |  +30  |  +15   |  -15   |    0   |
| C    | C1  | Garantia com Distribuidora   |    0  |  +10   |  +10   |   +8   |
| C    | C2  | Fundo de Provisão p/ Quebras |    0  |   +5   |  +20   |   -5   |

**Maior caixa:** A1 (+50) · **Melhor equilíbrio:** A2 · **Melhor para acervo:** A1/A2/C2 (+20)

---

### Dia X — Curadoria do Acervo (Agente: Maurício)
*Colecionador oferece lote raro (Kubrick, Kurosawa, Hitchcock) por R$100. Orçamento apertado.*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress | Moral |
|------|-----|------------------------------|------:|-------:|-------:|-------:|------:|
| A    | A1  | Nicho Premium                |  -20  |   +5   |  +20   |    0   |  +10  |
| A    | A2  | Parceria com Universitários  |  -20  |  +15   |  +15   |    0   |  +5   |
| B    | B1  | Custo de Oportunidade        |    0  |  +10   |   -5   |    0   |  -10  |
| B    | B2  | Consignação (50% por locação)|    0  |   +5   |   +5   |    0   |  -5   |

**Rota A:** investe em prestígio, custa caixa mas ganha acervo e moral. **Rota B:** sem custo financeiro mas moral sofre. **B2 (Consignação):** zero desembolso, lote exposto com split de 50% por locação — escreve flag `acervo_cult_consignado`.

---

### Dia Y — Impasse do Matrix (Agente: Leila)
*Sistema duplicou reserva da última cópia de Matrix: Dr. Armando (ticket alto) vs. Marcos (grêmio escolar).*

| Rota | Sub | Foco                         | Caixa | Tração | Acervo | Stress | Moral |
|------|-----|------------------------------|------:|-------:|-------:|-------:|------:|
| A    | A1  | Proporção de Receita / LTV   |    0  |  -15   |    0   |   +5   |  -5   |
| A    | A2  | Compensação Imediata         |  -10  |    0   |   -5   |   -5   |  +10  |
| B    | B1  | Marketing de Defensores      |    0  |  +15   |    0   |   +5   |  -5   |
| B    | B2  | Valorização Alternativa      |   -5  |  +10   |    0   |   -5   |  +15  |

**Melhor equilíbrio:** B2 (tração +10, stress -5, moral +15 pelo custo mínimo de -5 caixa). **Pior para tração:** A1 (-15).

---

## Eventos 2026 — Escala normalizada (caixa ÷250)

### Rota A — Estúdio de Conteúdo

| Evento               | Opção | Foco                          | Caixa | Tração | Acervo | Stress | Moral |
|----------------------|-------|-------------------------------|------:|-------:|-------:|-------:|------:|
| Malu2000             | A3    | Sell-Out                      |  +60  |  +20   |  -40   |  +10   |  -15  |
| Malu2000             | A4    | Recusa Premium                |    0  |  -20   |  +40   |  -10   |  +10  |
| Malu2000             | A5    | Cenografia Inteligente        |  +60  |  +10   |  +10   |  +30   |  +5   |
| Feira Geek (ZZXP)    | A6    | Estande Básico                |  -12  |  +30   |   0    |  +10   |  +5   |
| Feira Geek (ZZXP)    | A7    | Estande Premium               |  -32  |  +80   |   0    |  +40   |  +10  |
| Feira Geek (ZZXP)    | A8    | Parceria Zodak                |  +16  |  +60   |   0    |  +20   |  +10  |
| Zinta Originals      | A9    | Licenciar a Marca             |  +50  |  +20   |  -10   |  +10   |  -15  |
| Zinta Originals      | A10   | Licença Não Exclusiva         |  +28  |  +10   |   0    |   +5   |  +5   |
| Zinta Originals      | A11   | Recusa / Série Própria        |  -15  |  +30   |  +20   |  +25   |  +15  |
| Angel Investor       | A12   | Aceitar 30% Equity            |  +60  |  +30   |  -10   |  +40   |  -10  |
| Angel Investor       | A13   | Negociar 15% Equity           |  +30  |  +15   |   0    |  +20   |  +5   |
| Angel Investor       | A14   | Recusar / Independência       |    0  |  +10   |  +20   |  -15   |  +15  |

---

### Rota B — Liquidação Premium

| Evento              | Opção | Foco                          | Caixa | Tração | Acervo | Stress | Moral |
|---------------------|-------|-------------------------------|------:|-------:|-------:|-------:|------:|
| Mercado Livre       | B1    | eBay / Colecionador           |   +3  |    0   |  -10   |  +30   |  +5   |
| Mercado Livre       | B2    | Galeria de Arte Y2K           |   +8  |  -10   |  +20   |  -10   |  +15  |
| Mercado Livre       | B3    | Mystery Box                   |   +4  |  +40   |  -30   |  +10   |  -10  |
| Autenticidade       | B4    | Certificação Total            |   -8  |  +20   |  +40   |  +10   |  +10  |
| Autenticidade       | B5    | Disclaimer / Velocidade       |  +10  |  -20   |  -20   |  +20   |  -10  |
| Autenticidade       | B6    | Anti-Scalper                  |   +3  |  +40   |  +10   |  -10   |  +10  |
| Cinemateca          | B7    | Venda Total                   |  +40  |  +15   |  -40   |  -10   |  +5   |
| Cinemateca          | B8    | Venda Parcial / Núcleo        |  +20  |  +10   |  +10   |    0   |  +10  |
| Cinemateca          | B9    | Comodato / Parceria Cultural  |    0  |  +25   |  +20   |  +10   |  +15  |
| Receita Federal     | B10   | Pagar Tudo / Compliance       |  -18  |   +5   |   0    |  -15   |  +5   |
| Receita Federal     | B11   | Simples Retroativo            |   -9  |   +5   |   0    |   -5   |  +5   |
| Receita Federal     | B12   | REFIS + Reestruturação        |   -2  |  +15   |   0    |  +20   |  +10  |

---

### Rota C — Túnel do Tempo / Detox

| Evento          | Opção | Foco                          | Caixa | Tração | Acervo | Stress | Moral |
|-----------------|-------|-------------------------------|------:|-------:|-------:|-------:|------:|
| Detox Digital   | C1    | White Glove                   |   +6  |  +10   |  -20   |  +40   |  +5   |
| Detox Digital   | C2    | Cabines In-Store              |   +1  |  +10   |  +30   |  -20   |  +10  |
| Detox Digital   | C3    | B2B Corporativo               |  +12  |  -10   |  +10   |  +10   |   0   |
| Games Retrô     | C4    | Parceria Carlos               |   +5  |  +30   |  +10   |  +10   |  +5   |
| Games Retrô     | C5    | Área Própria                  |  -20  |  +50   |  +20   |  +30   |  +5   |
| Games Retrô     | C6    | Anunciar Primeiro             |    0  |  +20   |   0    |  -10   |  +5   |
| RetroZone Clone | C7    | Guerra de Preços              |  -10  |  +20   |   0    |  +25   |  -5   |
| RetroZone Clone | C8    | Inovar / Clube do Diretor     |   -5  |  +30   |  +15   |  +10   |  +15  |
| RetroZone Clone | C9    | Parceria / Divisão Território |   +5  |  +10   |   0    |  -10   |  +5   |
| Escola Dom Bosco| C10   | Aceitar + Maurício Monitor    |   +6  |  +20   |   +5   |  +15   |  +10  |
| Escola Dom Bosco| C11   | Escola Vem até a Locadora     |   +4  |  +25   |   0    |  +10   |  +10  |
| Escola Dom Bosco| C12   | Kit Educativo Recorrente      |   +3  |  +15   |  -10   |  +10   |  +5   |

---

### Rota D — Cine-Pub

| Evento             | Opção | Foco                          | Caixa | Tração | Acervo | Stress | Moral |
|--------------------|-------|-------------------------------|------:|-------:|-------:|-------:|------:|
| Cine-Pub           | D1    | Cine-Clube Intelectual        |   +2  |  +10   |  +40   |  -10   |  +10  |
| Cine-Pub           | D2    | Festa MTV Unplugged           |   +8  |  +40   |  -30   |  +40   |  -5   |
| Cine-Pub           | D3    | Hub B2B Podcasters            |   +5  |  +20   |  +10   |  +10   |  +5   |
| Banda (Crise)      | D4    | DJ Trash 80                   |   +5  |  +20   |   0    |  -10   |   0   |
| Banda (Crise)      | D5    | The Sluggs / Anos 90          |   -2  |  +50   |   0    |  +30   |  +10  |
| Banda (Crise)      | D6    | Maurício Narra ao Vivo        |   +2  |  +30   |  +20   |  -20   |  +15  |
| Alvará em Risco    | D7    | Isolamento Acústico           |   -8  |  +20   |   0    |  +15   |  +5   |
| Alvará em Risco    | D8    | Sarau Privado p/ Vizinho      |   -2  |  +15   |   +5   |  -15   |  +15  |
| Alvará em Risco    | D9    | Temporada Intimista           |   -5  |   +5   |  +10   |  -20   |   0   |
| Premiere Karla A.  | D10   | Desmonte Temporário           |   +8  |  +25   |   -5   |  +20   |  -5   |
| Premiere Karla A.  | D11   | Prateleiras como Cenografia   |   +8  |  +30   |  +10   |  +10   |  +15  |
| Premiere Karla A.  | D12   | Co-Autoria / Parceria         |   +5  |  +20   |  +10   |   +5   |  +10  |

---

## Impactos das Crises (Resolução)

### Se o jogador VENCE a crise:

| Crise                    | Recompensa                       | Penalidade  |
|--------------------------|----------------------------------|-------------|
| Leila (Tração)           | Tração +40 (cap 100)            | Caixa ×0.80 |
| Maurício (Acervo)        | Acervo +30 (cap 100)            | Stress -10  |
| Vagner (Stress)          | Stress -60                      | Caixa -20   |
| Advogado (Caixa)         | Caixa +40                       | Tração -15  |
| Coletivo (Moral Equipe)  | Moral Equipe +30 (cap 100)      | Caixa -10   |

### Se o jogador PERDE a crise:
Resultado direto = **GAME OVER**.
Segunda ocorrência da mesma crise = **GAME OVER automático** (sem diálogo).

---

## Limiares de Classificação Final (v3.0)

Score = `(caixa + tração + acervo - stress + moral_equipe) × dificuldade_mult`

| Classificação | Score mínimo |
|---------------|-------------|
| LENDÁRIO      | ≥ 400       |
| EXCELENTE     | ≥ 300       |
| BOM           | ≥ 200       |
| REGULAR       | ≥ 130       |
| DIFÍCIL       | < 130       |

> Base de partida: 100+50+50-0+70 = **270** pontos.
> Para LENDÁRIO em BETA (×1.0): acumular +130 líquido. Para VHS (×0.6): precisa de base 667 → inalcançável, teto real ~EXCELENTE.

---

## Análise de Alcance das Crises (v3.0)

### Crise do Vagner — Stress ≥ 150 (início: 0)
Pior caminho (máximo de stress acumulável em 7 eventos):
Dia2-C1(+30) + Dia3-A1(+30) + Dia5-C1(+30) + Dia6-B1(+22) + Dia4-A1(+15) + Dia4-C1(+15) + Dia12-A1(+15) = **+157 → CRISE** (7 escolhas ruins)

### Crise da Moral — Moral Equipe ≤ 20 (início: 70)
Pior caminho: Dia5-C2(-25) + Malu2000-A3(-15) + Mercado Livre-B3(-10) + Dia1-A2(-5) = **-55 → moral = 15 → CRISE** (4 escolhas ruins)

### Crise da Leila — Tração ≤ 10 (início: 50)
Pior caminho: Dia1-A2(-30) + Dia2-B2(-20) = **tração = 0 → CRISE** (apenas 2 eventos!)
Caminho alternativo com diaY: Dia1-A2(-30) + DiaY-A1(-15) = **tração = 5 → CRISE** (2 eventos)
> ⚠️ Continua muito fácil de acionar. Se quiser tornar mais difícil, aumentar limiar para ≤15 ou reduzir Dia1-A2 tração para -20.

### Crise do Maurício — Acervo ≤ 20 (início: 50)
Pior caminho: Dia2-A1(-15) + Dia3-A1(-8) + Dia5-C2(-15) + Dia6-A2(-15) = **-53 → acervo = 0 → CRISE** (4 escolhas ruins)

### Crise do Advogado — Caixa ≤ 0 (início: 100)
Pior caminho original: Dia3-A1(-45) + Dia4-A1(-30) + Dia5-A1(-30) = **-105 → caixa = 0 → CRISE** (3 escolhas ruins)
Caminho com diaX: DiaX-A1(-20) + Dia3-A1(-45) + Dia4-A1(-30) = **-95 → caixa = 5** (não dispara, mas fica crítico)
> DiaX entra como pressão adicional de caixa, não cria atalho sozinho para a crise.

---

## Sistema de Memória Narrativa — Flags (v3.3)

`estado["flags"]` é um dict persistente na sessão. Flags são escritas por sub-opções via `escreve_flags` e lidas por eventos 2026 via `memo_se_flags` para exibir contexto histórico antes da decisão.

### Flags geradas em 1999

| Flag                    | Gerada em     | Condição                                                  |
|-------------------------|---------------|-----------------------------------------------------------|
| `leila_puniu_cliente`   | diaW (A1/A2)  | Locadora confrontou e cobrou pelo cliente da fita trocada |
| `leila_absorveu_prejuizo` | diaW (B1/B2) | Locadora absorveu perda para preservar relacionamento     |
| `acervo_cult_comprado`  | diaX (A1/A2)  | Lote Kubrick/Kurosawa/Hitchcock adquirido em 1999         |
| `acervo_cult_negado`    | diaX (B1/B2)  | Lote raro recusado em favor de blockbusters               |
| `priorizou_faturamento` | diaY (A1/A2)  | Dr. Armando (ticket alto) preferido sobre Marcos          |
| `priorizou_tracao`      | diaY (B1/B2)  | Marcos (volume jovem) preferido sobre Dr. Armando         |
| `acervo_dublado`        | diaV (A1/A2)  | Estratégia comercial: 80% do estoque em versão dublada    |
| `acervo_legendado`      | diaV (B1/B2)  | Aposta cultural: foco em versões originais legendadas     |
| `mauricio_saiu`         | Dia5-C2       | Maurício pede as contas e vai pra Blockbuster — estagiário substitui |

### Pontes narrativas 1999 → 2026

| Flag ativa               | Evento 2026 afetado          | Efeito no texto                                                     |
|--------------------------|------------------------------|---------------------------------------------------------------------|
| `leila_absorveu_prejuizo` | evento_autenticidade_2026   | Lembrete: a locadora já cedeu antes — desta vez é público           |
| `leila_puniu_cliente`    | evento_autenticidade_2026    | Lembrete: reputação de rigor construída em 1999                     |
| `acervo_cult_comprado`   | evento_cinemateca_2026       | Lembrete: são exatamente as fitas de 1999 que a Cinemateca quer     |
| `acervo_cult_negado`     | evento_cinemateca_2026       | Lembrete: a ausência do lote de 1999 é notada pelo representante    |
| `acervo_cult_comprado`   | evento_clone_retro_2026      | Lembrete: 27 anos de curadoria não se fotografa e copia             |
| `acervo_cult_negado`     | evento_clone_retro_2026      | Lembrete: o concorrente usa exatamente o argumento que você recusou |
| `acervo_legendado`       | evento_detox_digital         | Lembrete: acervo original reforça o pitch de autenticidade          |
| `priorizou_faturamento`  | evento_detox_digital         | Lembrete: histórico de saber atender clientes de alto ticket        |

### Implementação no engine

- `reset_completo()`: `"flags": {}` inicializado junto ao estado
- `_aplicar_impacto_dinamico()`: loop final sobre `dict_opcao.get("escreve_flags", {})`
- `formatar_para_frontend()`: injeta memos ativos como `[Memória] ...` no topo do `texto_final`
- `_resolver_agente(agente_id)`: troca `ID_Mauricio` → `ID_Marcos` quando `mauricio_saiu` ativo

---

## Estagiário Marcos — Substituição de Agente (v3.4)

Quando `mauricio_saiu: true`, o personagem **Marcos** substitui Maurício em todos os eventos 2026 que teriam `agente_foco: "ID_Mauricio"`. Mesma estrutura de diálogo, outra voz e outra imagem.

### Perfil do Marcos

| Atributo      | Valor                                                              |
|---------------|--------------------------------------------------------------------|
| Idade         | 28 anos                                                            |
| Origem        | Afro-descendente, periferia                                        |
| Referências   | Drum and bass, raves, Sega                                         |
| Cinefilia     | Como Maurício, mas mais flexível — sem pedantismo                  |
| Visão         | Pensa na locadora como um todo (acervo, caixa e equipe juntos)     |
| Temperature   | 0.38 (entre Leila 0.42 e Maurício 0.31)                           |

### Pipeline de substituição — pontos cobertos

| Arquivo             | Ponto                             | Mecanismo                                        |
|---------------------|-----------------------------------|--------------------------------------------------|
| `engine.py`         | `formatar_para_frontend()`        | `_resolver_agente()` no campo `personagem`       |
| `engine.py`         | `processar_escolha()` — réplica   | `_resolver_agente()` em `agente_foco_default`    |
| `engine.py`         | `processar_escolha()` — tréplica  | `_resolver_agente()` em `agente_atual`           |
| `renderer_mixin.py` | Pool miss situação inicial        | `_resolver_agente()` em `agente_id`              |
| `renderer_mixin.py` | Réplica LLM síncrona              | `_resolver_agente()` em `agente_id`              |
| `renderer_mixin.py` | Tréplica LLM síncrona             | `_resolver_agente()` em `"ID_" + agente_atual`   |
| `renderer_mixin.py` | `_orquestrar_dialogo_evento()`    | `_resolver_agente()` por diálogo em 2026         |
| `app.py`            | `/api/fala-stream` (SSE)          | `_resolver_agente()` em `agente_id`              |
| `src/Maps.py`       | `IMG_PERSONS`                     | `"Marcos": "marcos"` — resolve `marcos.webp`     |
| `src/agents.py`     | `PROMPTS` + `_FALLBACK`           | Entry `ID_Marcos` com system prompt e fallback   |

> **Asset pendente (responsabilidade do dev):** `/static/img/marcos.webp`

---

## Rebalanceamento de Opções Dominantes (v3.3)

Problema identificado: **Dragon Age Problem** — opções "diplomáticas/criativas" eram vitórias puras em 3–4 eixos simultaneamente. Toda decisão precisa de um custo real.

| Opção | Métrica alterada | Antes | Depois | Justificativa                                                  |
|-------|-----------------|-------|--------|----------------------------------------------------------------|
| D11   | stress          | +10   | +25    | Negociar com a diretora é arriscado — incerteza do resultado   |
| D11   | caixa           | +8    | +6     | Karla aceitou mas exigiu desconto pela adaptação criativa      |
| D8    | stress          | -15   | +15    | Diplomacia com vizinho é incerta — pode não funcionar          |
| D8    | caixa           | -2    | -3     | Custo da noite privada + incerteza de resultado                |
| C9    | stress          | -10   | +10    | Contatar concorrente é incerto e emocionalmente desgastante    |
| C9    | caixa           | +5    | +3     | Caixa menor — o "acordo" ainda não gerou retorno concreto      |
| C9    | moral_equipe    | +5    | 0      | Leila fica sem saber se fez certo em se aproximar do clone     |
| B8    | stress          | 0     | +15    | Negociar venda parcial com a Cinemateca gera fricção real      |

**Regra de balanceamento aplicada:** nenhuma opção pode ser superior em ≥3 eixos simultâneos sem ter pelo menos 1 eixo de custo relevante.

---

## Resumo das Mudanças por Versão

| Versão | Principais mudanças                                                                         |
|--------|---------------------------------------------------------------------------------------------|
| v1.0   | Primeira versão                                                                             |
| v2.0   | Fix caixa -3000/+2000 nas crises; acervo em Dia3-A1 e Dia5-C2                             |
| v3.0   | Stress 1000→150; moral_equipe (início 70, crise ≤20); caixa 2026 ÷250; negativos 1999 ×1.5; nova crise moral; score e limiares atualizados |
| v3.1   | 2 novos eventos 1999: DiaX (curadoria Maurício) e DiaY (impasse Matrix Leila); fix caixa -100→-20 em DiaX; remoção do campo inválido `fidelidade` em DiaY |
| v3.2   | 8 novos eventos 2026 (2 por rota): A — Zinta Originals + Angel Investor; B — Cinemateca + Receita Federal; C — Clone RetroZone + Escola Dom Bosco; D — Alvará em Risco + Premiere Karla Aiala |
| v3.3   | Sistema de flags (memória narrativa 1999→2026); `escreve_flags` em diaW/X/Y/V; `memo_se_flags` em 4 eventos 2026; fix `fidelidade` restante em diaW (A1, A2, B1, B2); rebalanceamento de D11/D8/C9/B8 (Dragon Age Problem) |
| v3.4   | Estagiário Marcos: perfil LLM, flag `mauricio_saiu` em Dia5-C2 (voluntário, não demitido), `_resolver_agente()` no engine, substituição em 8 pontos do pipeline (renderer, SSE, Maps, agents) |
| v3.5   | Rename `mauricio_demitido` → `mauricio_saiu` em engine.py, mapa e JSON; auditoria geral (arquitetura, segurança, testes) |
