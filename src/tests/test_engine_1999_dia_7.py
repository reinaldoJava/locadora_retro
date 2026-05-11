import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios1999_Dia7_Encruzilhada(unittest.TestCase):
    """Testes para a Encruzilhada Mestra do Dia 7 (1999) - A grande decisão para 2026!"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Fim da semana 1. A locadora sobreviveu a 1999.
        # Os números refletem o acúmulo de uma gestão equilibrada até o domingo.
        self.motor.estado = {
            "caixa": 1500,
            "stress": 60,
            "acervo": 140,
            "tracao": 65,
            "dia_atual": 7
        }

    def test_dia7_opcao_1_estudio(self):
        """Testa o cenário da Opção 1: Rota Estúdio Y2K"""
        # Substitua pelos impactos reais do seu evento de encruzilhada (Rota A)
        impactos_opcao_1 = {"caixa": 500, "acervo": -30, "stress": -20, "tracao": 40}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 2000)
        self.assertEqual(self.motor.estado["acervo"], 110)
        self.assertEqual(self.motor.estado["stress"], 40)
        self.assertEqual(self.motor.estado["tracao"], 105)

    def test_dia7_opcao_2_colecionismo(self):
        """Testa o cenário da Opção 2: Rota Artefatos Históricos"""
        # Substitua pelos impactos reais do seu evento de encruzilhada (Rota B)
        impactos_opcao_2 = {"caixa": 1000, "acervo": -80, "stress": -10, "tracao": 20}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 2500)
        self.assertEqual(self.motor.estado["acervo"], 60) # Acervo cai drasticamente pois foi vendido
        self.assertEqual(self.motor.estado["stress"], 50)
        self.assertEqual(self.motor.estado["tracao"], 85)

    def test_dia7_opcao_3_detox(self):
        """Testa o cenário da Opção 3: Rota Detox Digital"""
        # Substitua pelos impactos reais do seu evento de encruzilhada (Rota C)
        impactos_opcao_3 = {"caixa": -200, "acervo": 0, "stress": 30, "tracao": 50}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1300)
        self.assertEqual(self.motor.estado["acervo"], 140)
        self.assertEqual(self.motor.estado["stress"], 90) # Logística aumenta o stress
        self.assertEqual(self.motor.estado["tracao"], 115)

    def test_dia7_opcao_4_bar(self):
        """Testa o cenário da Opção 4: Rota Speakeasy (Bar)"""
        # Substitua pelos impactos reais do seu evento de encruzilhada (Rota D)
        impactos_opcao_4 = {"caixa": -500, "acervo": -10, "stress": 40, "tracao": 80}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 1000) # Gasto alto para reforma
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 100) # Bar gera muito stress inicial
        self.assertEqual(self.motor.estado["tracao"], 145)

if __name__ == '__main__':
    unittest.main()