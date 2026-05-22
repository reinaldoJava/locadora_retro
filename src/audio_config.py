# src/audio_config.py
# Configuracao centralizada dos assets de audio do jogo.
#
# Consumido por: motor_shell.js (via endpoint /api/audio-config ou injetado no template)
# e por audio_utils.js para resolver IDs e caminhos sem hardcode espalhado.
#
# Estrutura:
#   keyboard_sounds  — pool de sons de tecla sorteados aleatoriamente no typeText
#   click_sound      — feedback de clique em botoes de opcao
#   intro_music      — trilha da tela de login (intro.html)
#   game_music_1999  — trilha do gameplay 1999 (index.html)
#   game_music_2026  — trilha do gameplay 2026, carregada sob demanda na virada
#   countdown_bip_*  — sons da contagem regressiva da cinemática 1999->2000

AUDIO_SETTINGS = {
    "keyboard_sounds": [
        "/static/audio/tecla_1.mp3",
        "/static/audio/tecla_2.mp3",
        "/static/audio/tecla_3.mp3",
        "/static/audio/tecla_4.mp3",
    ],
    "click_sound": "/static/audio/click.mp3",
    "intro_music": {
        "id": "trilha-sonora-intro",
        "src": "/static/audio/Game_1999.mp3",
        "volume": 0.4,
        "loop": True
    },
    "game_music_1999": {
        "id": "trilha-sonora-1999",
        "src": "/static/audio/Game_1999.mp3",
        "volume": 0.3,
        "loop": True
    },
    "game_music_2026": {
        "id": "trilha-sonora-2026",
        "src": "/static/audio/Game_2026.mp3",
        "volume": 0.3,
        "loop": True
    },
    "countdown_bip_normal": "/static/audio/bip_normal.mp3",
    "countdown_bip_final": "/static/audio/bip_final.mp3",
}
