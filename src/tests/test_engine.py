import pytest
import sys
import os

# Adiciona a pasta src ao path para os testes acharem o engine.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from engine import Engine

@pytest.fixture
def motor():
    """Fixture do Pytest para iniciar um motor limpo antes de cada teste."""
    return Engine()

def test_aplicar_impacto_basico(motor):
    impacto = {"tracao": 2, "acervo": -1, "caixa": 50, "stress": 1}
    motor.aplicar_impacto(impacto)

    assert motor.estado["tracao"] == 2
    assert motor.estado["acervo"] == -1
    assert motor.estado["caixa"] == 1050.0
    assert motor.estado["stress"] == 1

def test_game_over_falencia(motor):
    # Força o caixa a ficar negativo
    motor.aplicar_impacto({"caixa": -1001.0})
    acabou, motivo = motor.verificar_game_over()

    assert acabou is True
    assert "FALÊNCIA" in motivo

def test_game_over_tracao_alta(motor):
    motor.aplicar_impacto({"tracao": 5}) # Passa o limite de 4
    acabou, motivo = motor.verificar_game_over()

    assert acabou is True
    assert "CAOS URBANO" in motivo

def test_game_over_tracao_baixa(motor):
    motor.aplicar_impacto({"tracao": -5}) # Passa o limite negativo de -4
    acabou, motivo = motor.verificar_game_over()

    assert acabou is True
    assert "DESERTO" in motivo

def test_game_over_acervo_ruim(motor):
    motor.aplicar_impacto({"acervo": -5})
    acabou, motivo = motor.verificar_game_over()

    assert acabou is True
    assert "RUÍNA CULTURAL" in motivo

def test_game_over_stress_alto(motor):
    motor.aplicar_impacto({"stress": 5})
    acabou, motivo = motor.verificar_game_over()

    assert acabou is True
    assert "COLAPSO NERVOSO" in motivo

def test_vitoria_score_calculo(motor):
    # Simula um jogo vencido com recursos sobrando
    motor.estado["caixa"] = 1500.0  # +150 pontos
    motor.estado["tracao"] = 2      # +20 pontos
    motor.estado["acervo"] = 1      # +10 pontos
    motor.estado["stress"] = 1      # -20 pontos

    score = motor.calcular_score_final()
    # 150 + 20 + 10 - 20 = 160
    assert score == 160.0

def test_vitoria_score_nunca_negativo(motor):
    motor.estado["caixa"] = 0
    motor.estado["tracao"] = 0
    motor.estado["acervo"] = 0
    motor.estado["stress"] = 3  # Causaria -60 pontos

    score = motor.calcular_score_final()
    assert score == 0 # O score tem um limitador de zero (max(0, score))