/**
 * pagamento_pix.js
 * Controla o fluxo: Formulário → QR → Polling → Confirmação
 */

// ── Elementos ─────────────────────────────────────────────────
const stepForm = document.getElementById('step-form');
const stepQr   = document.getElementById('step-qr');
const stepOk   = document.getElementById('step-ok');

const btnGerar      = document.getElementById('btnGerar');
const btnCopiar     = document.getElementById('btnCopiar');
const btnVoltar     = document.getElementById('btnVoltar');
const btnNovaContrib = document.getElementById('btnNovaContrib');

const inputValor = document.getElementById('inputValor');
const inputNome  = document.getElementById('inputNome');

const qrImg        = document.getElementById('qrImg');
const qrSummary    = document.getElementById('qrSummary');
const pixCodeInput = document.getElementById('pixCodeInput');
const pixStatusBar = document.getElementById('pixStatusBar');
const pixStatusText = document.getElementById('pixStatusText');
const okMsg        = document.getElementById('okMsg');

// ── Estado ────────────────────────────────────────────────────
let pollingInterval = null;
let currentPagamentoId = null;

// ── Chips de valor rápido ─────────────────────────────────────
document.querySelectorAll('.pix-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.pix-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        inputValor.value = chip.dataset.v;
    });
});

// Desativa chip se usuário digitar valor manualmente
inputValor.addEventListener('input', () => {
    document.querySelectorAll('.pix-chip').forEach(c => c.classList.remove('active'));
});

// ── Tipo selecionado ──────────────────────────────────────────
function getTipo() {
    const checked = document.querySelector('input[name="tipo"]:checked');
    return checked ? checked.value : 'OFERTA';
}

// ── Gerar PIX ─────────────────────────────────────────────────
btnGerar.addEventListener('click', async () => {
    const valor = parseFloat(inputValor.value);
    if (!valor || valor < 1) {
        shake(inputValor.closest('.pix-valor-wrap'));
        return;
    }

    btnGerar.disabled = true;
    btnGerar.innerHTML = '<i class="ph ph-spinner"></i> Gerando...';

    try {
        const res = await fetch('/financeiro/api/gerar-pix/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                valor:     valor,
                tipo:      getTipo(),
                nome:      inputNome.value.trim() || 'Contribuinte Anônimo',
                igreja_id: IGREJA_ID || null,
            }),
        });

        const data = await res.json();

        if (!res.ok || data.error) {
            alert(data.error || 'Erro ao gerar PIX. Tente novamente.');
            btnGerar.disabled = false;
            btnGerar.innerHTML = '<i class="ph ph-qr-code"></i> Gerar PIX';
            return;
        }

        currentPagamentoId = data.pagamento_id;

        // Preenche UI
        qrImg.src           = data.qr_code_url;
        pixCodeInput.value  = data.pix_code;
        qrSummary.innerHTML = `
            <strong>${labelTipo(getTipo())}</strong> · 
            R$ ${valor.toFixed(2).replace('.', ',')} · 
            ${inputNome.value.trim() || 'Anônimo'}
        `;

        // Troca de step
        mostrarStep(stepQr);
        iniciarPolling();

    } catch (err) {
        alert('Erro de conexão. Verifique sua internet.');
        btnGerar.disabled = false;
        btnGerar.innerHTML = '<i class="ph ph-qr-code"></i> Gerar PIX';
    }
});

// ── Copiar código PIX ─────────────────────────────────────────
btnCopiar.addEventListener('click', () => {
    navigator.clipboard.writeText(pixCodeInput.value).then(() => {
        btnCopiar.innerHTML = '<i class="ph ph-check"></i> Copiado!';
        setTimeout(() => {
            btnCopiar.innerHTML = '<i class="ph ph-copy"></i> Copiar';
        }, 2000);
    });
});

// ── Voltar ────────────────────────────────────────────────────
btnVoltar.addEventListener('click', resetar);
btnNovaContrib.addEventListener('click', resetar);

function resetar() {
    pararPolling();
    currentPagamentoId = null;
    inputValor.value   = '';
    inputNome.value    = '';
    document.querySelectorAll('.pix-chip').forEach(c => c.classList.remove('active'));

    btnGerar.disabled = false;
    btnGerar.innerHTML = '<i class="ph ph-qr-code"></i> Gerar PIX';

    pixStatusBar.classList.remove('is-ok');
    pixStatusText.textContent = 'Aguardando pagamento...';

    mostrarStep(stepForm);
}

// ── Polling de status ─────────────────────────────────────────
function iniciarPolling() {
    pararPolling();
    pollingInterval = setInterval(verificarStatus, 5000);
}

function pararPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

async function verificarStatus() {
    if (!currentPagamentoId) return;

    try {
        const res  = await fetch(`/financeiro/api/status-pix/${currentPagamentoId}/`);
        const data = await res.json();

        if (data.status === 'approved') {
            pararPolling();
            confirmar();
        }
    } catch (_) {
        // Silencia erros de rede no polling
    }
}

// ── Confirmação ───────────────────────────────────────────────
function confirmar() {
    const valor = parseFloat(inputValor.value).toFixed(2).replace('.', ',');
    const tipo  = labelTipo(getTipo());
    const nome  = inputNome.value.trim() || 'Anônimo';

    okMsg.textContent = `R$ ${valor} de ${tipo} recebido. Obrigado, ${nome}! Que Deus abençoe.`;
    mostrarStep(stepOk);
}

// ── Helpers ───────────────────────────────────────────────────
function mostrarStep(el) {
    [stepForm, stepQr, stepOk].forEach(s => {
        s.classList.add('pix-card--hidden');
        s.style.display = 'none';
    });
    el.classList.remove('pix-card--hidden');
    el.style.display = 'flex';
    // Re-trigger animation
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = '';
}

function shake(el) {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'shake 0.4s ease';
    el.addEventListener('animationend', () => { el.style.animation = ''; }, { once: true });
}

function labelTipo(tipo) {
    return {
        DIZIMO:      'Dízimo',
        OFERTA:      'Oferta',
        MISSIONARIA: 'Oferta Missionária',
        AVULSA:      'Fundo de Construção',
    }[tipo] || 'Contribuição';
}

// ── CSS de shake injetado dinamicamente ──────────────────────
const style = document.createElement('style');
style.textContent = `
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%       { transform: translateX(-8px); }
    40%       { transform: translateX(8px); }
    60%       { transform: translateX(-5px); }
    80%       { transform: translateX(5px); }
}`;
document.head.appendChild(style);