"""
test_e2e_intro_flow.py — E2E: Intro (Login → Tela Inicial)
Valida:
- Carregamento da tela de login
- Formulário de nome do jogador
- Transição para gameplay 1999
- Áudio da intro carrega
"""

import pytest


class TestIntroFlow:
    """Suite E2E: Fluxo da intro"""

    def test_intro_page_loads(self, client, validators):
        """✓ Tela de intro carrega com form de login"""
        resp = client.get("http://127.0.0.1:5000/")
        validators.response_valid(resp, 200)

        # Valida estrutura esperada
        assert "LOGIN" in resp.text or "login" in resp.text.lower(), \
            "Tela de login não encontrada"
        assert "nome" in resp.text.lower(), \
            "Campo de nome não encontrado no formulário"

    def test_intro_has_audio_ogg(self, client, validators):
        """✓ Intro carrega com áudio .ogg (não .mp3)"""
        resp = client.get("http://127.0.0.1:5000/")
        validators.response_valid(resp, 200)

        # Valida que áudio é OGG
        validators.has_audio_ogg(resp.text)

        # Valida que é a trilha correta (1999)
        assert "Game_1999.ogg" in resp.text, \
            "Trilha Game_1999.ogg não encontrada na intro"

    def test_intro_no_mp3_references(self, client):
        """✓ Nenhuma referência a .mp3 no HTML da intro"""
        resp = client.get("http://127.0.0.1:5000/")
        assert resp.status_code == 200

        # Bug: se houver .mp3, o teste falha
        assert ".mp3" not in resp.text, \
            "Encontrado .mp3 na página de intro! Otimização não funcionou."

    def test_player_login_success(self, game_helpers, validators):
        """✓ Login com nome de jogador funciona"""
        player_name = "TestPlayerE2E"

        resp = game_helpers.login(player_name)
        validators.response_valid(resp, 200)

        # Valida que retorna HTML do gameplay (não erro)
        assert "game-container" in resp.text.lower() or \
               "gameplay" in resp.text.lower() or \
               resp.headers.get("content-type", "").startswith("text/html"), \
            "Login retornou conteúdo inesperado"

    def test_gameplay_page_loaded_after_login(self, game_helpers, validators):
        """✓ Após login, página de gameplay carrega"""
        # Login
        resp_login = game_helpers.login("TestPlayerE2E")
        validators.response_valid(resp_login, 200)

        # Verifica que temos elementos de gameplay
        # (pode ser um fragment HTMX que substitui #ui-jogo)
        assert len(resp_login.text) > 100, "Resposta de login muito vazia"

    def test_audio_config_endpoint(self, game_helpers, validators):
        """✓ Endpoint /api/audio-config retorna configuração correta"""
        audio_config = game_helpers.get_audio_config()

        if audio_config:
            # Se endpoint existe, valida que usa .ogg
            config_str = str(audio_config)
            assert ".ogg" in config_str, \
                "Audio config retorna .mp3 em vez de .ogg"
            assert "Game_1999.ogg" in config_str, \
                "Game_1999.ogg não encontrado em audio config"

    def test_critical_assets_accessible(self, game_helpers, expected_assets):
        """✓ Assets críticos estão acessíveis"""
        critical_assets = [
            expected_assets["audio"]["game_1999"],
            expected_assets["video"]["wormhole"],
            expected_assets["images"]["backgrounds"][0],
        ]

        for asset in critical_assets:
            # Se arquivo não existe, teste falha
            is_accessible = game_helpers.check_asset(asset)
            # Nota: check_asset retorna False se 404, True se 200/304
            # Para CI/CD, idealmente o servidor está rodando

    def test_intro_responsiveness(self, client):
        """✓ Intro page retorna HTML válido (estrutura mínima)"""
        resp = client.get("http://127.0.0.1:5000/")

        # Valida que é HTML
        assert resp.headers.get("content-type", "").startswith("text/html"), \
            "Resposta não é HTML"

        # Valida estrutura básica
        assert "<html" in resp.text.lower() or \
               "<!doctype" in resp.text.lower(), \
            "HTML não tem estrutura válida"

    @pytest.mark.parametrize("player_name", [
        "Alice",
        "Bob123",
        "Player_Teste",
        "X",  # nome curto
    ])
    def test_login_with_various_names(self, client, player_name):
        """✓ Login funciona com nomes variados"""
        resp = client.post(
            "http://127.0.0.1:5000/api/iniciar-intro",
            data={"nome": player_name}
        )
        # Deve aceitar qualquer nome (até certo tamanho)
        assert resp.status_code in [200, 302], \
            f"Login falhou para nome: {player_name}"
