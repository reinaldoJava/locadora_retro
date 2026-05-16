
let nomeDoJogadorSessao = "";

async function carregarDia() {
    try {
        // CIRÚRGICO: O "const" define a variável, e o fetch busca os dados
        const res = await fetch('/api/proximo-evento');

        // Converte a resposta para JSON
        const data = await res.json();

        // CIRÚRGICO: Retorna os dados para o Maestro (game.js) usar
        return data;

    } catch (erro) {
        console.error("Erro na carga do dia:", erro);
        // Lança o erro para a frente para o Maestro saber que falhou
        throw erro;
    }
}
// Substitua a sua função enviarEscolha no api.js por esta:
async function enviarEscolha(index) {
    document.getElementById("ui-opcoes").innerHTML = "";
    document.getElementById("ui-texto-dialogo").innerHTML = "";
    document.getElementById("fx-overlay").classList.add("fx-fade-out");

    await fetch('/api/escolha', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ indice: index })
    });

    setTimeout(() => {
        document.getElementById("fx-overlay").classList.remove("fx-fade-out");
        iniciarFluxo();
    }, 500);
}
