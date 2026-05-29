#!/usr/bin/env python3
"""
scripts/seed_pool.py
Pré-aquece o pool de falas gerando RUNS variações por chave.

Uso:
    python scripts/seed_pool.py           # 3 variações por chave (padrão)
    python scripts/seed_pool.py --runs 5  # 5 variações por chave

Chaves geradas por evento:
    evt_id                  → situação (fala inicial do NPC)
    evt_id:replica:R        → réplica para cada rota R
    evt_id:treplica:R:S     → tréplica para sub_opcao S da rota R
    evt_id:treplica:O       → tréplica para opcao O (eventos 1999 com opcoes[])
"""

import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents import gerar_fala, adicionar_ao_pool

DATA = ROOT / "data"

EVENT_FILES = [
    "eventos_1999.json",
    "evento_2026_gatilho_rota_A.json",
    "evento_2026_gatilho_rota_B.json",
    "evento_2026_gatilho_rota_C.json",
    "evento_2026_gatilho_rota_D.json",
    "game_over.json",
]


def _load(filename: str) -> list:
    path = DATA / filename
    with open(path, encoding="utf-8") as f:
        dados = json.load(f)
    return list(dados.values()) if isinstance(dados, dict) else dados


def _gerar(pool_key: str, agente_id: str, contexto: str, ano: int,
           temperatura, argumento: str, runs: int) -> None:
    print(f"  {pool_key}", end=" ", flush=True)
    for _ in range(runs):
        fala = gerar_fala(agente_id, contexto, ano, temperatura, argumento=argumento)
        adicionar_ao_pool(pool_key, fala)
        print(".", end="", flush=True)
    print()


def seed_evento(evt: dict, runs: int) -> None:
    evt_id    = evt.get("id", "")
    agente_id = evt.get("agente_foco", "")
    contexto  = evt.get("contexto_ia", "")
    ano       = evt.get("ano", 1999)

    if not evt_id or not agente_id or not contexto:
        return

    print(f"\n[{evt_id}]")

    # 1. Situação — fala inicial do NPC sem argumento
    _gerar(evt_id, agente_id, contexto, ano,
           evt.get("temp_situacao"), argumento="", runs=runs)

    # 2. Rotas principais (1999 e 2026): réplica + tréplica por sub_opcao
    for r_idx, rota in enumerate(evt.get("rotas_principais", [])):
        if "sub_opcoes" not in rota:
            continue

        # Réplica — NPC reage à fala do Gerente ao escolher a rota
        argumento_rep = rota.get("fala_gerente", "")
        _gerar(f"{evt_id}:replica:{r_idx}", agente_id, contexto, ano,
               rota.get("temp_replica"), argumento=argumento_rep, runs=runs)

        # Tréplica — NPC reage ao argumento do Gerente dentro da sub_opcao
        for s_idx, sub in enumerate(rota.get("sub_opcoes", [])):
            argumento_trep = sub.get("argumento_gerente", "")
            if not argumento_trep:
                continue
            agente_trep = sub.get("agente_foco", agente_id)
            _gerar(f"{evt_id}:treplica:{r_idx}:{s_idx}", agente_trep, contexto, ano,
                   sub.get("temp_treplica"), argumento=argumento_trep, runs=runs)

    # 3. Opcoes (eventos 1999): tréplica por opcao com argumento_gerente
    for o_idx, opcao in enumerate(evt.get("opcoes", [])):
        argumento_trep = opcao.get("argumento_gerente", "")
        if not argumento_trep or not opcao.get("treplica"):
            continue
        _gerar(f"{evt_id}:treplica:{o_idx}", agente_id, contexto, ano,
               opcao.get("temp_treplica"), argumento=argumento_trep, runs=runs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pré-aquece o pool de falas.")
    parser.add_argument("--runs", type=int, default=3,
                        help="Variações a gerar por chave (default: 3, max: 15)")
    args = parser.parse_args()
    runs = min(args.runs, 15)

    total_eventos = 0
    for filename in EVENT_FILES:
        print(f"\n{'='*50}")
        print(f"  {filename}")
        print(f"{'='*50}")
        eventos = _load(filename)
        for evt in eventos:
            seed_evento(evt, runs)
            total_eventos += 1

    print(f"\n✓ Concluído — {total_eventos} eventos, {runs} variações por chave.")


if __name__ == "__main__":
    main()
