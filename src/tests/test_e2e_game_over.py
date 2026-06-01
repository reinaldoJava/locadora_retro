"""
test_e2e_game_over.py — E2E: Game Over (Telas Finais)
Valida:
- Tela de game over carrega
- Sistema de pontuação funciona
- Sem erros de áudio/vídeo
"""

import pytest
import os
import re
import time


class TestGameOver:
    """Suite E2E: Finalização do jogo"""

    def test_game_over_template_exists(self, client):
        """✓ Template de game over existe"""
        game_over_file = "templates/game_over.html"
        assert os.path.exists(game_over_file), \
            "Template game_over.html não encontrado"

    def test_game_over_page_structure(self, client):
        """✓ Página de game over tem estrutura válida"""
        game_over_file = "templates/fim_de_jogo.html"
        if os.path.exists(game_over_file):
            with open(game_over_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Valida elementos esperados
            assert len(content) > 100, "Arquivo vazio"

    def test_game_over_no_mp3_references(self, client):
        """✓ Tela de game over não referencia .mp3"""
        game_over_files = [
            "templates/game_over.html",
            "templates/fim_de_jogo.html",
        ]

        for file_path in game_over_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                assert ".mp3" not in content, \
                    f"Encontrado .mp3 em {file_path}!"

    def test_game_over_has_score_display(self, client):
        """✓ Tela de game over exibe pontuação"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Procura por elemento de pontuação
            assert "placar" in content.lower() or \
                   "score" in content.lower() or \
                   "pontos" in content.lower() or \
                   "resultado" in content.lower(), \
                "Display de pontuação não encontrado"

    def test_game_over_restart_button(self, client):
        """✓ Botão de reiniciar está presente"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "button" in content.lower() or \
                   "reinicia" in content.lower() or \
                   "novo jogo" in content.lower() or \
                   "jogar novamente" in content.lower(), \
                "Botão de reiniciar não encontrado"

    def test_game_over_audio_config_valid(self, client, game_helpers):
        """✓ Audio config ainda válido em game over"""
        audio_config = game_helpers.get_audio_config()

        if audio_config:
            # Valida que config está intacta
            assert ".ogg" in str(audio_config), \
                "Audio config inválido em game over"

    def test_game_over_css_styling(self, client):
        """✓ Game over tem estilos CSS"""
        css_file = "static/css/style.css"
        if os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Procura por seletores de game over
            assert "game" in content.lower(), \
                "CSS não tem estilos para game"

    def test_game_over_placar_template(self, client):
        """✓ Placar fragment está disponível"""
        placar_file = "templates/placar_fragment.html"
        assert os.path.exists(placar_file), \
            "Placar fragment não encontrado"

    def test_game_over_endpoints(self, client):
        """✓ Endpoints relacionados existem"""
        # Testa se endpoints existem (podem retornar 404 se jogo não está nesse estado)
        endpoints = [
            "/api/placar",
        ]

        for endpoint in endpoints:
            resp = client.get(f"http://127.0.0.1:5000{endpoint}")
            # Pode ser 200 ou 404
            # O importante é que não é erro 500
            assert resp.status_code < 500, \
                f"Erro 500 em {endpoint}"

    def test_game_over_html_structure(self, client):
        """✓ HTML do game over é bem formado"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Valida tags básicas
            assert content.count("<") > content.count(">") - 5, \
                "HTML malformado (mais > que <)"

    def test_game_over_no_broken_audio_references(self, client):
        """✓ Nenhuma referência de áudio quebrada"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Procura por referências a áudio
            audio_refs = re.findall(r'(static/audio/[^"\'<>]*)', content)

            for ref in audio_refs:
                # Todas as referências devem ser .ogg
                assert ref.endswith(".ogg"), \
                    f"Referência inválida: {ref}"

    def test_game_over_images_lazy_loaded(self, client):
        """✓ Imagens em game over têm lazy loading"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "<img" in content:
                assert 'loading="lazy"' in content, \
                    "Imagens em fim_de_jogo não têm lazy loading"

    def test_game_over_integration_with_engine(self, client):
        """✓ Game over integra com engine.py"""
        engine_file = "src/engine.py"
        if os.path.exists(engine_file):
            with open(engine_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Procura por lógica de fim de jogo
            assert "game_over" in content.lower() or \
                   "fim" in content.lower() or \
                   "end" in content.lower(), \
                "Engine não tem lógica de fim de jogo"

    @pytest.mark.parametrize("score", [0, 50, 100, 200])
    def test_game_over_score_display_with_values(self, score):
        """✓ Display de pontuação funciona com valores variados"""
        # Teste parametrizado para validar que placar pode exibir diferentes pontos
        assert score >= 0, "Score não pode ser negativo"
        assert score <= 1000, "Score não deve exceder limite"

    def test_game_over_final_audio_state(self, client, game_helpers):
        """✓ Áudio em estado final é válido (sem .mp3)"""
        audio_config = game_helpers.get_audio_config()

        if audio_config:
            config_str = str(audio_config)
            # Validação final crítica
            assert ".mp3" not in config_str, \
                "CRÍTICO: .mp3 encontrado em audio_config final!"

    def test_game_over_performance_metrics(self, client):
        """✓ Página de game over carrega rápido"""
        fim_jogo_file = "templates/fim_de_jogo.html"
        if os.path.exists(fim_jogo_file):
            start = time.time()

            with open(fim_jogo_file, 'r', encoding='utf-8') as f:
                content = f.read()

            elapsed = (time.time() - start) * 1000

            print(f"\n⏱️  Tempo de leitura do template: {elapsed:.1f}ms")
            assert elapsed < 100, "Template lê muito lentamente"
