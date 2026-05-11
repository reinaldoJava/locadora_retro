import unittest
import sys
import os

# Garantindo que o Python localize a pasta src a partir da pasta tests
caminho_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if caminho_raiz not in sys.path:
    sys.path.insert(0, caminho_raiz)

from src.engine import Engine

class TestCenarios2026_Dia8(unittest.TestCase):
    """Testes para o Dia 8 (2026) - O primeiro dia da nova realidade!"""

    def setUp(self):
        self.motor = Engine()
        # Estado simulado após o salto temporal.
        # Os números refletem a locadora já transformada no novo modelo de negócios.
        self.motor.estado = {
            "caixa": 2000,
            "stress": 50,
            "acervo": 100,
            "tracao": 80,
            "dia_atual": 8
        }

    def test_dia8_rotaA_evento_malu2000(self):
        """Testa uma opção do evento da Rota A (Estúdio Y2K / Malu2000)"""
        # Substitua pelos impactos reais de uma das opções do evento 'evento_malu2000'
        impactos_rota_a = {"caixa": 300, "acervo": 0, "stress": 15, "tracao": 25}

        self.motor.aplicar_impacto(impactos_rota_a)

        self.assertEqual(self.motor.estado["caixa"], 2300)
        self.assertEqual(self.motor.estado["acervo"], 100)
        self.assertEqual(self.motor.estado["stress"], 65)
        self.assertEqual(self.motor.estado["tracao"], 105)

    def test_dia8_rotaB_evento_mercado_livre(self):
        """Testa uma opção do evento da Rota B (Colecionismo / Mercado Livre)"""
        # Substitua pelos impactos reais de uma das opções do evento 'evento_mercado_livre'
        impactos_rota_b = {"caixa": 600, "acervo": -10, "stress": 10, "tracao": 10}

        self.motor.aplicar_impacto(impactos_rota_b)

        self.assertEqual(self.motor.estado["caixa"], 2600)
        self.assertEqual(self.motor.estado["acervo"], 90)
        self.assertEqual(self.motor.estado["stress"], 60)
        self.assertEqual(self.motor.estado["tracao"], 90)

    def test_dia8_rotaC_evento_detox(self):
        """Testa uma opção do evento da Rota C (Detox Digital)"""
        # Substitua pelos impactos reais de uma das opções do evento 'evento_detox_digital'
        impactos_rota_c = {"caixa": 200, "acervo": 0, "stress": -20, "tracao": 30}

        self.motor.aplicar_impacto(impactos_rota_c)

        self.assertEqual(self.motor.estado["caixa"], 2200)
        self.assertEqual(self.motor.estado["acervo"], 100)
        self.assertEqual(self.motor.estado["stress"], 30)
        self.assertEqual(self.motor.estado["tracao"], 110)

    def test_dia8_rotaD_evento_cine_pub(self):
        """Testa uma opção do evento da Rota D (Bar / Cine Pub)"""
        # Substitua pelos impactos reais de uma das opções do evento 'evento_cine_pub'
        impactos_rota_d = {"caixa": 400, "acervo": 0, "stress": 30, "tracao": 40}

        self.motor.aplicar_impacto(impactos_rota_d)

        self.assertEqual(self.motor.estado["caixa"], 2400)
        self.assertEqual(self.motor.estado["acervo"], 100)
        self.assertEqual(self.motor.estado["stress"], 80)
        self.assertEqual(self.motor.estado["tracao"], 120)

if __name__ == '__main__':
    unittest.main()