// assets/js/financeiro/movimentacoes.js

const API_MEMBROS = document.getElementById('form-movimentacao').dataset.apiMembros;

let debounceTimer = null;

// ── Autocomplete ──────────────────────────────────────────────────────────────
document.getElementById('membro-busca').addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const termo = this.value.trim();

    if (termo.length < 2) {
        fecharResultados();
        return;
    }

    debounceTimer = setTimeout(() => buscarMembros(termo), 300);
});

function buscarMembros(termo) {
    fetch(`${API_MEMBROS}?q=${encodeURIComponent(termo)}`)
        .then(r => r.json())
        .then(data => renderResultados(data))
        .catch(() => fecharResultados());
}

function renderResultados(data) {
    const box = document.getElementById('membro-results');

    if (!data.length) {
        box.innerHTML = '<div class="cg-membro-option" style="color:#94a3b8;cursor:default;">Nenhum membro encontrado</div>';
        box.classList.add('active');
        return;
    }

    box.innerHTML = data.map(p => `
        <div class="cg-membro-option" onclick="selecionarMembro(${p.id}, '${p.nome.replace(/'/g,"\\'")}')">
            <div class="avatar">${p.nome.slice(0, 2).toUpperCase()}</div>
            <div class="info">
                <strong>${p.nome}</strong>
                <span>${p.tipo} • ${p.unidade}</span>
            </div>
        </div>
    `).join('');

    box.classList.add('active');
}

function selecionarMembro(id, nome) {
    document.getElementById('membro-id').value             = id;
    document.getElementById('membro-busca').value          = '';
    document.getElementById('membro-tag-nome').textContent = nome;
    document.getElementById('membro-tag').classList.add('visible');
    document.getElementById('anonimo-hint').style.display  = 'none';
    fecharResultados();
}

function limparMembro() {
    document.getElementById('membro-id').value = '';
    document.getElementById('membro-busca').value = '';
    document.getElementById('membro-tag').classList.remove('visible');
    document.getElementById('anonimo-hint').style.display = '';
}

function fecharResultados() {
    const box = document.getElementById('membro-results');
    box.innerHTML = '';
    box.classList.remove('active');
}

// Fecha ao clicar fora do wrapper
document.addEventListener('click', function (e) {
    if (!e.target.closest('.cg-membro-wrapper')) fecharResultados();
});

// ── Ocasião atípica ───────────────────────────────────────────────────────────
document.querySelectorAll('input[name="ocasiao"]').forEach(radio => {
    radio.addEventListener('change', function () {
        document.getElementById('cg-justificativa')
            .classList.toggle('cg-hidden', this.value !== 'atipico');
    });
});