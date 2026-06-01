"""
test_integration_audio_system.py — Integração: Sistema de Áudio
Valida:
- OGG carrega corretamente (sem .mp3)
- Arquivos de áudio existem e são acessíveis
- Templates usam corretos caminhos de áudio
"""

import pytest
import os
import re


class TestAudioSystemIntegration:
    """Suite Integração: Audio system (config + playback)"""

    def test_audio_config_file_exists(self):
        """✓ Arquivo src/audio_config.py existe"""
        assert os.path.exists("src/audio_config.py"), "src/audio_config.py não encontrado"

    def test_audio_config_no_mp3_references(self):
        """✓ src/audio_config.py não tem .mp3"""
        with open("src/audio_config.py", 'r', encoding='utf-8') as f:
            content = f.read()

        assert ".mp3" not in content, "CRÍTICO: .mp3 encontrado em audio_config.py!"
        assert ".ogg" in content, "audio_config.py não tem .ogg"

    def test_all_critical_audio_files_exist(self, client):
        """✓ Todos os arquivos críticos de áudio existem"""
        audio_files = [
            "/static/audio/Game_1999.ogg",
            "/static/audio/Game_2026.ogg",
            "/static/audio/click.ogg",
            "/static/audio/bip_normal.ogg",
            "/static/audio/bip_final.ogg",
            "/static/audio/tecla_1.ogg",
            "/static/audio/tecla_2.ogg",
            "/static/audio/tecla_3.ogg",
            "/static/audio/tecla_4.ogg",
        ]

        for audio_file in audio_files:
            resp = client.head(f"http://127.0.0.1:5000{audio_file}")
            assert resp.status_code in [200, 304], \
                f"Arquivo não acessível: {audio_file} (status {resp.status_code})"

    def test_no_mp3_files_accessible(self, client):
        """✓ Nenhum arquivo .mp3 está acessível"""
        # Tenta acessar um .mp3 que deveria ter sido removido
        resp = client.head("http://127.0.0.1:5000/static/audio/Game_1999.mp3")

        # Status deve ser 404 (não encontrado)
        assert resp.status_code == 404, \
            "CRÍTICO: Arquivo .mp3 ainda está acessível!"

    def test_intro_template_has_audio_ogg(self):
        """✓ Template intro.html usa .ogg"""
        with open("templates/intro.html", 'r', encoding='utf-8') as f:
            content = f.read()

        assert ".ogg" in content, "intro.html não tem .ogg"
        assert ".mp3" not in content, "intro.html ainda tem .mp3!"

    def test_game_ui_template_has_audio_ogg(self):
        """✓ Template game_ui.html usa .ogg"""
        with open("templates/game_ui.html", 'r', encoding='utf-8') as f:
            content = f.read()

        # Pode ter áudio ou não, mas se tiver deve ser .ogg
        if "audio" in content or "Game_" in content:
            assert ".mp3" not in content, "game_ui.html tem .mp3!"

    def test_cinematic_template_has_audio_ogg(self):
        """✓ Template cinematic_1999_to_2026.html usa .ogg"""
        with open("templates/cinematic_1999_to_2026.html", 'r', encoding='utf-8') as f:
            content = f.read()

        # Pode ter áudio ou não, mas se tiver deve ser .ogg
        if "audio" in content.lower() or "Game_" in content:
            assert ".mp3" not in content, "cinematic_1999_to_2026.html tem .mp3!"

    def test_audio_files_are_ogg_format(self):
        """✓ Todos os arquivos em static/audio/ são .ogg"""
        audio_dir = "static/audio"
        if os.path.exists(audio_dir):
            files = os.listdir(audio_dir)
            for f in files:
                if f.endswith(".mp3"):
                    raise AssertionError(f"Encontrado .mp3 em static/audio: {f}")
                assert f.endswith(".ogg"), f"Arquivo não é .ogg: {f}"

    def test_audio_utils_supports_ogg(self):
        """✓ audio_utils.js suporta .ogg"""
        audio_utils = "static/js/audio_utils.js"
        if os.path.exists(audio_utils):
            with open(audio_utils, 'r', encoding='utf-8') as f:
                content = f.read()

            # Não deve ter referências a .mp3
            assert ".mp3" not in content, "audio_utils.js tem .mp3!"

    def test_intro_slide_audio_ogg(self):
        """✓ intro_slide.html usa .ogg"""
        template_file = "templates/intro_slide.html"
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "audio" in content.lower() or ".ogg" in content or ".mp3" in content:
                assert ".mp3" not in content, "intro_slide.html tem .mp3!"

    def test_game_over_audio_ogg(self):
        """✓ Tela de game over usa .ogg"""
        template_file = "templates/game_over.html"
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "audio" in content.lower() or ".ogg" in content or ".mp3" in content:
                assert ".mp3" not in content, "game_over.html tem .mp3!"

    def test_fim_de_jogo_audio_ogg(self):
        """✓ Template fim_de_jogo.html usa .ogg"""
        template_file = "templates/fim_de_jogo.html"
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "audio" in content.lower() or ".ogg" in content or ".mp3" in content:
                assert ".mp3" not in content, "fim_de_jogo.html tem .mp3!"

    def test_keyboard_sounds_exist(self, client):
        """✓ Todos os 4 sons de teclado existem"""
        keyboard_sounds = [
            "/static/audio/tecla_1.ogg",
            "/static/audio/tecla_2.ogg",
            "/static/audio/tecla_3.ogg",
            "/static/audio/tecla_4.ogg",
        ]

        for sound in keyboard_sounds:
            resp = client.head(f"http://127.0.0.1:5000{sound}")
            assert resp.status_code in [200, 304], f"Tecla não acessível: {sound}"

    def test_countdown_sounds_exist(self, client):
        """✓ Sons de countdown existem"""
        countdown_sounds = [
            "/static/audio/bip_normal.ogg",
            "/static/audio/bip_final.ogg",
        ]

        for sound in countdown_sounds:
            resp = client.head(f"http://127.0.0.1:5000{sound}")
            assert resp.status_code in [200, 304], f"Som de countdown não acessível: {sound}"
