import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios2026_Dia9(unittest.TestCase):
    """Testes específicos para as ramificações do Dia 9 (2026)"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Jogador estabilizado na nova realidade de 2026.
        # Os números de caixa e tração são naturalmente maiores nesta era.
        self.motor.estado = {
            "caixa": 2500,
            "stress": 45,
            "acervo": 110,
            "tracao": 90,
            "dia_atual": 9
        }

    def test_dia9_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 9"""
        # Exemplo: Investimento pesado em tráfego pago / marketing digital
        impactos_opcao_1 = {"caixa": -400, "acervo": 0, "stress": 10, "tracao": 50}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 2100)
        self.assertEqual(self.motor.estado["acervo"], 110)
        self.assertEqual(self.motor.estado["stress"], 55)
        self.assertEqual(self.motor.estado["tracao"], 140)

    def test_dia9_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 9"""
        # Exemplo: Problemas com o servidor / internet cai (Prejuízo financeiro e de stress)
        impactos_opcao_2 = {"caixa": -200, "acervo": 0, "stress": 30, "tracao": -10}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 2300)
        self.assertEqual(self.motor.estado["acervo"], 110)
        self.assertEqual(self.motor.estado["stress"], 75)
        self.assertEqual(self.motor.estado["tracao"], 80)

    def test_dia9_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 9"""
        # Exemplo: Parceria com influenciador local (Gera muito caixa e tração)
        impactos_opcao_3 = {"caixa": 500, "acervo": 10, "stress": 20, "tracao": 40}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 3000)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 65)
        self.assertEqual(self.motor.estado["tracao"], 130)

    def test_dia9_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 9"""
        # Exemplo: Atualização de software/equipamentos internos (Reduz stress a longo prazo)
        impactos_opcao_4 = {"caixa": -300, "acervo": 20, "stress": -25, "tracao": 15}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 2200)
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 20)
        self.assertEqual(self.motor.estado["tracao"], 105)

if __name__ == '__main__':
    unittest.main()