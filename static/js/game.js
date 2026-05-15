// === game.js ===
// Função principal que rege a orquestra
async function iniciarFluxo() {
    try {
        // 1. Pede os dados para o carteiro (api.js)
        const data = await carregarDia();

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

// === O GATILHO DE IGNIÇÃO ===
document.addEventListener('DOMContentLoaded', () => {
    const btnStart = document.getElementById('btn-start-game');
    const startOverlay = document.getElementById('start-overlay');
    const trilha = document.getElementById('trilha-sonora');

    if (btnStart) {
        btnStart.addEventListener('click', async () => {
            // 1. Pega o nome que o jogador digitou (se houver um input)
            const inputNome = document.getElementById('input-nome-jogador');
            const nomeParaSalvar = inputNome ? inputNome.value : "Gerente";

            // 2. Avisa o backend para resetar e já manda o nome novo
            // Vamos criar uma rota que faz os dois de uma vez para ser mais rápido
            await fetch('/api/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nomeParaSalvar })
            });

            // 3. Esconde a intro
            if (startOverlay) startOverlay.style.display = 'none';

            // 4. Toca a trilha
            if (trilha) {
                trilha.volume = 0.2;
                trilha.play().catch(() => {});
            }

            // 5. SÓ AGORA chama o maestro para buscar o Dia 1
            iniciarFluxo();
        });
    }
});