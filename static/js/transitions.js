function executarTransicao2026(data) {
    const elementos = obterElementos();
    limparElementos(elementos);

    esconderUiMostrarCena(elementos.uiPrincipal, elementos.cenaFim);
    fadeOutTrilha(elementos.trilha);

    iniciarEspetaculoContagem(elementos, data);
}

// ---------------- MÉTODOS AUXILIARES ----------------

function obterElementos() {
    return {
        uiPrincipal: document.getElementById("ui-jogo"),
        cenaFim: document.getElementById("cena-fim-1999"),
        videoShutdown: document.getElementById("video-shutdown"),
        containerShutdown: document.getElementById("container-shutdown"),
        trilha: document.getElementById("trilha-sonora"),
        textoVirada: document.getElementById("texto-virada"),
        numeroContagem: document.getElementById("numero-contagem"),
        textoFelizAno: document.getElementById("texto-feliz-ano"),
        imagensPersonagens: document.getElementById("imagens-personagens")
    };
}

function limparElementos({ textoVirada, numeroContagem, textoFelizAno, imagensPersonagens }) {
    if (textoVirada) textoVirada.innerHTML = "";
    if (numeroContagem) numeroContagem.style.display = "none";
    if (textoFelizAno) textoFelizAno.style.display = "none";
    if (imagensPersonagens) imagensPersonagens.style.display = "none";
}

function esconderUiMostrarCena(uiPrincipal, cenaFim) {
    if (uiPrincipal) uiPrincipal.style.display = "none";
    cenaFim.style.display = "flex";
    setTimeout(() => { cenaFim.style.opacity = "1"; }, 100);
}

function fadeOutTrilha(trilha) {
    if (trilha) transicaoDeVolume(trilha, 0, 2000);
}

function iniciarEspetaculoContagem(elementos, data) {
    setTimeout(() => {
        mostrarMensagemInicial(elementos.textoVirada);

        setTimeout(() => {
            mostrarMensagemContagem(elementos.textoVirada);

            setTimeout(() => {
                iniciarContagemRegressiva(elementos, data);
            }, 3500);
        }, 2500);
    }, 1500);
}

function mostrarMensagemInicial(textoVirada) {
    if (textoVirada) textoVirada.innerHTML = "Parabéns, você chegou ao final de 1999.<br>";
}

function mostrarMensagemContagem(textoVirada) {
    if (textoVirada) textoVirada.innerHTML += "<br>Vai começar a contagem regressiva para as novas aventuras no ano 2000 que se iniciará em:";
}

function iniciarContagemRegressiva({ numeroContagem, textoVirada, textoFelizAno, imagensPersonagens, cenaFim, videoShutdown, containerShutdown, uiPrincipal, trilha }, data) {
    if (numeroContagem) numeroContagem.style.display = "block";
    let contador = 5;

    const intervaloContagem = setInterval(() => {
        if (contador > 0) {
            atualizarContagem(numeroContagem, contador);
            tocarSomContagem(contador);
            contador--;
        } else {
            clearInterval(intervaloContagem);
            finalizarContagem({ textoVirada, numeroContagem, textoFelizAno, imagensPersonagens, cenaFim, videoShutdown, containerShutdown, uiPrincipal, trilha }, data);
        }
    }, 1000);
}

function atualizarContagem(numeroContagem, contador) {
    if (numeroContagem) numeroContagem.innerText = contador;
}

function tocarSomContagem(contador) {
    if (contador > 1) {
        somContagem1.cloneNode().play().catch(() => {});
    } else {
        somContagem2.cloneNode().play().catch(() => {});
    }
}

function finalizarContagem({ textoVirada, numeroContagem, textoFelizAno, imagensPersonagens, cenaFim, videoShutdown, containerShutdown, uiPrincipal, trilha }, data) {
    if (textoVirada) textoVirada.style.display = "none";
    if (numeroContagem) numeroContagem.style.display = "none";

    if (textoFelizAno) textoFelizAno.style.display = "block";
    if (imagensPersonagens) imagensPersonagens.style.display = "flex";

    setTimeout(() => {
        iniciarShutdown({ cenaFim, videoShutdown, containerShutdown, uiPrincipal, trilha }, data);
    }, 4500);
}

function iniciarShutdown({ cenaFim, videoShutdown, containerShutdown, uiPrincipal, trilha }, data) {
    cenaFim.style.display = "none";
    cenaFim.style.opacity = "0";

    if (containerShutdown) containerShutdown.style.display = "flex";
    videoShutdown.style.display = "block";
    videoShutdown.play().catch(e => console.warn("Erro no vídeo:", e));

    videoShutdown.onended = () => {
        encerrarShutdown({ videoShutdown, containerShutdown, uiPrincipal, trilha }, data);
    };
}

function encerrarShutdown({ videoShutdown, containerShutdown, uiPrincipal, trilha }, data) {
    videoShutdown.style.display = "none";
    if (containerShutdown) containerShutdown.style.display = "none";

    if (uiPrincipal) uiPrincipal.style.display = "block";

    if (trilha) {
        trilha.src = "/static/audio/Game_2026.mp3";
        trilha.volume = 0.3;
        trilha.play().catch(() => {});
    }
    renderizarCena(data);
}

// Adicione esta função ao final do seu game.j
function executarAnimacaoTerminal() {
    return new Promise((resolve) => {
        const overlay = document.getElementById('terminal-overlay');
        const gif = document.getElementById('terminal-gif');

        if (!overlay || !gif) {
            console.error("Elementos do Terminal não encontrados!");
            resolve();
            return;
        }

        overlay.classList.remove('layout-oculto');

        // Truque para reiniciar o GIF do começo
        const srcOriginal = gif.src;
        gif.src = '';
        gif.src = srcOriginal;

        // AJUSTE: Coloque aqui o tempo exato em milissegundos do seu GIF
        // Se o GIF dura 2 segundos, use 2000.
        setTimeout(() => {
            overlay.classList.add('layout-oculto');
            resolve();
        }, 3000);
    });
}