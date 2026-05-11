import unittest
import sys
import os

# Garantindo que o pytest ache a pasta src
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestMotorBasico(unittest.TestCase):
    """Testes corrigidos baseados no comportamento real da sua Engine"""

    def setUp(self):
        self.motor = Engine()
        self.motor.estado = {"caixa": 100, "stress": 20, "acervo": 100, "tracao": 50, "dia_atual": 1}

    def test_game_over_burnout_equipe(self):
        """Testa se o jogo acaba quando o stress passa do limite."""
        self.motor.estado["stress"] = 110
        derrota, motivo = self.motor.verificar_game_over()

        self.assertTrue(derrota)
        # Verifica se a mensagem real de colapso nervoso foi acionada
        self.assertIn("colapso", motivo.lower())

    def test_jogo_continua_status_normais(self):
        """Testa se o jogo permite continuar retornando uma string vazia."""
        derrota, motivo = self.motor.verificar_game_over()

        self.assertFalse(derrota)
        self.assertEqual(motivo, '') # Corrigido para esperar '' ao invés de None


class TestCenarios1999_Dia1(unittest.TestCase):
    """Testes específicos para todas as ramificações do Dia 1 (1999)"""

    def setUp(self):
        self.motor = Engine()
        # Estado exato que o jogador começa no Dia 1
        self.motor.estado = {
            "caixa": 1000,
            "stress": 0,
            "acervo": 100,
            "tracao": 0,
            "dia_atual": 1
        }

    def test_dia1_opcao_1(self):
        """Testa o cenário da Opção 1 do Dia 1"""
        # Substitua estes valores pelos impactos REAIS da opção 1 do seu JSON
        impactos_opcao_1 = {"caixa": -150, "acervo": 20, "stress": 10, "tracao": 5}

        self.motor.aplicar_impacto(impactos_opcao_1)

        # Validando se a matemática do cenário fechou perfeitamente
        self.assertEqual(self.motor.estado["caixa"], 850)
        self.assertEqual(self.motor.estado["acervo"], 120)
        self.assertEqual(self.motor.estado["stress"], 10)
        self.assertEqual(self.motor.estado["tracao"], 5)

    def test_dia1_opcao_2(self):
        """Testa o cenário da Opção 2 do Dia 1"""
        # Substitua estes valores pelos impactos REAIS da opção 2 do seu JSON
        impactos_opcao_2 = {"caixa": -300, "acervo": 50, "stress": 25, "tracao": 15}

        self.motor.aplicar_impacto(impactos_opcao_2)

        self.assertEqual(self.motor.estado["caixa"], 700)
        self.assertEqual(self.motor.estado["acervo"], 150)
        self.assertEqual(self.motor.estado["stress"], 25)
        self.assertEqual(self.motor.estado["tracao"], 15)

    def test_dia1_opcao_3(self):
        """Testa o cenário da Opção 3 do Dia 1"""
        # Substitua estes valores pelos impactos REAIS da opção 3 do seu JSON
        impactos_opcao_3 = {"caixa": 200, "acervo": -10, "stress": 30, "tracao": -5}

        self.motor.aplicar_impacto(impactos_opcao_3)

        self.assertEqual(self.motor.estado["caixa"], 1200)
        self.assertEqual(self.motor.estado["acervo"], 90)
        self.assertEqual(self.motor.estado["stress"], 30)
        self.assertEqual(self.motor.estado["tracao"], -5)

    def test_dia1_opcao_4(self):
        """Testa o cenário da Opção 4 do Dia 1"""
        # Substitua estes valores pelos impactos REAIS da opção 4 do seu JSON
        impactos_opcao_4 = {"caixa": 0, "acervo": 0, "stress": -10, "tracao": 10}

        self.motor.aplicar_impacto(impactos_opcao_4)

        self.assertEqual(self.motor.estado["caixa"], 1000)
        self.assertEqual(self.motor.estado["acervo"], 100)
        # Como o stress inicial era 0, dependendo da sua engine ele pode ficar negativo ou travar no 0.
        # Ajuste a expectativa abaixo dependendo de como o seu motor lida com status negativos.
        self.assertEqual(self.motor.estado["stress"], -10)
        self.assertEqual(self.motor.estado["tracao"], 10)

if __name__ == '__main__':
    unittest.main()