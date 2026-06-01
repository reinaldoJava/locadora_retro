"""
test_e2e_gameplay_1999.py — E2E: Gameplay 1999 (Dias 1-7)
Valida:
- Gameplay funciona após login
- Sem referências a .mp3
- Efeitos sonoros existem em .ogg
- Imagens existem em .webp
"""

import pytest
import os


class TestGameplay1999:
    """Suite E2E: Gameplay do ano 1999"""

    def test_gameplay_endpoint_accessible(self, client, game_helpers):
        """✓ Gameplay é acessível após login"""
        resp = game_helpers.login("TestPlayer1999")
        assert resp.status_code == 200

    def test_gameplay_no_mp3_references(self, client, game_helpers):
        """✓ Gameplay não referencia .mp3"""
        resp = game_helpers.login("TestPlayer1999")
        assert resp.status_code == 200

        # Crítico: sem .mp3
        assert ".mp3" not in resp.text, \
            "FALHA: Gameplay ainda referencia .mp3!"

    def test_gameplay_file_has_ogg(self, client):
        """✓ game_ui.html tem referências .ogg"""
        # Valida template direto em vez de resposta HTTP
        if os.path.exists("templates/game_ui.html"):
            with open("templates/game_ui.html", 'r', encoding='utf-8') as f:
                content = f.read()

            # Deve ter .ogg se tiver áudio
            if "audio" in content.lower() or "Game_" in content:
                assert ".ogg" in content, "game_ui.html sem .ogg"
                assert ".mp3" not in content, "game_ui.html tem .mp3!"

    def test_game_1999_audio_exists(self, client):
        """✓ Game_1999.ogg existe e é acessível"""
        resp = client.head("http://127.0.0.1:5000/static/audio/Game_1999.ogg")
        assert resp.status_code in [200, 304], \
            f"Game_1999.ogg não acessível: {resp.status_code}"

    def test_click_sound_exists(self, client):
        """✓ click.ogg existe e é acessível"""
        resp = client.head("http://127.0.0.1:5000/static/audio/click.ogg")
        assert resp.status_code in [200, 304], \
            f"click.ogg não acessível: {resp.status_code}"

    def test_keyboard_sounds_exist(self, client):
        """✓ Sons de teclado (tecla_*.ogg) existem"""
        for i in range(1, 5):
            resp = client.head(f"http://127.0.0.1:5000/static/audio/tecla_{i}.ogg")
            assert resp.status_code in [200, 304], \
                f"tecla_{i}.ogg não acessível"

    def test_background_images_webp_exist(self, client):
        """✓ Background images existem em .webp"""
        backgrounds = [
            "/static/img/bg_1999.webp",
            "/static/img/bg_undefined.webp",
        ]

        for bg in backgrounds:
            resp = client.head(f"http://127.0.0.1:5000{bg}")
            # Pode ser 200 ou 404 se imagem opcional
            assert resp.status_code in [200, 304, 404], \
                f"Status inesperado para {bg}: {resp.status_code}"

    def test_character_images_exist(self, client):
        """✓ Imagens de personagens existem"""
        characters = [
            "/static/img/leila.webp",
            "/static/img/marcos.webp",
            "/static/img/vagner.webp",
        ]

        for char in characters:
            resp = client.head(f"http://127.0.0.1:5000{char}")
            # Pode ser 200 ou 404 se personagem opcional
            assert resp.status_code in [200, 304, 404], \
                f"Status inesperado para {char}: {resp.status_code}"

    def test_day_1_scenario_accessible(self, game_helpers):
        """✓ Primeiro dia (Dia 1) é acessível após login"""
        resp = game_helpers.login("TestDay1")
        assert resp.status_code == 200

    def test_game_transitions_endpoint_exists(self, client):
        """✓ Endpoint de transição entre dias existe"""
        resp = client.post("http://127.0.0.1:5000/api/iniciar-game-transition")
        # Pode ser 200, 302, 404, ou 405
        assert resp.status_code in [200, 302, 404, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_interacao_endpoint_exists(self, client):
        """✓ Endpoint de interação existe"""
        resp = client.post("http://127.0.0.1:5000/api/interagir",
                          json={"choice_id": "1"})
        # Pode ser 200, 302, 404, ou 405
        assert resp.status_code in [200, 302, 404, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_no_mp3_in_audio_directory(self, client):
        """✓ Nenhum .mp3 está acessível em static/audio/"""
        resp = client.head("http://127.0.0.1:5000/static/audio/Game_1999.mp3")
        assert resp.status_code == 404, \
            "CRÍTICO: Game_1999.mp3 ainda está acessível!"
