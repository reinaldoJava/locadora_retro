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
    document.getElementById("ato1-terminal").classList.add("oculto");
    document.getElementById("ato2-vhs").classList.remove("oculto");

    // 1. Salva a sessão no Backend
    fetch('/api/iniciar-sessao', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nome: nomeDigitado})
    }).catch(err => console.error("Erro sessão:", err));

    // 2. Baixa o JSON durante a transição
    fetch('/api/intro-roteiro')
        .then(res => res.json())
        .then(data => {
            roteiroIntro = data;
        }).catch(err => console.error("Erro JSON:", err));

    setTimeout(() => {
        iniciarApresentacao();
    }, 2500);
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
        // === TRANSIÇÃO WORMHOLE CIRÚRGICA ===
        const videoWormhole = document.getElementById("video-wormhole-intro");

        if (videoWormhole) {
            // Mostra o vídeo por cima de tudo
            videoWormhole.classList.remove("oculto");
            videoWormhole.style.display = "block";

            // Dá o play
            videoWormhole.play().catch(e => {
                console.warn("Autoplay do vídeo bloqueado", e);
                window.location.href = "/jogo"; // Fallback se der erro
            });

            // Quando o vídeo acabar, aí sim muda de página
            videoWormhole.onended = () => {
                window.location.href = "/jogo";
            };
        } else {
            // Fallback caso você esqueça de colocar o HTML do vídeo
            window.location.href = "/jogo";
        }
    }
};
// Função que sorteia e toca um dos 4 sons
function tocarSomDeTecla() {
    const indexAleatorio = Math.floor(Math.random() * sonsTeclado.length);
    const somClone = sonsTeclado[indexAleatorio].cloneNode(); // O clone permite que os sons se sobreponham rápido
    somClone.volume = 0.4; // Ajuste o volume aqui (0.0 a 1.0)
    somClone.play().catch(() => {}); // O catch ignora erros silenciosamente caso o navegador reclame
}
