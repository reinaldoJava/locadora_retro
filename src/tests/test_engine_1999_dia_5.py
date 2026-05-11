import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios1999_Dia5(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 5 (1999)"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Jogador chegando no Dia 5 (Sexta-feira).
        # A locadora já tem um bom caixa, mas a equipe está começando a cansar.
        self.motor.estado = {
            "caixa": 1200,
            "stress": 40,
            "acervo": 160,
            "tracao": 40,
            "dia_atual": 5
        }

    def test_dia5_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 5"""
        # Exemplo: Lidar com o pico de clientes da sexta-feira (Ganha caixa, sobe stress)
        impactos_opcao_1 = {"caixa": 300, "acervo": -10, "stress": 25, "tracao": 20}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 1500)
        self.assertEqual(self.motor.estado["acervo"], 150)
        self.assertEqual(self.motor.estado["stress"], 65)
        self.assertEqual(self.motor.estado["tracao"], 60)

    def test_dia5_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 5"""
        # Exemplo: Comprar lançamentos caros para o fim de semana (Gasta caixa, sobe acervo)
        impactos_opcao_2 = {"caixa": -300, "acervo": 60, "stress": 10, "tracao": 15}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 900)
        self.assertEqual(self.motor.estado["acervo"], 220)
        self.assertEqual(self.motor.estado["stress"], 50)
        self.assertEqual(self.motor.estado["tracao"], 55)

    def test_dia5_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 5"""
        # Exemplo: Fazer uma confraternização rápida com a equipe (Paga caixa, reduz stress)
        impactos_opcao_3 = {"caixa": -100, "acervo": 0, "stress": -25, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1100)
        self.assertEqual(self.motor.estado["acervo"], 160)
        self.assertEqual(self.motor.estado["stress"], 15)
        self.assertEqual(self.motor.estado["tracao"], 45)

    def test_dia5_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 5"""
        # Exemplo: Vender fitas velhas para fazer um caixa rápido
        impactos_opcao_4 = {"caixa": 150, "acervo": -30, "stress": 0, "tracao": -5}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 1350)
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 40)
        self.assertEqual(self.motor.estado["tracao"], 35)

if __name__ == '__main__':
    unittest.main()