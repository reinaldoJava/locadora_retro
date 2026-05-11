import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios1999_Dia6(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 6 (1999) - O temido Sábado!"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Jogador chegando no Dia 6 (Sábado).
        # Muito movimento acumulado, estresse beirando a zona de perigo.
        self.motor.estado = {
            "caixa": 1400,
            "stress": 55,
            "acervo": 150,
            "tracao": 50,
            "dia_atual": 6
        }

    def test_dia6_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 6"""
        # Exemplo: O grande pico de sábado à noite (Lucro altíssimo, estresse nas alturas)
        impactos_opcao_1 = {"caixa": 400, "acervo": -20, "stress": 30, "tracao": 25}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 1800)
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 85)
        self.assertEqual(self.motor.estado["tracao"], 75)

    def test_dia6_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 6"""
        # Exemplo: Cobrar multas de atraso com rigor (Ganha um pouco de caixa, mas perde tração/simpatia)
        impactos_opcao_2 = {"caixa": 150, "acervo": 10, "stress": 15, "tracao": -15}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 1550)
        self.assertEqual(self.motor.estado["acervo"], 160)
        self.assertEqual(self.motor.estado["stress"], 70)
        self.assertEqual(self.motor.estado["tracao"], 35)

    def test_dia6_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 6"""
        # Exemplo: Chamar reforços (Pagar freelancer para ajudar no balcão e aliviar a equipe)
        impactos_opcao_3 = {"caixa": -150, "acervo": 0, "stress": -30, "tracao": 10}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1250)
        self.assertEqual(self.motor.estado["acervo"], 150)
        self.assertEqual(self.motor.estado["stress"], 25)
        self.assertEqual(self.motor.estado["tracao"], 60)

    def test_dia6_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 6"""
        # Exemplo: Fitas danificadas descobertas (Prejuízo no acervo, tenta remendar para não perder cliente)
        impactos_opcao_4 = {"caixa": -50, "acervo": -15, "stress": 20, "tracao": -5}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 1350)
        self.assertEqual(self.motor.estado["acervo"], 135)
        self.assertEqual(self.motor.estado["stress"], 75)
        self.assertEqual(self.motor.estado["tracao"], 45)

if __name__ == '__main__':
    unittest.main()