// ==========================================
// EFEITOS SONOROS
// ==========================================
const somClick = new Audio('/static/audio/click.mp3');
const somContagem1 = new Audio('/static/audio/contagem_1.mp3'); // CIRÚRGICO: Som do 5 ao 2
const somContagem2 = new Audio('/static/audio/contagem_2.mp3'); // CIRÚRGICO: Som do 1

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
function tocarClick() {
    const clone = somClick.cloneNode();
    clone.volume = 0.6; // Ajuste o volume se achar muito alto
    clone.play().catch(() => {}); // Catch silencioso para evitar erros no console
}