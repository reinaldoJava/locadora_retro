import unittest
import sys
import os

# Garantindo que o pytest ache a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios1999_Dia3(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 3 (1999)"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado de como o jogador iniciaria o Dia 3.
        # Ajuste esses valores base conforme o balanceamento do seu jogo.
        self.motor.estado = {
            "caixa": 750,
            "stress": 20,
            "acervo": 120,
            "tracao": 15,
            "dia_atual": 3
        }

    def test_dia3_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 3"""
        # Substitua pelos impactos reais do seu JSON
        impactos_opcao_1 = {"caixa": -100, "acervo": 40, "stress": 10, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 650)
        self.assertEqual(self.motor.estado["acervo"], 160)
        self.assertEqual(self.motor.estado["stress"], 30)
        self.assertEqual(self.motor.estado["tracao"], 20)

    def test_dia3_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 3"""
        # Substitua pelos impactos reais do seu JSON
        impactos_opcao_2 = {"caixa": 150, "acervo": -20, "stress": 20, "tracao": -5}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 900)
        self.assertEqual(self.motor.estado["acervo"], 100)
        self.assertEqual(self.motor.estado["stress"], 40)
        self.assertEqual(self.motor.estado["tracao"], 10)

    def test_dia3_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 3"""
        # Substitua pelos impactos reais do seu JSON
        impactos_opcao_3 = {"caixa": 300, "acervo": 0, "stress": 35, "tracao": 15}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1050)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 55)
        self.assertEqual(self.motor.estado["tracao"], 30)

    def test_dia3_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 3"""
        # Substitua pelos impactos reais do seu JSON
        impactos_opcao_4 = {"caixa": -50, "acervo": 10, "stress": -10, "tracao": 0}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 700)
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 10)
        self.assertEqual(self.motor.estado["tracao"], 15)

if __name__ == '__main__':
    unittest.main()