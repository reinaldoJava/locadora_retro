"""
test_unit_audio.py — Unit Tests: Audio System
Testa configuração de áudio, formato OGG, volumes e transições.
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from audio_config import (
        AUDIO_CONFIG,
        get_audio_config,
        INTRO_MUSIC,
        GAME_MUSIC_1999,
        GAME_MUSIC_2026,
        CLICK_SOUND,
        KEYBOARD_SOUNDS,
    )
    AUDIO_MODULE_AVAILABLE = True
except ImportError:
    AUDIO_MODULE_AVAILABLE = False


@pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
class TestAudioConfig:
    """Suite: Configuração de Áudio"""

    def test_audio_config_dict(self):
        """✓ AUDIO_CONFIG é um dicionário"""
        assert isinstance(AUDIO_CONFIG, dict), "AUDIO_CONFIG deve ser dict"

    def test_audio_config_has_required_keys(self):
        """✓ AUDIO_CONFIG tem chaves obrigatórias"""
        required_keys = [
            'intro_music',
            'game_music_1999',
            'game_music_2026',
            'click_sound',
            'keyboard_sounds',
            'countdown_bip_normal',
            'countdown_bip_final',
        ]

        for key in required_keys:
            assert key in AUDIO_CONFIG, f"Chave '{key}' faltando em AUDIO_CONFIG"

    def test_audio_config_no_mp3_references(self):
        """✓ AUDIO_CONFIG não contém .mp3"""
        config_str = str(AUDIO_CONFIG)

        # Crítico: sem .mp3
        assert ".mp3" not in config_str, \
            "CRÍTICO: .mp3 encontrado em AUDIO_CONFIG!"

    def test_audio_config_uses_ogg_format(self):
        """✓ AUDIO_CONFIG usa formato .ogg"""
        config_str = str(AUDIO_CONFIG)

        # Deve ter referências a .ogg
        assert ".ogg" in config_str, "AUDIO_CONFIG não tem .ogg"


class TestAudioFiles:
    """Suite: Arquivos de Áudio"""

    def test_audio_directory_exists(self):
        """✓ Diretório static/audio/ existe"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"
        assert audio_dir.exists(), "Diretório static/audio/ não encontrado"

    def test_critical_audio_files_exist(self):
        """✓ Arquivos críticos de áudio existem"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        critical_files = [
            'Game_1999.ogg',
            'Game_2026.ogg',
            'click.ogg',
            'bip_normal.ogg',
            'bip_final.ogg',
        ]

        for filename in critical_files:
            filepath = audio_dir / filename
            assert filepath.exists(), f"Arquivo {filename} não encontrado"

    def test_keyboard_sounds_exist(self):
        """✓ Todos os 4 sons de teclado existem"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        for i in range(1, 5):
            filepath = audio_dir / f"tecla_{i}.ogg"
            assert filepath.exists(), f"Arquivo tecla_{i}.ogg não encontrado"

    def test_audio_files_are_ogg_format(self):
        """✓ Todos os arquivos em static/audio/ são .ogg"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        for filename in os.listdir(audio_dir):
            if not filename.startswith('.'):
                assert filename.endswith('.ogg'), \
                    f"Arquivo {filename} não é .ogg"

    def test_no_mp3_files_in_audio_directory(self):
        """✓ Nenhum arquivo .mp3 em static/audio/"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        for filename in os.listdir(audio_dir):
            assert not filename.endswith('.mp3'), \
                f"Encontrado .mp3: {filename}"


@pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
class TestMusicConfiguration:
    """Suite: Configuração de Música"""

    def test_intro_music_configured(self):
        """✓ Música de intro está configurada"""
        assert INTRO_MUSIC is not None, "INTRO_MUSIC não configurada"
        assert isinstance(INTRO_MUSIC, (str, dict)), \
            "INTRO_MUSIC deve ser string ou dict"

    def test_game_music_1999_configured(self):
        """✓ Música de 1999 está configurada"""
        assert GAME_MUSIC_1999 is not None, "GAME_MUSIC_1999 não configurada"
        assert isinstance(GAME_MUSIC_1999, (str, dict)), \
            "GAME_MUSIC_1999 deve ser string ou dict"

    def test_game_music_2026_configured(self):
        """✓ Música de 2026 está configurada"""
        assert GAME_MUSIC_2026 is not None, "GAME_MUSIC_2026 não configurada"
        assert isinstance(GAME_MUSIC_2026, (str, dict)), \
            "GAME_MUSIC_2026 deve ser string ou dict"

    def test_music_paths_are_ogg(self):
        """✓ Caminhos de música são .ogg"""
        music_items = [INTRO_MUSIC, GAME_MUSIC_1999, GAME_MUSIC_2026]

        for music in music_items:
            music_str = str(music)
            assert ".ogg" in music_str, f"Música não é .ogg: {music}"


@pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
class TestEffectSounds:
    """Suite: Sons de Efeito"""

    def test_click_sound_configured(self):
        """✓ Som de clique está configurado"""
        assert CLICK_SOUND is not None, "CLICK_SOUND não configurada"
        assert isinstance(CLICK_SOUND, (str, dict)), \
            "CLICK_SOUND deve ser string ou dict"

    def test_click_sound_is_ogg(self):
        """✓ Som de clique é .ogg"""
        click_str = str(CLICK_SOUND)
        assert ".ogg" in click_str, "CLICK_SOUND não é .ogg"

    def test_keyboard_sounds_configured(self):
        """✓ Sons de teclado estão configurados"""
        assert KEYBOARD_SOUNDS is not None, "KEYBOARD_SOUNDS não configurada"
        assert isinstance(KEYBOARD_SOUNDS, list), \
            "KEYBOARD_SOUNDS deve ser lista"

    def test_keyboard_sounds_has_four_items(self):
        """✓ Array de teclado tem 4 sons"""
        assert len(KEYBOARD_SOUNDS) >= 4, \
            f"KEYBOARD_SOUNDS deve ter 4+ items, tem {len(KEYBOARD_SOUNDS)}"

    def test_keyboard_sounds_are_ogg(self):
        """✓ Todos os sons de teclado são .ogg"""
        for sound in KEYBOARD_SOUNDS:
            sound_str = str(sound)
            assert ".ogg" in sound_str, f"Som de teclado não é .ogg: {sound}"


@pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
class TestCountdownSounds:
    """Suite: Sons de Countdown"""

    def test_countdown_bip_normal_configured(self):
        """✓ Som de bip normal está configurado"""
        assert 'countdown_bip_normal' in AUDIO_CONFIG
        bip = AUDIO_CONFIG.get('countdown_bip_normal')
        assert bip is not None, "countdown_bip_normal é None"

    def test_countdown_bip_final_configured(self):
        """✓ Som de bip final está configurado"""
        assert 'countdown_bip_final' in AUDIO_CONFIG
        bip = AUDIO_CONFIG.get('countdown_bip_final')
        assert bip is not None, "countdown_bip_final é None"

    def test_countdown_biips_are_ogg(self):
        """✓ Sons de countdown são .ogg"""
        bips = [
            AUDIO_CONFIG.get('countdown_bip_normal'),
            AUDIO_CONFIG.get('countdown_bip_final'),
        ]

        for bip in bips:
            if bip:
                bip_str = str(bip)
                assert ".ogg" in bip_str, f"Bip não é .ogg: {bip}"


class TestAudioConfigFunction:
    """Suite: Função get_audio_config()"""

    @pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
    def test_get_audio_config_returns_dict(self):
        """✓ get_audio_config() retorna dict"""
        config = get_audio_config()

        assert isinstance(config, dict), "get_audio_config deve retornar dict"

    @pytest.mark.skipif(not AUDIO_MODULE_AVAILABLE, reason="audio_config not available")
    def test_get_audio_config_contains_keys(self):
        """✓ get_audio_config() retorna chaves esperadas"""
        config = get_audio_config()

        expected_keys = ['game_music_1999', 'game_music_2026', 'click_sound']
        for key in expected_keys:
            assert key in config, f"Chave '{key}' faltando em get_audio_config()"
