"""
conftest.py — Fixtures compartilhadas para testes E2E e Integração
Configura: cliente HTTP, session do jogo, fixtures de data
"""

import pytest
import requests
import json
from datetime import datetime
from pathlib import Path


# ===== CONFIGURAÇÃO BASE =====

# Tenta 127.0.0.1 primeiro (mais comum em Windows), depois localhost
import requests as _req
_urls = ["http://127.0.0.1:5000", "http://localhost:5000"]
BASE_URL = None
for url in _urls:
    try:
        _req.head(url, timeout=2)
        BASE_URL = url
        break
    except:
        pass

if not BASE_URL:
    BASE_URL = "http://127.0.0.1:5000"  # Default

TIMEOUT = 10


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP para requisições ao servidor"""
    session = requests.Session()
    session.timeout = TIMEOUT
    # Test health check
    try:
        resp = session.get(f"{BASE_URL}/")
        assert resp.status_code in [200, 302], "Servidor não está acessível"
    except Exception as e:
        pytest.skip(f"Servidor não respondeu: {e}")
    return session


@pytest.fixture(scope="function")
def game_session(client):
    """Cria uma nova sessão de jogo para cada teste"""
    # Limpa cookies anteriores
    client.cookies.clear()

    # Inicia o jogo (tela de intro)
    resp = client.get(f"{BASE_URL}/")
    assert resp.status_code in [200, 302]

    return {
        "client": client,
        "session_cookies": client.cookies,
        "player_name": f"TestPlayer_{datetime.now().timestamp()}",
        "start_time": datetime.now()
    }


# ===== HELPERS PARA NAVEGAÇÃO =====

@pytest.fixture
def game_helpers(game_session):
    """Funções auxiliares para interagir com o jogo"""
    client = game_session["client"]

    class GameHelpers:
        @staticmethod
        def login(player_name="TestPlayer"):
            """Faz login no jogo"""
            resp = client.post(
                f"{BASE_URL}/api/iniciar-intro",
                data={"nome": player_name}
            )
            return resp

        @staticmethod
        def select_difficulty(difficulty="beta"):
            """Seleciona dificuldade (não disponível na demo, mas deixamos o helper)"""
            # Neste projeto, dificuldade é fixa em "beta"
            pass

        @staticmethod
        def advance_day():
            """Avança para o próximo dia"""
            resp = client.post(f"{BASE_URL}/api/iniciar-game-transition")
            return resp

        @staticmethod
        def make_choice(option_id):
            """Faz uma escolha no diálogo"""
            resp = client.post(
                f"{BASE_URL}/api/interagir",
                json={"choice_id": option_id}
            )
            return resp

        @staticmethod
        def get_current_state():
            """Obtém o estado atual do jogo

            Nota: /api/game-state não é exposto na aplicação atual.
            O estado fica armazenado em session (lado servidor).
            Retorna None para compatibilidade com testes.
            """
            # Este endpoint não existe na aplicação
            return None

        @staticmethod
        def get_audio_config():
            """Obtém configuração de áudio do backend

            Nota: /api/audio-config não é exposto na aplicação atual.
            Audio config é gerenciado por src/audio_config.py (carregado direto nos templates).
            Para validar áudio, leia os templates ou os arquivos direto do disco.
            Retorna None para compatibilidade com testes.
            """
            # Este endpoint não existe na aplicação
            return None

        @staticmethod
        def check_asset(asset_path):
            """Verifica se um asset está acessível"""
            resp = client.head(f"{BASE_URL}{asset_path}")
            return resp.status_code == 200

    return GameHelpers()


# ===== VALIDADORES =====

@pytest.fixture
def validators():
    """Funções para validar estados e conteúdo"""

    class Validators:
        @staticmethod
        def has_audio_ogg(html_content):
            """Verifica se há referências a .ogg em vez de .mp3"""
            assert ".ogg" in html_content, "Não encontrado arquivo .ogg no HTML"
            assert ".mp3" not in html_content, "Ainda há referência a .mp3 no HTML"

        @staticmethod
        def has_video_element(html_content):
            """Verifica se vídeo está no HTML"""
            assert "<video" in html_content or "wormhole.mp4" in html_content

        @staticmethod
        def has_lazy_loading(html_content):
            """Verifica se imagens têm loading='lazy'"""
            assert 'loading="lazy"' in html_content, "Lazy loading não implementado"

        @staticmethod
        def response_valid(resp, expected_status=200):
            """Valida resposta HTTP"""
            assert resp.status_code == expected_status, \
                f"Status {resp.status_code}, esperado {expected_status}: {resp.text[:200]}"
            return True

        @staticmethod
        def json_has_key(data, key):
            """Valida presença de chave em JSON"""
            assert key in data, f"Chave '{key}' não encontrada em: {data}"

    return Validators()


# ===== FIXTURES DE DADOS =====

@pytest.fixture(scope="session")
def expected_assets():
    """Mapeia assets esperados no projeto"""
    return {
        "audio": {
            "game_1999": "/static/audio/Game_1999.ogg",
            "game_2026": "/static/audio/Game_2026.ogg",
            "bip_normal": "/static/audio/bip_normal.ogg",
            "bip_final": "/static/audio/bip_final.ogg",
            "click": "/static/audio/click.ogg",
            "teclas": [
                "/static/audio/tecla_1.ogg",
                "/static/audio/tecla_2.ogg",
                "/static/audio/tecla_3.ogg",
                "/static/audio/tecla_4.ogg",
            ]
        },
        "video": {
            "wormhole": "/static/video/wormhole.mp4",
        },
        "images": {
            "backgrounds": [
                "/static/img/bg_1999.webp",
                "/static/img/bg_2026.webp",
                "/static/img/bg_undefined.webp",
            ],
            "characters": [
                "/static/img/leila.webp",
                "/static/img/vagner.webp",
                "/static/img/marcos.webp",
                "/static/img/influenciadora.webp",
            ]
        }
    }
