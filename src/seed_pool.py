#!/usr/bin/env python3
"""
scripts/seed_pool.py — Cache Warming do Pool de Falas (Offline Inference)
=========================================================================
Padrão arquitetural: Cache Warming / Offline Inference.

Pré-popula o Firestore fala_pool com variações de fala para todos os eventos
de 1999 ANTES do deploy, de modo que o gameplay nunca precise chamar a
Gemini API em tempo real.

Chaves geradas por evento com agente_foco:
  {evt_id}                      — situação (fala inicial do NPC)
  {evt_id}:replica:{rota_idx}   — réplica por rota principal (A/B/C)
  {evt_id}:treplica:{r}:{s}     — tréplica por rota+sub-opção

Execução sequencial com CALL_DELAY_S entre chamadas para respeitar
o rate limit do free tier (15 req/min → 1 req / ~4s).

Uso:
  cd /caminho/do/projeto
  export GEMINI_API_KEY=...
  export LLM_PROVIDER=gemini
  python scripts/seed_pool.py [--variations N] [--dry-run] [--skip-existing]

Flags:
  --variations N    Número de variações por chave (padrão: 5)
  --dry-run         Lista o que seria gerado sem chamar a API
  --skip-existing   Pula chaves que já têm >= MIN_EXISTING variações no pool
"""

import sys
import os
import json
import time
import argparse
import pathlib

# Permite importar src/ a partir da raiz do projeto
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents import (
    gerar_fala,
    obter_do_pool,
    adicionar_ao_pool,
    _RETRY_DELAYS,
)

# ── Configuração ────────────────────────────────────────────────────────────
CALL_DELAY_S   = 4.5   # segundos entre chamadas (garante < 15 req/min)
MIN_EXISTING   = 3     # variações mínimas para considerar chave "aquecida"
DATA_DIR       = ROOT / "data"

# Arquivos que contêm eventos com agente_foco (somente 1999)
EVENT_FILES = [
    DATA_DIR / "eventos_1999.json",
]


# ── Utilitários ─────────────────────────────────────────────────────────────

def carregar_eventos() -> list[dict]:
    """Carrega todos os eventos com agente_foco dos arquivos configurados."""
    eventos = []
    for path in EVENT_FILES:
        with open(path, encoding="utf-8") as f:
            for evt in json.load(f):
                if evt.get("agente_foco") and evt.get("contexto_ia"):
                    eventos.append(evt)
    return eventos


def chaves_do_evento(evt: dict) -> list[tuple[str, str, str, str]]:
    """
    Retorna lista de (pool_key, tipo, argumento, descricao) para um evento.
    tipo: 'situacao' | 'replica' | 'treplica'
    argumento: texto do Gerente que dispara a fala do NPC (vazio na situação)
    """
    evt_id    = evt["id"]
    agente_id = evt["agente_foco"]
    rotas     = evt.get("rotas_principais", [])
    resultado = []

    # Situação
    resultado.append((
        evt_id,
        "situacao",
        "",
        f"[situação] {evt_id}"
    ))

    # Réplica por rota
    for r_idx, rota in enumerate(rotas):
        pool_key  = f"{evt_id}:replica:{r_idx}"
        argumento = rota.get("fala_gerente", "")
        resultado.append((
            pool_key,
            "replica",
            argumento,
            f"[réplica rota {r_idx}] {evt_id}"
        ))

    # Tréplica por rota+sub
    for r_idx, rota in enumerate(rotas):
        for s_idx, sub in enumerate(rota.get("sub_opcoes", [])):
            pool_key  = f"{evt_id}:treplica:{r_idx}:{s_idx}"
            argumento = sub.get("argumento_gerente", "")
            resultado.append((
                pool_key,
                "treplica",
                argumento,
                f"[tréplica {r_idx}:{s_idx}] {evt_id}"
            ))

    return resultado


def contar_no_pool(pool_key: str) -> int:
    """Retorna quantas variações já existem no pool para a chave."""
    # obter_do_pool retorna uma fala aleatória ou None — não expõe a contagem.
    # Aqui acessamos o Firestore diretamente se disponível; senão assume 0.
    try:
        from google.cloud import firestore as _fs
        db = _fs.Client()
        doc = db.collection("fala_pool").document(pool_key).get()
        if doc.exists:
            return len(doc.to_dict().get("falas", []))
        return 0
    except Exception:
        return 0  # Firestore indisponível: trata como vazio


# ── Seed ────────────────────────────────────────────────────────────────────

def seed(variations: int, dry_run: bool, skip_existing: bool) -> None:
    eventos = carregar_eventos()

    # Montar plano completo
    plano: list[tuple[dict, str, str, str, str]] = []
    for evt in eventos:
        for pool_key, tipo, argumento, desc in chaves_do_evento(evt):
            plano.append((evt, pool_key, tipo, argumento, desc))

    total_chaves    = len(plano)
    total_chamadas  = total_chaves * variations
    tempo_estimado  = total_chamadas * CALL_DELAY_S / 60

    print(f"\n{'='*60}")
    print(f"  LOCADORA RETRÔ — Cache Warming (seed_pool.py)")
    print(f"{'='*60}")
    print(f"  Eventos com agente: {len(eventos)}")
    print(f"  Chaves a preencher: {total_chaves}")
    print(f"  Variações por chave: {variations}")
    print(f"  Total de chamadas:  {total_chamadas}")
    print(f"  Tempo estimado:     ~{tempo_estimado:.0f} min")
    print(f"  Modo dry-run:       {'SIM' if dry_run else 'NÃO'}")
    print(f"  Pular existentes:   {'SIM' if skip_existing else 'NÃO'}")
    print(f"{'='*60}\n")

    if dry_run:
        for i, (evt, pool_key, tipo, argumento, desc) in enumerate(plano, 1):
            print(f"  [{i:03d}] {desc}")
            print(f"        chave:     {pool_key}")
            print(f"        argumento: {argumento[:60]!r}" if argumento else "        argumento: (vazio)")
        print(f"\n  [dry-run] Nenhuma chamada realizada.")
        return

    chamadas_feitas   = 0
    chamadas_puladas  = 0
    chamadas_erro     = 0

    for evt_idx, (evt, pool_key, tipo, argumento, desc) in enumerate(plano):
        agente_id = evt["agente_foco"]
        contexto  = evt["contexto_ia"]
        ano       = evt.get("ano", 1999)

        existentes = contar_no_pool(pool_key) if skip_existing else 0

        if skip_existing and existentes >= MIN_EXISTING:
            print(f"  ⏭  {desc} — {existentes} variações já existem, pulando")
            chamadas_puladas += variations
            continue

        geradas_nessa_chave = 0
        for v in range(existentes, variations):
            print(f"  ⟳  {desc} [{v+1}/{variations}]", end="", flush=True)

            fala = gerar_fala(agente_id, contexto, ano, argumento=argumento)

            if fala and fala != "...":
                adicionar_ao_pool(pool_key, fala)
                chamadas_feitas += 1
                geradas_nessa_chave += 1
                print(f" ✓  {fala[:70]!r}")
            else:
                chamadas_erro += 1
                print(f" ✗  fallback/erro")

            # Delay entre chamadas para respeitar o rate limit
            if v < variations - 1 or evt_idx < len(plano) - 1:
                time.sleep(CALL_DELAY_S)

        print(f"     → {geradas_nessa_chave} variações geradas para {pool_key}\n")

    print(f"\n{'='*60}")
    print(f"  Seed concluído")
    print(f"  Chamadas bem-sucedidas: {chamadas_feitas}")
    print(f"  Chamadas puladas:       {chamadas_puladas}")
    print(f"  Erros/fallbacks:        {chamadas_erro}")
    print(f"{'='*60}\n")


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cache Warming — pré-popula o pool de falas no Firestore."
    )
    parser.add_argument(
        "--variations", type=int, default=5,
        help="Número de variações a gerar por chave (padrão: 5)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Lista o plano sem chamar a API"
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help=f"Pula chaves que já têm >= {MIN_EXISTING} variações no Firestore"
    )
    args = parser.parse_args()

    seed(
        variations=args.variations,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
    )
