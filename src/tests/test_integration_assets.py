"""
test_integration_assets.py — Integração: Assets (Vídeo, Imagens, Lazy Load)
Valida:
- Video otimizado carrega sem erro
- Imagens WebP carregam
- Lazy loading funciona (imagens não carregam até visível)
"""

import pytest


class TestAssetsIntegration:
    """Suite Integração: Assets system"""

    def test_video_wormhole_exists_and_accessible(self, client):
        """✓ Vídeo wormhole.mp4 existe e é acessível"""
        resp = client.head("http://127.0.0.1:5000/static/video/wormhole.mp4")

        # Arquivo deve existir
        assert resp.status_code in [200, 304], \
            f"Vídeo wormhole não acessível: {resp.status_code}"

    def test_video_wormhole_is_optimized(self, client):
        """✓ Vídeo wormhole.mp4 está otimizado (<2MB)"""
        resp = client.head("http://127.0.0.1:5000/static/video/wormhole.mp4")

        if resp.status_code == 200:
            size_bytes = int(resp.headers.get("content-length", 0))
            size_mb = size_bytes / (1024 * 1024)

            # Esperado: ~700KB após otimização com H.265
            print(f"\n📊 Tamanho wormhole.mp4: {size_mb:.2f} MB")

            # Validação: deve ser menor que 2MB
            assert size_mb < 2, f"Vídeo muito grande: {size_mb:.2f} MB"

    def test_all_background_images_exist(self, client):
        """✓ Todas as imagens de background existem"""
        backgrounds = [
            "/static/img/bg_1999.webp",
            "/static/img/bg_2026.webp",
            "/static/img/bg_undefined.webp",
            "/static/img/bg_2026_artefatos.webp",
            "/static/img/bg_2026_detox.webp",
            "/static/img/bg_2026_pub.webp",
            "/static/img/bg_2026_y2k_set.webp",
        ]

        for bg in backgrounds:
            resp = client.head(f"http://127.0.0.1:5000{bg}")
            assert resp.status_code in [200, 304], \
                f"Background não acessível: {bg}"

    def test_all_character_images_exist(self, client):
        """✓ Todas as imagens de personagens existem"""
        characters = [
            "/static/img/leila.webp",
            "/static/img/marcos.webp",
            "/static/img/influenciadora.webp",
            "/static/img/jovem_genZ.webp",
            "/static/img/gerente.webp",
            "/static/img/vagner.webp",
            "/static/img/mauricio.webp",
        ]

        for char in characters:
            resp = client.head(f"http://127.0.0.1:5000{char}")
            assert resp.status_code in [200, 304], \
                f"Personagem não acessível: {char}"

    def test_all_audio_files_exist(self, client):
        """✓ Todos os arquivos de áudio (.ogg) existem"""
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

        for audio in audio_files:
            resp = client.head(f"http://127.0.0.1:5000{audio}")
            assert resp.status_code in [200, 304], \
                f"Áudio não acessível: {audio}"

    def test_no_mp3_files_accessible(self, client):
        """✓ Nenhum arquivo .mp3 está acessível"""
        # Tenta acessar um .mp3 que deveria ter sido removido
        resp = client.head("http://127.0.0.1:5000/static/audio/Game_1999.mp3")

        # Status deve ser 404 (não encontrado)
        assert resp.status_code == 404, \
            "CRÍTICO: Arquivo .mp3 ainda está acessível!"

    def test_lazy_loading_in_templates(self):
        """✓ Templates contêm atributo loading='lazy' em <img>"""
        import os

        # Valida templates principais
        templates = [
            "templates/index.html",
            "templates/game_ui.html",
            "templates/cinematic_1999_to_2026.html",
        ]

        for template in templates:
            if os.path.exists(template):
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Se tem <img>, deve ter lazy loading
                if "<img" in content:
                    assert 'loading="lazy"' in content, \
                        f"{template} tem <img> mas sem lazy loading"

    def test_images_in_webp_format(self, client):
        """✓ Imagens estão em formato WebP"""
        # Testa que imagens WebP existem
        webp_images = [
            "/static/img/leila.webp",
            "/static/img/marcos.webp",
            "/static/img/bg_1999.webp",
        ]

        for img in webp_images:
            resp = client.head(f"http://127.0.0.1:5000{img}")
            # Deve existir em .webp
            assert resp.status_code in [200, 304], \
                f"Imagem WebP não encontrada: {img}"

    def test_image_sizes_reasonable(self, client):
        """✓ Imagens têm tamanho razoável (<500KB cada)"""
        # Testa algumas imagens críticas
        test_images = [
            "/static/img/leila.webp",
            "/static/img/marcos.webp",
        ]

        for img in test_images:
            resp = client.head(f"http://127.0.0.1:5000{img}")

            if resp.status_code == 200:
                size_bytes = int(resp.headers.get("content-length", 0))
                size_kb = size_bytes / 1024

                # WebP com qualidade boa deve ser < 500KB
                print(f"\n📊 Tamanho {img}: {size_kb:.1f} KB")

                # Validação: não muito grande
                assert size_kb < 500, f"Imagem muito grande: {img} ({size_kb:.1f} KB)"

    def test_video_content_type_correct(self, client):
        """✓ Vídeo tem content-type correto (video/mp4)"""
        resp = client.head("http://127.0.0.1:5000/static/video/wormhole.mp4")

        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "").lower()

            # Deve ser video/mp4 (ou mp4)
            assert "video" in content_type or "mp4" in content_type, \
                f"Content-type incorreto: {content_type}"
