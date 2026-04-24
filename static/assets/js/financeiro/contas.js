/**
 * contas.js - Central de Obrigações
 */

const POR_PAGINA = 8;
let paginaAtual = 1;
let itensFiltrados = [];

// ── Globais (chamadas pelo HTML) ──────────────────────────────

function preencherFormulario(id, nome, fornecedor, valor, vencimento, categoria, recorrencia, tipo, status) {
    document.getElementById('conta_id').value = id;
    document.getElementById('nome').value = nome;
    document.getElementById('fornecedor').value = fornecedor;
    document.getElementById('vencimento').value = vencimento;

    const v = parseFloat(String(valor).replace(',', '.'));
    document.getElementById('valor').value = isNaN(v) ? '' : v.toFixed(2);

    const selCat = document.getElementById('categoria');
    for (let o of selCat.options) { if (o.value === categoria) { o.selected = true; break; } }

    const selRec = document.getElementById('recorrencia');
    for (let o of selRec.options) { if (o.value === recorrencia) { o.selected = true; break; } }

    document.getElementById(tipo === 'ENTRADA' ? 'tipo_entrada' : 'tipo_saida').checked = true;
    document.getElementById('form-title').textContent = 'Editar Conta';

    // Botão pagar
    const btnPagar = document.getElementById('btn-pagar');
    const banner   = document.getElementById('pago-banner');
    if (status === 'pago') {
        btnPagar.classList.add('cg-hidden');
        banner.classList.add('visible');
    } else {
        btnPagar.classList.remove('cg-hidden');
        banner.classList.remove('visible');
    }

    // Botão apagar — atualiza o form de deletar com o id certo
    const btnDeletar  = document.getElementById('btn-deletar');
    const formDeletar = document.getElementById('form-deletar');
    btnDeletar.style.display  = 'flex';
    formDeletar.action = `/financeiro/contas/${id}/deletar/`;

    document.getElementById('cg-form-conta').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function aplicarFiltros() {
    const mes    = document.getElementById('filter-mes').value;
    const status = document.getElementById('filter-status').value;

    itensFiltrados = getTodosItens().filter(item => {
        const itemMes    = (item.dataset.vencimento || '').split('-')[1] || '';
        const itemStatus = item.dataset.status || '';
        return (!mes || itemMes === mes) && (!status || itemStatus === status);
    });

    paginaAtual = 1;
    renderizar();
}

// ── Internas ──────────────────────────────────────────────────

function getTodosItens() {
    return Array.from(document.querySelectorAll('#lista-contas .cg-activity-item'));
}

function renderizar() {
    getTodosItens().forEach(el => el.style.display = 'none');
    const inicio = (paginaAtual - 1) * POR_PAGINA;
    itensFiltrados.slice(inicio, inicio + POR_PAGINA).forEach(el => el.style.display = 'flex');
    renderizarPaginacao();
}

function renderizarPaginacao() {
    const total = Math.ceil(itensFiltrados.length / POR_PAGINA);
    const nav   = document.getElementById('paginacao');
    nav.innerHTML = '';
    if (total <= 1) return;

    const btnAnt = document.createElement('button');
    btnAnt.className = 'cg-page-btn';
    btnAnt.innerHTML = '<i class="ph ph-caret-left"></i>';
    btnAnt.disabled  = paginaAtual === 1;
    btnAnt.onclick   = () => { paginaAtual--; renderizar(); };
    nav.appendChild(btnAnt);

    const info = document.createElement('span');
    info.className   = 'cg-page-info';
    info.textContent = `${paginaAtual} / ${total}`;
    nav.appendChild(info);

    const btnProx = document.createElement('button');
    btnProx.className = 'cg-page-btn';
    btnProx.innerHTML = '<i class="ph ph-caret-right"></i>';
    btnProx.disabled  = paginaAtual === total;
    btnProx.onclick   = () => { paginaAtual++; renderizar(); };
    nav.appendChild(btnProx);
}

// ── DOM pronto ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {

    // Botão apagar submete o form de deletar
    document.getElementById('btn-deletar').addEventListener('click', function () {
        if (confirm('Tem certeza que quer apagar essa conta? Não tem volta!')) {
            document.getElementById('form-deletar').submit();
        }
    });

    // Comprovante
    document.getElementById('btn-camera').addEventListener('click', () => document.getElementById('file-camera').click());
    document.getElementById('btn-gallery').addEventListener('click', () => document.getElementById('file-gallery').click());

    function handleFile(file) {
        if (!file) return;
        const preview = document.getElementById('upload-preview');
        const img     = document.getElementById('preview-img');
        const pdfBox  = document.getElementById('preview-pdf-name');

        if (file.type === 'application/pdf') {
            preview.style.display = 'none';
            pdfBox.style.display  = 'block';
            document.getElementById('pdf-filename').textContent = file.name;
        } else {
            const r = new FileReader();
            r.onload = e => { img.src = e.target.result; preview.style.display = 'block'; pdfBox.style.display = 'none'; };
            r.readAsDataURL(file);
        }
    }

    document.getElementById('file-camera').addEventListener('change', function () { handleFile(this.files[0]); });
    document.getElementById('file-gallery').addEventListener('change', function () { handleFile(this.files[0]); });
    document.getElementById('btn-remove-file').addEventListener('click', () => {
        document.getElementById('file-camera').value  = '';
        document.getElementById('file-gallery').value = '';
        document.getElementById('upload-preview').style.display   = 'none';
        document.getElementById('preview-pdf-name').style.display = 'none';
    });

    // Inicia com mês atual
    const mesAtual = String(new Date().getMonth() + 1).padStart(2, '0');
    document.getElementById('filter-mes').value = mesAtual;
    aplicarFiltros();
});