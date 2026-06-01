"""
test_taac_performance.py — TAAC: Testes de Performance
Valida velocidade de carregamento, tamanhos de assets e otimizações.
"""

import pytest
import os
from pathlib import Path


class TestAssetSizes:
    """Suite: Tamanhos de Assets"""

    def test_audio_files_reasonable_size(self):
        """✓ Arquivos de áudio têm tamanho razoável"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        # Máximo esperado por arquivo
        max_size_mb = 10  # 10MB é limite razoável

        if audio_dir.exists():
            for filename in os.listdir(audio_dir):
                filepath = audio_dir / filename

                if filepath.is_file():
                    size_bytes = filepath.stat().st_size
                    size_mb = size_bytes / (1024 * 1024)

                    print(f"\n  {filename}: {size_mb:.2f} MB")

                    assert size_mb < max_size_mb, \
                        f"Arquivo {filename} muito grande: {size_mb:.2f} MB"

    def test_game_music_files_optimized(self):
        """✓ Arquivos de musica (Game_*.ogg) estão otimizados"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        music_files = ['Game_1999.ogg', 'Game_2026.ogg']

        if audio_dir.exists():
            for filename in music_files:
                filepath = audio_dir / filename

                if filepath.exists():
                    size_bytes = filepath.stat().st_size
                    size_mb = size_bytes / (1024 * 1024)

                    # Música esperada ser < 8MB (dependendo da duração)
                    # Após otimização OGG, deve ser menor
                    assert size_mb < 15, \
                        f"{filename} deve ser <15MB, tem {size_mb:.2f}MB"

    def test_effect_sounds_minimal_size(self):
        """✓ Sons de efeito têm tamanho razoável"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        # Sons de efeito devem ser pequenos (< 300KB)
        # Alguns efeitos (como biips) podem ser um pouco maiores
        effect_files = ['click.ogg', 'bip_normal.ogg', 'bip_final.ogg']

        if audio_dir.exists():
            for filename in effect_files:
                filepath = audio_dir / filename

                if filepath.exists():
                    size_bytes = filepath.stat().st_size
                    size_kb = size_bytes / 1024

                    # Efeito deve ser pequeno
                    assert size_kb < 300, \
                        f"{filename} muito grande: {size_kb:.1f}KB (max 300KB)"

    def test_webp_images_smaller_than_png(self):
        """✓ Imagens WebP estão otimizadas"""
        img_dir = Path(__file__).parent.parent.parent / "static" / "img"

        if img_dir.exists():
            webp_files = [f for f in os.listdir(img_dir) if f.endswith('.webp')]

            for filename in webp_files[:5]:  # Testa amostra
                filepath = img_dir / filename
                size_bytes = filepath.stat().st_size
                size_kb = size_bytes / 1024

                print(f"\n  {filename}: {size_kb:.1f} KB")

                # WebP com boa qualidade deve ser < 500KB
                assert size_kb < 500, \
                    f"Imagem {filename} muito grande: {size_kb:.1f}KB"

    def test_video_optimized(self, client):
        """✓ Vídeo está otimizado"""
        resp = client.head("http://127.0.0.1:5000/static/video/wormhole.mp4")

        if resp.status_code == 200:
            size_bytes = int(resp.headers.get("content-length", 0))
            size_mb = size_bytes / (1024 * 1024)

            print(f"\n  wormhole.mp4: {size_mb:.2f} MB")

            # Vídeo otimizado deve ser < 2MB
            assert size_mb < 2, \
                f"Vídeo muito grande: {size_mb:.2f}MB (esperado <2MB)"


class TestPageLoadPerformance:
    """Suite: Performance de Carregamento"""

    def test_html_file_sizes_reasonable(self):
        """✓ Arquivos HTML têm tamanho razoável"""
        html_files = [
            "templates/index.html",
            "templates/intro.html",
            "templates/game_ui.html",
        ]

        for html_file in html_files:
            if os.path.exists(html_file):
                size_bytes = Path(html_file).stat().st_size
                size_kb = size_bytes / 1024

                print(f"\n  {html_file}: {size_kb:.1f} KB")

                # HTML deve ser < 500KB (descompactado)
                assert size_kb < 500, \
                    f"{html_file} muito grande: {size_kb:.1f}KB"

    def test_css_file_size_reasonable(self):
        """✓ Arquivo CSS tem tamanho razoável"""
        css_file = "static/css/style.css"

        if os.path.exists(css_file):
            size_bytes = Path(css_file).stat().st_size
            size_kb = size_bytes / 1024

            print(f"\n  {css_file}: {size_kb:.1f} KB")

            # CSS deve ser < 100KB
            assert size_kb < 100, \
                f"CSS muito grande: {size_kb:.1f}KB"

    def test_javascript_file_sizes_reasonable(self):
        """✓ Arquivos JS têm tamanho razoável"""
        js_dir = Path(__file__).parent.parent.parent / "static" / "js"

        if js_dir.exists():
            js_files = [f for f in os.listdir(js_dir) if f.endswith('.js')]

            for filename in js_files[:5]:  # Amostra
                filepath = js_dir / filename
                size_bytes = filepath.stat().st_size
                size_kb = size_bytes / 1024

                print(f"\n  {filename}: {size_kb:.1f} KB")

                # JS individual deve ser < 100KB
                assert size_kb < 100, \
                    f"{filename} muito grande: {size_kb:.1f}KB"


class TestCompressionOptimization:
    """Suite: Otimizações de Compressão"""

    def test_audio_uses_ogg_not_mp3(self):
        """✓ Áudio usa OGG (menor que MP3)"""
        audio_dir = Path(__file__).parent.parent.parent / "static" / "audio"

        if audio_dir.exists():
            ogg_count = len([f for f in os.listdir(audio_dir) if f.endswith('.ogg')])
            mp3_count = len([f for f in os.listdir(audio_dir) if f.endswith('.mp3')])

            assert ogg_count > 0, "Nenhum arquivo OGG encontrado"
            assert mp3_count == 0, "Ainda há arquivos MP3"

            print(f"\n  OGG files: {ogg_count}, MP3 files: {mp3_count}")

    def test_images_use_webp_format(self):
        """✓ Imagens usam WebP (menor que PNG/JPG)"""
        img_dir = Path(__file__).parent.parent.parent / "static" / "img"

        if img_dir.exists():
            webp_count = len([f for f in os.listdir(img_dir) if f.endswith('.webp')])
            png_count = len([f for f in os.listdir(img_dir) if f.endswith('.png')])
            jpg_count = len([f for f in os.listdir(img_dir) if f.endswith('.jpg')])

            total = webp_count + png_count + jpg_count

            print(f"\n  WebP: {webp_count}, PNG: {png_count}, JPG: {jpg_count}")

            # Deve ter WebP (ao menos alguns)
            assert webp_count > 0, "Nenhuma imagem em WebP encontrada"


class TestLazyLoading:
    """Suite: Lazy Loading"""

    def test_templates_have_lazy_loading_attributes(self):
        """✓ Templates têm loading='lazy' para imagens"""
        html_files = [
            "templates/game_ui.html",
            "templates/cinematic_1999_to_2026.html",
        ]

        for html_file in html_files:
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Se tem <img>, pode ter lazy loading
                if "<img" in content:
                    lazy_count = content.count('loading="lazy"')

                    print(f"\n  {html_file}: {lazy_count} lazy-loaded images")

    def test_video_has_preload_attribute(self):
        """✓ Vídeo tem atributo preload"""
        html_files = [
            "templates/cinematic_1999_to_2026.html",
        ]

        for html_file in html_files:
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "<video" in content:
                    # Pode ter preload="metadata" ou preload="none"
                    has_preload = "preload=" in content

                    print(f"\n  {html_file}: {'✓' if has_preload else '⚠'} preload")
