#!/usr/bin/env python3
"""
validate_tests.py — Validação da estrutura de testes E2E (sem pytest)
Verifica se todos os arquivos estão corretos e prontos para rodar
"""

import os
import sys
import requests
from pathlib import Path

# Cores ANSI
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_file_exists(filepath, description):
    """Verifica se arquivo existe"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"{GREEN}OK{RESET} {description}")
        return True
    else:
        print(f"{RED}FAIL{RESET} {description}")
        return False

def check_file_content(filepath, search_term, should_have=True):
    """Verifica conteúdo do arquivo"""
    if not os.path.exists(filepath):
        return False

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    has_term = search_term in content

    if should_have and has_term:
        return True
    elif not should_have and not has_term:
        return True
    else:
        return False

def check_server(url):
    """Verifica se servidor está rodando"""
    try:
        resp = requests.head(url, timeout=2)
        return resp.status_code < 500
    except:
        return False

def main():
    print_header("VALIDACAO DE TESTES E2E - LOCADORA RETRO")

    # 1. Verificar estrutura de arquivos
    print(f"{YELLOW}[1/4] Verificando estrutura...{RESET}")
    files_ok = True

    test_files = [
        ("src/tests/conftest.py", "Infraestrutura pytest"),
        ("src/tests/test_e2e_intro_flow.py", "Testes: Intro"),
        ("src/tests/test_e2e_gameplay_1999.py", "Testes: 1999"),
        ("src/tests/test_e2e_transition_1999_2026.py", "Testes: Transicao"),
        ("src/tests/test_e2e_gameplay_2026.py", "Testes: 2026"),
        ("src/tests/test_e2e_game_over.py", "Testes: Game Over"),
        ("pytest.ini", "Config pytest"),
        ("run_tests_e2e.sh", "Script shell"),
    ]

    for filepath, description in test_files:
        if not check_file_exists(filepath, description):
            files_ok = False

    # 2. Verificar conteúdo crítico
    print(f"\n{YELLOW}[2/4] Validando conteudo critico...{RESET}")
    content_ok = True

    checks = [
        ("src/tests/conftest.py", "BASE_URL", "BASE_URL configurado"),
        ("src/tests/test_e2e_intro_flow.py", "test_intro_no_mp3", "Teste: sem MP3"),
        ("src/audio_config.py", ".ogg", "Audio config com OGG"),
    ]

    for filepath, term, description in checks:
        if check_file_content(filepath, term):
            print(f"{GREEN}OK{RESET} {description}")
        else:
            print(f"{RED}FAIL{RESET} {description}")
            content_ok = False

    # 3. Verificar produção (código, não testes)
    print(f"\n{YELLOW}[3/4] Validando producao (sem MP3)...{RESET}")
    prod_ok = True

    prod_files = [
        ("src/audio_config.py", ".mp3", False),
        ("static/js/audio_utils.js", ".mp3", False),
        ("templates/index.html", ".mp3", False),
        ("templates/intro.html", ".mp3", False),
    ]

    for filepath, term, should_have in prod_files:
        if os.path.exists(filepath):
            has_term = term in open(filepath, 'r', encoding='utf-8', errors='ignore').read()
            if not has_term:
                print(f"{GREEN}OK{RESET} {filepath} - sem MP3")
            else:
                print(f"{RED}FAIL{RESET} {filepath} - AINDA TEM MP3!")
                prod_ok = False

    # 4. Verificar servidor
    print(f"\n{YELLOW}[4/4] Verificando servidor...{RESET}")
    server_ok = False

    urls = [("http://127.0.0.1:5000", "127.0.0.1:5000"), ("http://localhost:5000", "localhost:5000")]

    for url, label in urls:
        if check_server(url):
            print(f"{GREEN}OK{RESET} Servidor em {label}")
            server_ok = True
            break

    if not server_ok:
        print(f"{YELLOW}SKIP{RESET} Servidor (inicie com: python app.py)")

    # Resumo
    print_header("RESUMO")

    total_checks = [
        ("Estrutura", files_ok),
        ("Conteudo", content_ok),
        ("Producao", prod_ok),
    ]

    passed = sum(1 for _, ok in total_checks if ok)

    for name, ok in total_checks:
        status = f"{GREEN}OK{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"{status} {name}")

    print(f"\nResultado: {passed}/{len(total_checks)}")

    if passed == len(total_checks):
        print(f"\n{GREEN}TUDO PRONTO!{RESET}")
        print(f"1. Inicie servidor: python app.py")
        print(f"2. Em outro terminal: bash run_tests_e2e.sh\n")
        return 0
    else:
        print(f"\n{RED}Problemas encontrados{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
