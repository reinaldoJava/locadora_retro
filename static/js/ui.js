// ==========================================
// ESTADO GLOBAL
// ==========================================
let cenaAtual = {
    filaDialogos: [],
    indiceFala: 0,
    opcoes: [],
    ano: null
};


// ==========================================
// MOTOR PRINCIPAL
// ==========================================

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


function renderizarOpcoesReais() {
    const containerOpcoes = document.getElementById("ui-opcoes");
    containerOpcoes.innerHTML = '';

    cenaAtual.opcoes.forEach((opt, i) => {
        const btn = document.createElement('button');
        btn.className = 'vn-btn';
        btn.innerText = opt.nome || opt;
        btn.onclick = () =>{
            enviarEscolha(i);
            tocarClick();
        }
        containerOpcoes.appendChild(btn);
    });
}
