// === game.js ===
// Função principal que rege a orquestra
async function iniciarFluxo() {
    try {
        // 1. Pede os dados para o carteiro (api.js)
        const data = await carregarDia();
        // CAPTURA CIRÚRGICA DA VIRADA DE ERA
        if (data.virada_1999 === true) {
            exibirCenaFim1999();
            return;
        }
        // 2. O Maestro decide quem vai atuar com base nas flags do backend
        if (data.wormhole === true) {
            // Roda o cinema de virada de ano (transitions.js)
            executarTransicao2026(data);
        } else {
            // Se for o começo de 1999, roda o terminal (transitions.js)
            if (data.play_gif_terminal === true) {
                executarAnimacaoTerminal();
            }

            // Desenha a tela do jogo normal (ui.js)
            renderizarCena(data);
        }
    } catch (erro) {
        console.error("Falha Crítica ao carregar o sistema: ", erro);
    }
}

// === O GATILHO DE IGNIÇÃO ===
// Assim que o navegador montar o HTML, ele chama o Maestro
document.addEventListener('DOMContentLoaded', () => {
    iniciarFluxo();
});
// Removemos o evento 'DOMContentLoaded' que rodava o carregarDia automaticamente.
// Agora, esperamos o clique do jogador para destravar o áudio e iniciar o fluxo.

// === O GATILHO DE IGNIÇÃO CORRIGIDO ===
document.addEventListener('DOMContentLoaded', () => {
    const btnStart = document.getElementById('btn-start-game');
    const startOverlay = document.getElementById('start-overlay');
    const trilha = document.getElementById('trilha-sonora');

    if (btnStart) {
        btnStart.addEventListener('click', async () => {
            const inputNome = document.getElementById('input-nome-jogador');
            const nomeParaSalvar = inputNome ? inputNome.value : "Gerente";

            // Reseta o motor no servidor
            await fetch('/api/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nomeParaSalvar })
            });

            if (startOverlay) startOverlay.style.display = 'none';

            if (trilha) {
                trilha.volume = 0.2;
                trilha.play().catch(() => {});
            }

            // UNICA IGNIÇÃO PERMITIDA: Chama o maestro aqui e em nenhum outro lugar de forma automática
            iniciarFluxo();
        });
    }
});
// Adicione esta função ao final do seu game.js para gerenciar a cena oculta
function exibirCenaFim1999() {
    // Esconde a interface padrão do jogo
    document.querySelector(".game-container").style.display = "none";

    // Ativa e estiliza o container da virada
    const cenaFim = document.getElementById("cena-fim-1999");
    cenaFim.style.display = "flex";
    cenaFim.style.flexDirection = "column";
    cenaFim.style.alignItems = "center";
    cenaFim.style.justifyContent = "center";
    cenaFim.style.width = "100vw";
    cenaFim.style.height = "100vh";
    cenaFim.style.position = "fixed";
    cenaFim.style.backgroundColor = "black";

    const textoVirada = document.getElementById("texto-virada");
    const numeroContagem = document.getElementById("numero-contagem");
    const textoFelizAno = document.getElementById("texto-feliz-ano");
    const imagensPersonagens = document.getElementById("imagens-personagens");

    textoVirada.innerText = "31 de Dezembro de 1999 - 23:59:55";

    // Executa a contagem progressiva/regressiva na tela
    setTimeout(() => {
        textoVirada.style.display = "none";
        numeroContagem.style.display = "block";

        let segundos = 5;
        numeroContagem.innerText = segundos;

        let intervalo = setInterval(() => {
            segundos--;
            if (segundos > 0) {
                numeroContagem.innerText = segundos;
            } else {
                clearInterval(intervalo);
                numeroContagem.style.display = "none";
                textoFelizAno.style.display = "block";
                imagensPersonagens.style.display = "flex";

                // Finaliza a comemoração e salta nativamente para 2026
                setTimeout(() => {
                    cenaFim.style.display = "none";
                    document.querySelector(".game-container").style.display = "block";

                    // CHAMA O MAESTRO: Como o motor já está apontado para 2026, ele carregará o arquivo novo
                    iniciarFluxo();
                }, 4000);
            }
        }, 1000);
    }, 3000);
}