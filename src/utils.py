from datetime import date

_MESES_PT = [
    "", "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

def data_hoje_ptbr():
    """Retorna a data atual no formato '21 de maio de 2026'."""
    hoje = date.today()
    return f"{hoje.day} de {_MESES_PT[hoje.month]} de {hoje.year}"

def formatar_dialogo(dialogo):
    """Formata um dict de dialogo como HTML. Substitui DATA_DE_HOJE."""
    agente = dialogo["agente"].replace("ID_", "")
    fala = dialogo["fala"].replace("DATA_DE_HOJE", data_hoje_ptbr())
    return (
        f"<p class='nome-personagem'>{agente}</p>"
        f"<p class='fala-dialogo'>{fala}</p>"
    )
