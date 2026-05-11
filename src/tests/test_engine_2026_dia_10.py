import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios2026_Dia10(unittest.TestCase):
    """Testes específicos para as ramificações do Dia 10 (2026)"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado: Negócio rodando a todo vapor em 2026.
        self.motor.estado = {
            "caixa": 3000,
            "stress": 50,
            "acervo": 120,
            "tracao": 100,
            "dia_atual": 10
        }

    def test_dia10_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 10"""
        # Exemplo: Mudança no algoritmo das redes sociais (Perde tração, gasta caixa para recuperar)
        impactos_opcao_1 = {"caixa": -300, "acervo": 0, "stress": 20, "tracao": -15}

        self.motor.aplicar_impacto(impactos_opcao_1)

        self.assertEqual(self.motor.estado["caixa"], 2700)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 70)
        self.assertEqual(self.motor.estado["tracao"], 85)

    def test_dia10_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 10"""
        # Exemplo: Vídeo viralizando organicamente (Explosão de caixa e tração, stress da demanda)
        impactos_opcao_2 = {"caixa": 800, "acervo": -10, "stress": 25, "tracao": 40}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 3800)
        self.assertEqual(self.motor.estado["acervo"], 110)
        self.assertEqual(self.motor.estado["stress"], 75)
        self.assertEqual(self.motor.estado["tracao"], 140)

    def test_dia10_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 10"""
        # Exemplo: Lançamento de um clube de assinaturas (Ganho estável, aumenta acervo)
        impactos_opcao_3 = {"caixa": 200, "acervo": 30, "stress": 10, "tracao": 20}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 3200)
        self.assertEqual(self.motor.estado["acervo"], 150)
        self.assertEqual(self.motor.estado["stress"], 60)
        self.assertEqual(self.motor.estado["tracao"], 120)

    def test_dia10_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 10"""
        # Exemplo: Concorrente tenta copiar seu modelo (Foco na equipe, reduz stress, mantém a base)
        impactos_opcao_4 = {"caixa": -150, "acervo": 0, "stress": -30, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 2850)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 20)
        self.assertEqual(self.motor.estado["tracao"], 105)

if __name__ == '__main__':
    unittest.main()