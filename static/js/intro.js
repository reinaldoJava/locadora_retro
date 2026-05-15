// static/js/intro.js

let nomeDigitado = "";
let slideAtual = 0;
let roteiroIntro = [];
let transicaoIniciada = false;
let digitacaoInterval = null;
let isDigitando = false;
let textoCompletoAtual = "";
// Carrega os 4 sons de tecla na memória (ajuste para .wav se os seus arquivos forem .wav)
const sonsTeclado = [
    new Audio('/static/audio/tecla_1.mp3'),
    new Audio('/static/audio/tecla_2.mp3'),
    new Audio('/static/audio/tecla_3.mp3'),
    new Audio('/static/audio/tecla_4.mp3')
];

document.addEventListener('DOMContentLoaded', () => {
    const inputNome = document.getElementById("nome-jogador");
    if (inputNome) {
        inputNome.addEventListener("input", () => {
            tocarSomDeTecla();
        });
        inputNome.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                if (transicaoIniciada) return;

                const inputVal = this.value.trim().toUpperCase();
                if (inputVal.length > 0) {
                    transicaoIniciada = true;
                    nomeDigitado = inputVal;
                    this.disabled = true;

                    // === CIRÚRGICO: DA PLAY NA MÚSICA DA INTRO ===
                    const trilhaIntro = document.getElementById('trilha-sonora-intro');
                    if (trilhaIntro) {
                        trilhaIntro.volume = 0.5; // Começa alto
                        trilhaIntro.play().catch(e => console.warn("Erro no audio intro", e));
                    }
                    // ===========================================

                    iniciarTransicaovhs();
                }
            }
        });
    }
});

function iniciarTransicaovhs() {
    const nomeDigitado = document.getElementById("input-nome")?.value || "GERENTE";

    // 1. MUDANÇA VISUAL IMEDIATA
    document.getElementById("ato1-terminal").classList.add("oculto");
    document.getElementById("ato2-vhs").classList.remove("oculto");

    console.log("Tentando resetar o servidor para 1999...");

    // 2. ORDEM DE CHEGADA: Primeiro o Reset.
    // Usamos o .then() para garantir que nada aconteça antes do reset terminar.
    fetch('/api/reset', { // Certifique-se que essa rota faz o 'motor = Engine()' no Python
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nome: nomeDigitado})
    })
        .then(response => {
            if (!response.ok) throw new Error("Falha ao resetar");
            console.log("Servidor resetado com sucesso!");

            // 3. Só agora buscamos o roteiro da intro
            return fetch('/api/intro-roteiro');
        })
        .then(res => res.json())
        .then(data => {
            roteiroIntro = data;

            // 4. Só agora iniciamos o cronômetro para a apresentação
            setTimeout(() => {
                iniciarApresentacao();
            }, 2500);
        })
        .catch(err => {
            console.error("Erro no fluxo de inicialização:", err);
            // Opcional: Se der erro, avisar o usuário ou tentar de novo
        });
}
function iniciarApresentacao() {
    // Trava de segurança: se o JSON não baixou a tempo, aborta e tenta de novo em 500ms
    if (roteiroIntro.length === 0) {
        setTimeout(iniciarApresentacao, 500);
        return;
    }

    document.getElementById("ato2-vhs").classList.add("oculto");
    const containerAto3 = document.getElementById("ato3-elenco");
    containerAto3.classList.remove("oculto");
    containerAto3.classList.add("fade-in");

    // Injeta dinamicamente
    const indexGerente = roteiroIntro.length - 1;
    roteiroIntro[indexGerente].texto = roteiroIntro[indexGerente].texto.replace("{NOME_JOGADOR}", nomeDigitado);

    renderizarSlide();
}

function renderizarSlide() {
    const slide = roteiroIntro[slideAtual];
    const imgElenco = document.getElementById("elenco-imagem");

    if (slide.imagem) {
        imgElenco.src = slide.imagem;
        imgElenco.classList.remove("oculto");
    } else {
        imgElenco.classList.add("oculto");
    }

    // O título entra de uma vez
    document.getElementById("elenco-titulo").innerText = slide.titulo;

    // === MÁQUICA DO EFEITO DE DIGITAÇÃO AQUI ===
    const elementoTexto = document.getElementById("elenco-texto");
    elementoTexto.innerText = ""; // Limpa o texto anterior
    textoCompletoAtual = slide.texto;
    isDigitando = true;

    let i = 0;
    clearInterval(digitacaoInterval); // Garante que não tenha duas digitações ocorrendo ao mesmo tempo

    digitacaoInterval = setInterval(() => {
        if (i < textoCompletoAtual.length) {
            const letraAtual = textoCompletoAtual.charAt(i);
            elementoTexto.innerHTML += letraAtual;

            // Só toca som se não for um espaço em branco ou quebra de linha (dá mais realismo)
            if (letraAtual !== ' ' && letraAtual !== '\n') {
                tocarSomDeTecla();
            }
            i++;
        } else {
            // Terminou de digitar
            clearInterval(digitacaoInterval);
            isDigitando = false;
        }
    }, 60); // <-- 40ms é a velocidade de digitação. Diminua para mais rápido, aumente para mais lento.
}

// O botão precisa estar ligado a esta função no HTML via onclick="avancarApresentacao()"
window.avancarApresentacao = function() {
    // REGRA DE UX: Se clicar enquanto digita, corta a animação e mostra tudo
    if (isDigitando) {
        clearInterval(digitacaoInterval);
        document.getElementById("elenco-texto").innerText = textoCompletoAtual;
        isDigitando = false;
        return; // Para a execução por aqui
    }

    // Se não estiver digitando, segue o fluxo normal
    slideAtual++;
    if (slideAtual < roteiroIntro.length) {
        renderizarSlide();
    } else {
        // === : ESMAECER A TELA E BAIXAR O SOM ===

        // 1. Pega o corpo da página e aplica uma transição CSS via JS
        document.body.style.transition = "opacity 2.0s ease-in-out";
        document.body.style.opacity = "0";

        // 2. Pega o áudio e faz um "Fade Out" suave
        const trilha = document.getElementById('trilha-sonora-intro');
        if (trilha) {
            let volumeAtual = trilha.volume;
            const fadeAudio = setInterval(() => {
                if (volumeAtual > 0.1) {
                    volumeAtual -= 0.1;
                    trilha.volume = volumeAtual.toFixed(1); // Evita bugs de precisão decimal
                } else {
                    clearInterval(fadeAudio);
                    trilha.pause();
                }
            }, 200); // Reduz o volume a cada 200ms
        }

        // 3. Aguarda exatos 2 segundos e dispara a mudança de página
        setTimeout(() => {
            window.location.href = "/jogo";
        }, 2000);
    }
};
// Função que sorteia e toca um dos 4 sons
function tocarSomDeTecla() {
    const indexAleatorio = Math.floor(Math.random() * sonsTeclado.length);
    const somClone = sonsTeclado[indexAleatorio].cloneNode(); // O clone permite que os sons se sobreponham rápido
    somClone.volume = 0.4; // Ajuste o volume aqui (0.0 a 1.0)
    somClone.play().catch(() => {}); // O catch ignora erros silenciosamente caso o navegador reclame
}
