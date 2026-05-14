// ==========================================
// ESTADO GLOBAL
// ==========================================
let cenaAtual = {
    filaDialogos: [],
    indiceFala: 0,
    opcoes: [],
    ano: null
};
const somClick = new Audio('/static/audio/click.mp3');
let nomeDoJogadorSessao = "";

// ==========================================
// FUNÇÕES AUXILIARES
// ==========================================
function processarTextoBruto(textoBruto) {
    const blocos = textoBruto.split(/\n\s*\n/);
    let fila = [];

    blocos.forEach(bloco => {
        let limpo = bloco.trim();
        if (!limpo) return;

        const regex = /^([A-ZÀ-Úa-zà-ú\s]+):\s*([\s\S]*)/i;
        const match = limpo.match(regex);

        if (match) {
            fila.push({ personagem: match[1].trim().toUpperCase(), texto: match[2].trim() });
        } else {
            fila.push({ personagem: "SISTEMA", texto: limpo });
        }
    });
    return fila;
}

// ==========================================
// MOTOR PRINCIPAL
// ==========================================
async function carregarDia() {
    try {
        const res = await fetch('/api/proximo-evento');
        const data = await res.json();
        nomeDoJogadorSessao = data.nome_usuario;
        // Pega a trilha sonora
        const trilha = document.getElementById('trilha-sonora');

        if (data.wormhole === true) {
            console.log(">>> RODANDO O VÍDEO WORMHOLE! <<<");
            const video = document.getElementById("video-wormhole");
            if(video) {
                video.classList.remove("layout-oculto");
                video.load();
                video.play().catch(e => console.error("Erro no play do vídeo:", e));

                video.onended = () => {
                    video.classList.add("layout-oculto");
                    renderizarCena(data);
                };
            }
        }
        else if (data.play_gif_terminal === true) {
            console.log(">>> RODANDO GIF DO TERMINAL <<<");
            await executarAnimacaoTerminal();
            // CIRÚRGICO: A página jogo abriu. Toca a música baixa enquanto o terminal fecha
            if (trilha) {
                transicaoDeVolume(trilha, 1.0, 2000); // Sobe para 100% em 2 segundos
                trilha.play().catch(e => console.warn("Autoplay bloqueado:", e));
            }else{
                // Caso não tenha GIF (ex: carregamento direto)
                if (trilha) trilha.volume = 1.0;
                renderizarCena(data);
            }
            renderizarCena(data);
        }
        else {
            // Cena normal de 1999 (Dias 2, 3, etc)
            // Se a música por acaso estiver pausada, dá play nela cheia.
            if (trilha && trilha.paused) {
                trilha.volume = 1.0;
                trilha.play().catch(e => console.warn(e));
            }
            renderizarCena(data);
        }
    } catch (e) { console.error("Erro na carga do dia:", e); }
}

function renderizarCena(data) {
    const elementoFundo = document.getElementById("ui-bg");
    // Correção: Voltando para .jpg conforme o arquivo bg_1999.jpg original
    if (data.ano && elementoFundo) {
        elementoFundo.src = `/static/img/bg_${data.ano}.png`;
    }

    cenaAtual.filaDialogos = processarTextoBruto(data.texto);
    cenaAtual.indiceFala = 0;
    cenaAtual.opcoes = data.opcoes || [];

    proximoPasso();
}

window.proximoPasso = function() {
    const containerOpcoes = document.getElementById("ui-opcoes");
    const elementoTexto = document.getElementById("ui-texto-dialogo");
    const scrollBox = document.getElementById("scroll-box");

    containerOpcoes.innerHTML = '';

    if (cenaAtual.indiceFala < cenaAtual.filaDialogos.length) {
        const fala = cenaAtual.filaDialogos[cenaAtual.indiceFala];
        const nomeBruto = fala.personagem; // Ex: "JOÃO", "VAGNER"
        const nomeFalando = nomeBruto.trim().toUpperCase();

        // Acumula o texto
        elementoTexto.innerHTML += `<p><strong>${nomeBruto}:</strong> ${fala.texto}</p><br>`;
        scrollBox.scrollTop = scrollBox.scrollHeight;

        // Controle de Imagens
        const imgVagner = document.getElementById("ator-vagner");
        const containerVagner = document.getElementById("ator-vagner-container");
        const imgNPC = document.getElementById("ator-npc");
        const containerNPC = document.getElementById("ator-npc-container");

        containerVagner.classList.remove("layout-oculto");

        // A LISTA BRANCA DE IMAGENS (Somente eles têm arquivo .png próprio)
        const npcsValidos = ["LEILA", "MAURICIO", "VAGNER"];

        if (nomeFalando === "VAGNER") {
            imgVagner.className = "actor-img ator-foco";
            if (!containerNPC.classList.contains("layout-oculto")) {
                imgNPC.className = "actor-img ator-inativo";
            }
        } else if (nomeFalando !== "SISTEMA") {
            containerNPC.classList.remove("layout-oculto");
            imgNPC.className = "actor-img ator-foco";
            imgVagner.className = "actor-img ator-inativo";

            // Se o nome não estiver na lista branca, garantimos que é o Gerente
            if (npcsValidos.includes(nomeFalando)) {
                const nomeArquivo = nomeFalando.toLowerCase();
                imgNPC.src = `/static/img/${nomeArquivo}.png`;
            } else {
                imgNPC.src = `/static/img/gerente.png`;
            }
        }

        // Botão de Avançar
        const btnNext = document.createElement('button');
        btnNext.className = 'vn-btn';
        btnNext.innerText = "Continuar...";
        btnNext.onclick = () => {
            tocarClick();
            cenaAtual.indiceFala++;
            window.proximoPasso();
        };
        containerOpcoes.appendChild(btnNext);

    } else {
        renderizarOpcoesReais();
    }
};

function renderizarOpcoesReais() {
    const containerOpcoes = document.getElementById("ui-opcoes");
    containerOpcoes.innerHTML = '';

    cenaAtual.opcoes.forEach((opt, i) => {
        const btn = document.createElement('button');
        btn.className = 'vn-btn';
        btn.innerText = opt.nome || opt;
        btn.onclick = () =>{
            tocarClick();
            enviarEscolha(i);
        }
        containerOpcoes.appendChild(btn);
    });
}

async function enviarEscolha(index) {
    document.getElementById("ui-texto-dialogo").innerHTML = "";
    document.getElementById("fx-overlay").classList.add("fx-fade-out");

    await fetch('/api/escolha', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ indice: index })
    });

    setTimeout(() => {
        document.getElementById("fx-overlay").classList.remove("fx-fade-out");
        carregarDia();
    }, 500);
}
// Adicione esta função ao final do seu game.js
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
// Função para fazer Fade In ou Fade Out do áudio
function transicaoDeVolume(audioElement, volumeAlvo, tempoEmMs) {
    return new Promise((resolve) => {
        const passos = 20; // Quantidade de "degraus" do volume
        const intervalo = tempoEmMs / passos;
        const diferencaVolume = (volumeAlvo - audioElement.volume) / passos;

        const timer = setInterval(() => {
            let novoVolume = audioElement.volume + diferencaVolume;

            // Travas de segurança (volume deve ficar entre 0 e 1)
            if (novoVolume > 1) novoVolume = 1;
            if (novoVolume < 0) novoVolume = 0;

            audioElement.volume = novoVolume;

            // Se chegou no volume alvo ou muito perto dele
            if ((diferencaVolume > 0 && audioElement.volume >= volumeAlvo) ||
                (diferencaVolume < 0 && audioElement.volume <= volumeAlvo)) {
                audioElement.volume = volumeAlvo;
                clearInterval(timer);
                resolve();
            }
        }, intervalo);
    });
}
// Removemos o evento 'DOMContentLoaded' que rodava o carregarDia automaticamente.
// Agora, esperamos o clique do jogador para destravar o áudio e iniciar o fluxo.

document.addEventListener('DOMContentLoaded', () => {
    const btnStart = document.getElementById('btn-start-game');
    const startOverlay = document.getElementById('start-overlay');
    const trilha = document.getElementById('trilha-sonora');
    if (btnStart) {
        btnStart.addEventListener('click', () => {
            // 1. Esconde a tela de botão
            startOverlay.style.display = 'none';

            if (trilha) {
                trilha.volume = 0.2; // Já deixa baixo para o GIF do Terminal
                // O .play() aqui é garantido de funcionar porque veio de um clique real
                trilha.play().catch(e => console.warn("Erro no audio do jogo:", e));
            }

            // 3. Agora sim, chama o backend e roda a mágica toda
             carregarDia();
        });
    } else {
        // Fallback caso você esqueça de colocar o HTML do botão
        carregarDia();
    }
});
function tocarClick() {
    const clone = somClick.cloneNode();
    clone.volume = 0.6; // Ajuste o volume se achar muito alto
    clone.play().catch(() => {}); // Catch silencioso para evitar erros no console
}