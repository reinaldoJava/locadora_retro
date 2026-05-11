import unittest
import sys
import os

# Garantindo que o pytest ache a pasta src
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, caminho_raiz)
from src.engine import Engine

class TestCenarios1999_Dia2(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 2 (1999)"""

    def setUp(self):
        self.motor = Engine()
        # Aqui simulamos um estado intermediário, como se o jogador
        # já tivesse passado pelo Dia 1. Você pode ajustar esses valores base
        # para refletir uma média de como o jogador chega no Dia 2.
        self.motor.estado = {
            "caixa": 850,
            "stress": 10,
            "acervo": 110,
            "tracao": 5,
            "dia_atual": 2
        }

    def test_dia2_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 2"""
        # Substitua pelos impactos reais do seu JSON para a Opção 1 do Dia 2
        impactos_opcao_1 = {"caixa": 100, "acervo": -5, "stress": 15, "tracao": 10}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 950)
        self.assertEqual(self.motor.estado["acervo"], 105)
        self.assertEqual(self.motor.estado["stress"], 25)
        self.assertEqual(self.motor.estado["tracao"], 15)

    def test_dia2_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 2"""
        # Substitua pelos impactos reais do seu JSON para a Opção 2 do Dia 2
        impactos_opcao_2 = {"caixa": -200, "acervo": 30, "stress": -5, "tracao": 20}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 650)
        self.assertEqual(self.motor.estado["acervo"], 140)
        self.assertEqual(self.motor.estado["stress"], 5)
        self.assertEqual(self.motor.estado["tracao"], 25)

    def test_dia2_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 2"""
        # Substitua pelos impactos reais do seu JSON para a Opção 3 do Dia 2
        impactos_opcao_3 = {"caixa": 50, "acervo": 0, "stress": 30, "tracao": -10}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 900)
        self.assertEqual(self.motor.estado["acervo"], 110)
        self.assertEqual(self.motor.estado["stress"], 40)
        self.assertEqual(self.motor.estado["tracao"], -5)

    def test_dia2_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 2"""
        # Substitua pelos impactos reais do seu JSON para a Opção 4 do Dia 2
        impactos_opcao_4 = {"caixa": -50, "acervo": 10, "stress": 0, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 800)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 10)
        self.assertEqual(self.motor.estado["tracao"], 10)