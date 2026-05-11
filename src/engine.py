# ==========================================
# engine.py - O Gestor de Estado e Regras
# ==========================================

class Engine:
    def __init__(self):
        # Estado inicial das barras e caixa
        self.estado = {
            "caixa": 1000.0,
            "tracao": 0,    # Escala agora é de -100 a +100
            "acervo": 0,    # Escala agora é de -100 a +100
            "stress": 0,    # Escala agora é de -100 a +100
            "dia_atual": 1
        }

        # Definições de limites reais para o Game Over
        self.LIMITE_BARRA = 100
        self.CAIXA_MINIMO = 0.0

    def renderizar_barra(self, valor, nome):
        """
        Cria uma representação visual para o terminal.
        Como a escala agora é 100, dividimos por 10 para ter até 10 blocos na tela.
        Isso não será usado na Interface Gráfica futura, mas ajuda no debug atual.
        """
        tamanho = 10 # 10 blocos para cada lado
        prenchimento = "#"
        vazio = " "

        # Normaliza o valor para a quantidade de blocos
        blocos = int(valor / 10)
        posicao = max(min(blocos, tamanho), -tamanho)

        if posicao > 0:
            barra = f"[{vazio * tamanho}|{prenchimento * posicao}{vazio * (tamanho - posicao)}]"
        elif posicao < 0:
            posicao_abs = abs(posicao)
            barra = f"[{vazio * (tamanho - posicao_abs)}{prenchimento * posicao_abs}|{vazio * tamanho}]"
        else:
            barra = f"[{vazio * tamanho}|{vazio * tamanho}]"

        return f"{nome.capitalize():<10} {barra} ({valor:+})"

    def aplicar_impacto(self, impacto):
        """
        Soma os valores de impacto do JSON ao estado atual.
        """
        for chave, valor in impacto.items():
            if chave in self.estado:
                self.estado[chave] += valor

    def verificar_game_over(self):
        """
        Verifica se alguma barra estourou ou se o dinheiro acabou.
        Retorna (True, "Mensagem") se o jogo acabou, ou (False, "") se continua.
        """
        # 1. Checar Falência
        if self.estado["caixa"] < self.CAIXA_MINIMO:
            return True, "🚨 FALÊNCIA! O caixa ficou negativo. Os agiotas e o banco lacraram a porta de aço."

        # 2. Checar Tração (Leila)
        if self.estado["tracao"] > self.LIMITE_BARRA:
            return True, "🚨 CAOS URBANO! A loja viralizou tanto que a multidão quebrou a montra e a polícia fechou tudo."
        if self.estado["tracao"] < -self.LIMITE_BARRA:
            return True, "🚨 DESERTO! Ninguém mais entra na loja. A Leila demitiu-se para trabalhar na Blockbuster."

        # 3. Checar Acervo (Maurício)
        if self.estado["acervo"] > self.LIMITE_BARRA:
            return True, "🚨 ELITISMO! O Maurício expulsou todos os clientes que não sabiam pronunciar 'Tarkovsky'. A loja faliu por falta de público."
        if self.estado["acervo"] < -self.LIMITE_BARRA:
            return True, "🚨 RUÍNA CULTURAL! O acervo virou lixo. O Maurício teve um colapso e ateou fogo às fitas de má qualidade."

        # 4. Checar Stress (Vagner)
        if self.estado["stress"] > self.LIMITE_BARRA:
            return True, "🚨 COLAPSO NERVOSO! O Vagner teve um ataque cardíaco com as contas e a fiscalização fechou a loja por irregularidades."

        return False, ""

    def mostrar_status_completo(self):
        """
        Imprime o painel de controle para o jogador.
        """
        print("\n" + "—" * 45)
        print(f"💰 CAIXA: R$ {self.estado['caixa']:.2f}")
        print(self.renderizar_barra(self.estado["tracao"], "Tração"))
        print(self.renderizar_barra(self.estado["acervo"], "Acervo"))
        print(self.renderizar_barra(self.estado["stress"], "Stress"))
        print("—" * 45)

    def calcular_score_final(self):
        """
        Calcula a pontuação final baseada no sucesso da gestão.
        """
        score = (self.estado["caixa"] / 10) + (self.estado["tracao"] * 10) + (self.estado["acervo"] * 10) - (self.estado["stress"] * 20)
        return max(0, score)