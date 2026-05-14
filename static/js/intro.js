// static/js/intro.js

let nomeDigitado = "";
let slideAtual = 0;
let roteiroIntro = [];
let transicaoIniciada = false;

document.addEventListener('DOMContentLoaded', () => {
    const inputNome = document.getElementById("nome-jogador");
    if(inputNome) {
        inputNome.addEventListener("keydown", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                if (transicaoIniciada) return;

                const inputVal = this.value.trim().toUpperCase();
                if (inputVal.length > 0) {
                    transicaoIniciada = true;
                    nomeDigitado = inputVal;
                    this.disabled = true;
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nomeDigitado })
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

    document.getElementById("elenco-titulo").innerText = slide.titulo;
    document.getElementById("elenco-texto").innerText = slide.texto;
}

// O botão precisa estar ligado a esta função no HTML via onclick="avancarApresentacao()"
window.avancarApresentacao = function() {
    slideAtual++;
    if (slideAtual < roteiroIntro.length) {
        renderizarSlide();
    } else {
        window.location.href = "/jogo";
    }
};