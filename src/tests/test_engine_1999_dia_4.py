import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios1999_Dia4(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 4 (1999)"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Jogador chegando no Dia 4.
        # Ajuste conforme o balanceamento esperado para o meio da semana 1.
        self.motor.estado = {
            "caixa": 900,
            "stress": 30,
            "acervo": 140,
            "tracao": 25,
            "dia_atual": 4
        }

    def test_dia4_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 4"""
        # Exemplo: Investimento em marketing local (panfletagem)
        impactos_opcao_1 = {"caixa": -150, "acervo": 0, "stress": 15, "tracao": 30}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 750)
        self.assertEqual(self.motor.estado["acervo"], 140)
        self.assertEqual(self.motor.estado["stress"], 45)
        self.assertEqual(self.motor.estado["tracao"], 55)

    def test_dia4_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 4"""
        # Exemplo: Compra de fitas usadas de um lote de vizinho
        impactos_opcao_2 = {"caixa": -250, "acervo": 60, "stress": 10, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 650)
        self.assertEqual(self.motor.estado["acervo"], 200)
        self.assertEqual(self.motor.estado["stress"], 40)
        self.assertEqual(self.motor.estado["tracao"], 30)

    def test_dia4_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 4"""
        # Exemplo: Promoção "Pague 2 Leve 3" no balcão
        impactos_opcao_3 = {"caixa": 100, "acervo": -10, "stress": 20, "tracao": 15}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1000)
        self.assertEqual(self.motor.estado["acervo"], 130)
        self.assertEqual(self.motor.estado["stress"], 50)
        self.assertEqual(self.motor.estado["tracao"], 40)

    def test_dia4_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 4"""
        # Exemplo: Ignorar evento e focar em limpeza/organização
        impactos_opcao_4 = {"caixa": 0, "acervo": 0, "stress": -20, "tracao": -5}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 900)
        self.assertEqual(self.motor.estado["acervo"], 140)
        self.assertEqual(self.motor.estado["stress"], 10)
        self.assertEqual(self.motor.estado["tracao"], 20)

if __name__ == '__main__':
    unittest.main()