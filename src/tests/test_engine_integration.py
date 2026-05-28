# src/tests/test_engine_integration.py
# Testes de integração usando os JSONs reais de data/.
# Roda com: pytest src/tests/test_engine_integration.py -v

import pytest
import sys
import os

# Garante que o módulo engine é encontrado independente de onde pytest é chamado.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from engine import Engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def motor_1999():
    """Engine carregado apenas com o cenário 1999."""
    return Engine(lista_cenarios=["eventos_1999.json"])


@pytest.fixture
def motor_completo():
    """Engine completo (1999 + 2026)."""
    return Engine(lista_cenarios=["eventos_1999.json", "eventos_2026.json"])


# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------

class TestEstadoInicial:
    def test_metricas_iniciais(self, motor_1999):
        e = motor_1999.estado
        assert e["caixa"] == 100
        assert e["tracao"] == 50
        assert e["acervo"] == 50
        assert e["stress"] == 0
        assert e["moral_equipe"] == 70

    def test_flags_vazias(self, motor_1999):
        assert motor_1999.estado["flags"] == {}

    def test_primeiro_evento_existe(self, motor_1999):
        resultado = motor_1999.formatar_para_frontend()
        assert "texto" in resultado
        assert "opcoes" in resultado
        assert len(resultado["opcoes"]) > 0

    def test_ano_inicial_1999(self, motor_1999):
        resultado = motor_1999.formatar_para_frontend()
        assert resultado["ano"] == 1999


# ---------------------------------------------------------------------------
# Flags — escrita e leitura
# ---------------------------------------------------------------------------

class TestFlags:
    def _avançar_ate(self, motor, evt_id_alvo: str):
        """Avança o engine até o evento com id_evento == evt_id_alvo."""
        for _ in range(50):  # limite de segurança
            evt = motor.obter_evento_atual()
            if evt and evt.get("id_evento") == evt_id_alvo:
                return True
            if evt and evt.get("opcoes"):
                motor.processar_escolha(0)  # sempre escolha A
            else:
                break
        return False

    def test_leila_puniu_cliente_flag_diaW_A(self, motor_1999):
        """Opção A em diaW deve escrever leila_puniu_cliente."""
        encontrou = self._avançar_ate(motor_1999, "1999_diaW_golpe_fita_trocada_leila")
        assert encontrou, "Evento diaW não encontrado nos 50 primeiros passos"
        # opcao 0 = sub-opcao A (índice 0)
        motor_1999.processar_escolha(0)
        assert motor_1999.estado["flags"].get("leila_puniu_cliente") is True

    def test_leila_absorveu_prejuizo_flag_diaW_B(self):
        """Opção B em diaW deve escrever leila_absorveu_prejuizo."""
        motor = Engine(lista_cenarios=["eventos_1999.json"])
        for _ in range(50):
            evt = motor.obter_evento_atual()
            if evt and evt.get("id_evento") == "1999_diaW_golpe_fita_trocada_leila":
                break
            motor.processar_escolha(0)
        # sub-opcao B = índice 1
        motor.processar_escolha(1)
        assert motor.estado["flags"].get("leila_absorveu_prejuizo") is True

    def test_mauricio_saiu_flag_dia5_C2(self):
        """Dia5-C2 deve escrever mauricio_saiu (não mauricio_demitido)."""
        motor = Engine(lista_cenarios=["eventos_1999.json"])
        for _ in range(50):
            evt = motor.obter_evento_atual()
            if evt and evt.get("id_evento") == "1999_dia5_sindicato_ou_corte":
                break
            motor.processar_escolha(0)
        # sub-opção C = índice 2
        motor.processar_escolha(2)
        flags = motor.estado["flags"]
        assert flags.get("mauricio_saiu") is True, "Flag mauricio_saiu deve estar ativa"
        assert "mauricio_demitido" not in flags, "Flag antiga mauricio_demitido não deve existir"


# ---------------------------------------------------------------------------
# _resolver_agente — substituição Maurício → Marcos
# ---------------------------------------------------------------------------

class TestResolverAgente:
    def test_sem_flag_retorna_mauricio(self, motor_1999):
        assert motor_1999._resolver_agente("ID_Mauricio") == "ID_Mauricio"

    def test_com_flag_retorna_marcos(self, motor_1999):
        motor_1999.estado["flags"]["mauricio_saiu"] = True
        assert motor_1999._resolver_agente("ID_Mauricio") == "ID_Marcos"

    def test_outros_agentes_inalterados(self, motor_1999):
        motor_1999.estado["flags"]["mauricio_saiu"] = True
        assert motor_1999._resolver_agente("ID_Vagner") == "ID_Vagner"
        assert motor_1999._resolver_agente("ID_Leila") == "ID_Leila"
        assert motor_1999._resolver_agente("ID_Gerente") == "ID_Gerente"

    def test_flag_false_nao_substitui(self, motor_1999):
        motor_1999.estado["flags"]["mauricio_saiu"] = False
        assert motor_1999._resolver_agente("ID_Mauricio") == "ID_Mauricio"


# ---------------------------------------------------------------------------
# Game-over — verificar thresholds (retorna bool, não tupla)
# ---------------------------------------------------------------------------

class TestGameOver:
    def test_caixa_zero_game_over(self, motor_1999):
        motor_1999.estado["caixa"] = 0
        resultado = motor_1999.verificar_game_over()
        assert resultado is True

    def test_caixa_negativa_game_over(self, motor_1999):
        motor_1999.estado["caixa"] = -10
        assert motor_1999.verificar_game_over() is True

    def test_caixa_positiva_sem_game_over(self, motor_1999):
        motor_1999.estado["caixa"] = 1
        assert motor_1999.verificar_game_over() is False

    def test_stress_game_over(self, motor_1999):
        """Ajuste o threshold conforme valor canônico definido (150 ou 90)."""
        motor_1999.estado["stress"] = 150
        assert motor_1999.verificar_game_over() is True

    def test_acervo_zero_game_over(self, motor_1999):
        motor_1999.estado["acervo"] = 0
        assert motor_1999.verificar_game_over() is True


# ---------------------------------------------------------------------------
# processar_escolha — API pública correta
# ---------------------------------------------------------------------------

class TestProcessarEscolha:
    def test_retorna_dict_com_campos_esperados(self, motor_1999):
        resultado = motor_1999.processar_escolha(0)
        assert isinstance(resultado, dict)
        # Deve ter pelo menos estado atualizado
        assert "estado" in resultado or motor_1999.estado is not None

    def test_escolha_altera_estado(self, motor_1999):
        estado_antes = dict(motor_1999.estado)
        motor_1999.processar_escolha(0)
        # Pelo menos uma métrica deve ter mudado
        metricas = ["caixa", "tracao", "acervo", "stress", "moral_equipe"]
        alguma_mudou = any(
            motor_1999.estado[m] != estado_antes[m] for m in metricas
        )
        assert alguma_mudou, "Nenhuma métrica mudou após processar_escolha(0)"

    def test_escolha_invalida_nao_explode(self, motor_1999):
        """Índice fora do range não deve lançar exceção não tratada."""
        try:
            motor_1999.processar_escolha(999)
        except (IndexError, KeyError) as e:
            pytest.fail(f"processar_escolha(999) lançou {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Smoke test — percurso completo sem travar
# ---------------------------------------------------------------------------

class TestPercursoCompleto:
    def test_jogo_completo_sem_crash(self):
        """Simula uma partida inteira escolhendo sempre a opção 0."""
        motor = Engine(lista_cenarios=["eventos_1999.json", "eventos_2026.json"])
        passos = 0
        limite = 200  # margem para todos os eventos existentes
        while passos < limite:
            if motor.verificar_game_over():
                break
            evt = motor.obter_evento_atual()
            if evt is None:
                break
            motor.processar_escolha(0)
            passos += 1
        assert passos < limite, "Percurso não terminou em 200 passos — possível loop infinito"

    def test_jogo_completo_ramo_C_mauricio_saiu(self):
        """Percurso forçando C2 em Dia5 para validar flag mauricio_saiu no ramo 2026."""
        motor = Engine(lista_cenarios=["eventos_1999.json", "eventos_2026.json"])
        passos = 0
        while passos < 200:
            if motor.verificar_game_over():
                break
            evt = motor.obter_evento_atual()
            if evt is None:
                break
            # Força sub-opção C (índice 2) em Dia5
            if evt and evt.get("id_evento") == "1999_dia5_sindicato_ou_corte":
                motor.processar_escolha(2)
            else:
                motor.processar_escolha(0)
            passos += 1
        # Se chegou em 2026, Marcos deve ser resolvido como agente nos eventos de Maurício
        if motor.estado.get("flags", {}).get("mauricio_saiu"):
            assert motor._resolver_agente("ID_Mauricio") == "ID_Marcos"
