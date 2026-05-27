// ─── Config ────────────────────────────────────────────────────
// Substitua com sua chave PIX e URL do webhook n8n
const CHAVE_PIX   = "00020126330014br.gov.bcb.pix0111999999999995204000053039865802BR5913Igreja Central6009SAO PAULO62070503***6304ABCD"; // payload real aqui
const N8N_WEBHOOK = "https://seu-n8n.exemplo.com/webhook/pix-confirmado";
const IGREJA_ID   = "";

// ─── Estado ────────────────────────────────────────────────────
let pollingTimer = null;
let dadosPagamento = {};

const isMobile = () => /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

// ─── Elementos ─────────────────────────────────────────────────
const stepForm  = document.getElementById('step-form');
const stepQr    = document.getElementById('step-qr');
const stepOk    = document.getElementById('step-ok');

const inputValor    = document.getElementById('inputValor');
const inputNome     = document.getElementById('inputNome');
const btnGerar      = document.getElementById('btnGerar');
const btnVoltar     = document.getElementById('btnVoltar');
const btnCopiar     = document.getElementById('btnCopiar');
const btnNova       = document.getElementById('btnNova');

const qrSummary     = document.getElementById('qrSummary');
const qrFrameWrap   = document.getElementById('qrFrameWrap');
const mobileLabel   = document.getElementById('mobileLabel');
const qrImg         = document.getElementById('qrImg');
const pixCodeInput  = document.getElementById('pixCodeInput');
const statusBar     = document.getElementById('statusBar');
const statusText    = document.getElementById('statusText');
const okReceipt     = document.getElementById('okReceipt');

// ─── Chips de valor ────────────────────────────────────────────
document.querySelectorAll('.chip').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        inputValor.value = btn.dataset.v;
    });
});

inputValor.addEventListener('input', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
});

// ─── Gerar PIX ─────────────────────────────────────────────────
btnGerar.addEventListener('click', () => {
    const valor = parseFloat(inputValor.value);
    if (!valor || valor <= 0) {
        inputValor.focus();
        return;
    }

    const tipo = document.querySelector('input[name="tipo"]:checked')?.value || 'OFERTA';
    const nome = inputNome.value.trim() || 'Anônimo';
    const txId = 'TX' + Date.now();

    dadosPagamento = { valor, tipo, nome, txId, timestamp: new Date().toISOString() };

    // Summary
    const tipoLabel = { DIZIMO: 'Dízimo', OFERTA: 'Oferta', MISSIONARIA: 'Oferta Missionária', AVULSA: 'Construção' }[tipo];
    qrSummary.innerHTML = `<strong>${nome}</strong> · ${tipoLabel}<br>
        <strong style="font-size:1.1rem">R$ ${valor.toFixed(2).replace('.', ',')}</strong>`;

    // Código PIX (em produção, gere dinamicamente no backend com o valor real)
    pixCodeInput.value = CHAVE_PIX;

    // QR Code via API pública (google charts — substitua por geração no backend)
    const qrData = encodeURIComponent(CHAVE_PIX);
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?data=${qrData}&size=200x200&margin=10`;

    // Desktop = mostra QR; Mobile = só código
    if (isMobile()) {
        mobileLabel.style.display = 'flex';
        qrFrameWrap.style.display = 'none';
    } else {
        qrFrameWrap.style.display = 'flex';
        mobileLabel.style.display = 'none';
    }

    showStep(stepQr);
    iniciarPolling(txId, valor, nome, tipo);
});

// ─── Copiar ────────────────────────────────────────────────────
btnCopiar.addEventListener('click', () => {
    navigator.clipboard.writeText(pixCodeInput.value).then(() => {
        btnCopiar.classList.add('copied');
        btnCopiar.innerHTML = '<i class="ph ph-check"></i> Copiado!';
        setTimeout(() => {
            btnCopiar.classList.remove('copied');
            btnCopiar.innerHTML = '<i class="ph ph-copy"></i> Copiar';
        }, 2500);
    });
});

// ─── Voltar ────────────────────────────────────────────────────
btnVoltar.addEventListener('click', () => {
    clearPolling();
    showStep(stepForm);
});

btnNova.addEventListener('click', () => {
    inputValor.value = '';
    inputNome.value = '';
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    showStep(stepForm);
});

// ─── Polling — checa confirmação no n8n ───────────────────────
function iniciarPolling(txId, valor, nome, tipo) {
    let tentativas = 0;
    const maxTentativas = 60; // 5 min

    pollingTimer = setInterval(async () => {
        tentativas++;
        if (tentativas > maxTentativas) {
            clearPolling();
            statusText.textContent = 'Tempo esgotado. Tente novamente.';
            return;
        }

        try {
            // Consulta o n8n para saber se o pagamento foi confirmado
            // O n8n recebe o webhook do banco/PSP e registra o txId
            const res = await fetch(`${N8N_WEBHOOK}/status?txId=${txId}&igrejaId=${IGREJA_ID}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (res.ok) {
                const data = await res.json();
                if (data.confirmado) {
                    clearPolling();
                    confirmarPagamento(data, valor, nome, tipo);
                }
            }
        } catch (e) {
            // silencioso — continua tentando
        }
    }, 5000); // checa a cada 5s
}

function clearPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingTimer = null;
}

// ─── Confirmar pagamento ───────────────────────────────────────
function confirmarPagamento(data, valor, nome, tipo) {
    statusBar.classList.add('confirmed');
    statusText.textContent = 'Pagamento confirmado!';

    const tipoLabel = { DIZIMO: 'Dízimo', OFERTA: 'Oferta', MISSIONARIA: 'Oferta Missionária', AVULSA: 'Construção' }[tipo];

    okReceipt.innerHTML = `
        <strong>Tipo:</strong> ${tipoLabel}<br>
        <strong>Valor:</strong> R$ ${valor.toFixed(2).replace('.', ',')}<br>
        <strong>Nome:</strong> ${nome}<br>
        <strong>Protocolo:</strong> ${data.txId || dadosPagamento.txId}<br>
        <strong>Data:</strong> ${new Date().toLocaleString('pt-BR')}
    `;

    // Notificar n8n → IA → sistema (POST com dados completos)
    fetch(`${N8N_WEBHOOK}/registrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            txId: dadosPagamento.txId,
            igrejaId: IGREJA_ID,
            valor,
            nome,
            tipo,
            timestamp: dadosPagamento.timestamp,
            confirmadoEm: new Date().toISOString()
        })
    }).catch(() => {});

    setTimeout(() => showStep(stepOk), 800);
}

// ─── Navegação ─────────────────────────────────────────────────
function showStep(target) {
    [stepForm, stepQr, stepOk].forEach(s => {
        s.classList.toggle('card--hidden', s !== target);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
}