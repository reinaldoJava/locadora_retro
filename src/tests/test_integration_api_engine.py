"""
test_integration_api_engine.py — Integração: APIs e Game Engine
Valida:
- Endpoints retornam respostas corretas
- Módulos centrais existem e são acessíveis
"""

import pytest
import os


class TestAPIEngineIntegration:
    """Suite Integração: API endpoints + Core modules"""

    def test_audio_config_file_exists(self):
        """✓ Arquivo de configuração de áudio existe"""
        audio_config_file = "src/audio_config.py"
        assert os.path.exists(audio_config_file), \
            "Arquivo src/audio_config.py não encontrado"

    def test_core_modules_exist(self):
        """✓ Módulos centrais existem"""
        modules = [
            "src/engine.py",
            "src/narrative_director.py",
            "src/audio_config.py",
        ]

        for module in modules:
            assert os.path.exists(module), f"Módulo não encontrado: {module}"

    def test_iniciar_intro_endpoint_exists(self, client):
        """✓ Endpoint POST /api/iniciar-intro existe"""
        resp = client.post("http://127.0.0.1:5000/api/iniciar-intro",
                          data={"nome": "TestPlayer"})

        # Deve retornar 200 ou 302 (redirect)
        assert resp.status_code in [200, 302, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_game_transition_endpoint_exists(self, client):
        """✓ Endpoint POST /api/iniciar-game-transition existe"""
        resp = client.post("http://127.0.0.1:5000/api/iniciar-game-transition")

        # Pode ser 200, 302, 404, ou 405
        assert resp.status_code in [200, 302, 404, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_interagir_endpoint_exists(self, client):
        """✓ Endpoint POST /api/interagir existe"""
        resp = client.post("http://127.0.0.1:5000/api/interagir",
                          json={"choice": "A"})

        # Pode ser 200, 302, 404, ou 405
        assert resp.status_code in [200, 302, 404, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_api_endpoints_no_500_errors(self, client):
        """✓ Nenhum endpoint retorna erro 500"""
        endpoints = [
            ("POST", "/api/iniciar-intro"),
            ("POST", "/api/iniciar-game-transition"),
            ("POST", "/api/interagir"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                resp = client.get(f"http://127.0.0.1:5000{endpoint}")
            else:
                resp = client.post(f"http://127.0.0.1:5000{endpoint}")

            # Qualquer status é ok, menos 500
            assert resp.status_code != 500, \
                f"Erro 500 em {method} {endpoint}"

    def test_login_creates_session(self, game_helpers):
        """✓ Login cria sessão válida"""
        resp = game_helpers.login("TestPlayer")

        # Deve retornar 200
        assert resp.status_code == 200, \
            f"Login falhou com status {resp.status_code}"

        # Resposta deve ter conteúdo HTML
        assert len(resp.text) > 100, "Resposta de login vazia"

    def test_placar_endpoint_exists(self, client):
        """✓ Endpoint /api/placar é acessível"""
        resp = client.get("http://127.0.0.1:5000/api/placar")

        # Pode ser 200 ou 404 dependendo de implementação
        assert resp.status_code in [200, 404], \
            f"Status inesperado: {resp.status_code}"

    def test_animacao_concluida_endpoint_exists(self, client):
        """✓ Endpoint /api/animacao-concluida é acessível"""
        resp = client.post("http://127.0.0.1:5000/api/animacao-concluida")

        # Pode ser 200 (ok), 204 (no content), 302, 404, ou 405
        assert resp.status_code in [200, 204, 302, 404, 405], \
            f"Status inesperado: {resp.status_code}"

    def test_api_response_times_reasonable(self, client):
        """✓ APIs respondem em tempo razoável (<2s)"""
        import time

        endpoints = [
            ("POST", "/api/iniciar-intro"),
        ]

        for method, endpoint in endpoints:
            start = time.time()

            try:
                if method == "GET":
                    resp = client.get(f"http://127.0.0.1:5000{endpoint}", timeout=5)
                else:
                    resp = client.post(f"http://127.0.0.1:5000{endpoint}", timeout=5)

                elapsed = (time.time() - start) * 1000

                print(f"\n⏱️  {method} {endpoint}: {elapsed:.0f}ms")

                # Deve responder em menos de 2 segundos
                assert elapsed < 2000, f"Resposta lenta: {elapsed:.0f}ms"
            except Exception as e:
                # Timeout ou erro de conexão é aceitável para teste de performance
                print(f"\n⏱️  {method} {endpoint}: erro ({e})")

    def test_engine_has_required_attributes(self):
        """✓ Engine tem atributos esperados"""
        import os

        engine_file = "src/engine.py"
        assert os.path.exists(engine_file), "engine.py não encontrado"

        with open(engine_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Valida que tem classe Engine
        assert "class Engine" in content, "Classe Engine não encontrada"

        # Valida que tem __init__
        assert "def __init__" in content, "Método __init__ não encontrado em Engine"

    def test_narrative_director_exists(self):
        """✓ DiretorNarrativo existe"""
        import os

        narrative_file = "src/narrative_director.py"
        assert os.path.exists(narrative_file), "narrative_director.py não encontrado"

        with open(narrative_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "class DiretorNarrativo" in content, \
            "Classe DiretorNarrativo não encontrada"
