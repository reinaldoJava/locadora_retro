// ==========================================
// ESTADO GLOBAL
// ==========================================
let cenaAtual = {
    filaDialogos: [],
    indiceFala: 0,
    opcoes: [],
    ano: null
};

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

        // --- DEBUGGER NO CONSOLE ---
        console.log("DADOS RECEBIDOS DO BACKEND:", data);
        console.log("STATUS DO WORMHOLE:", data.wormhole);

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
            else {
                console.error("Tag de vídeo não encontrada no HTML!");
                renderizarCena(data);
            }

        }// === NOVA REGRA DO GIF ===
        else if (data.play_gif_terminal === true) {
            console.log(">>> RODANDO GIF DO TERMINAL <<<");
            await executarAnimacaoTerminal(); // Espera o GIF terminar
            renderizarCena(data); // Renderiza o primeiro dia de 1999
        }
        else {
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
        btn.onclick = () => enviarEscolha(i);
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
// Inicia o jogo quando o script carrega
document.addEventListener('DOMContentLoaded', carregarDia);