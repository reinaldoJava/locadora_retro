# src/Maps.py
# Constantes de mapeamento usadas pelos mixins de renderizacao.
# LAYOUT_RANDOM e mantido por compatibilidade mas o tema por partida
# e gerenciado pela sessao Flask (session[tema_visual]).

import random

LAYOUT_RANDOM = random.choice(["tema-a", "tema-b", "tema-c"])
ROTA_BG_2026 = {
    "A": "bg_2026_y2k_set",
    "B": "bg_2026_artefatos",
    "C": "bg_2026_detox",
    "D": "bg_2026_pub",
}
IMG_PERSONS = {
    "Leila": "leila", "Mauricio": "mauricio",
    "Vagner": "vagner", "Gerente": "gerente",
    "Influenciadora": "influenciadora",
    "Jovem GenZ": "jovem_genZ