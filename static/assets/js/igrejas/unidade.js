/**
 * Unidade Intelligence & Drawer Control - Sistema PDB
 */

var unidadeModule = {
    init: function() {
        console.log("🚀 LuminaGestão: Inteligência da Unidade Ativada.");
        this.drawer = document.getElementById('unidadeDrawer');
        this.overlay = document.getElementById('drawerOverlay');
        this.form = document.getElementById('drawerForm');
        this.fields = document.getElementById('dynamicFields');
        
        this.initMiniSearch();
        this.initCloseEvents();
    },

    openDrawer: function(tipo, data = {}) {
        // Redefine os elementos para garantir que o JS os encontre após mudanças no DOM
        this.drawer = document.getElementById('unidadeDrawer');
        this.overlay = document.getElementById('drawerOverlay');
        this.fields = document.getElementById('dynamicFields');

        if (!this.drawer || !this.fields) {
            console.error("Erro: Container 'dynamicFields' não encontrado no HTML.");
            return;
        }

        this.fields.innerHTML = ""; 
        let html = `<input type="hidden" name="acao_tipo" value="${tipo}">`;

        // --- FORMULÁRIO: EDITAR UNIDADE ---
        if (tipo === 'editar') {
            this.updateHeader("Editar Unidade", "Atualize os dados estruturais", "ph-church");
            html += `
                <div class="input-group">
                    <label>Nome da Unidade</label>
                    <input type="text" name="nome" value="${data.nome || ''}" required>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="input-group"><label>CNPJ</label><input type="text" name="cnpj" value="${data.cnpj || ''}"></div>
                    <div class="input-group"><label>Telefone</label><input type="text" name="telefone" value="${data.telefone || ''}"></div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="input-group"><label>Cidade</label><input type="text" name="cidade" value="${data.cidade || ''}"></div>
                    <div class="input-group"><label>Bairro</label><input type="text" name="bairro" value="${data.bairro || ''}"></div>
                </div>
                <div class="input-group">
                    <label>Capacidade (Lugares)</label>
                    <input type="number" name="capacidade" value="${data.capacidade || 0}">
                </div>
            `;
        } 
        // --- FORMULÁRIO: REMANEJAR OU PASTOR ---
        else if (tipo === 'remanejar' || tipo === 'atribuir_pastor') {
            const isPastor = tipo === 'atribuir_pastor';
            this.updateHeader(
                isPastor ? "Definir Dirigente" : "Remanejar Membro", 
                isPastor ? "Selecione o líder responsável" : "Trazer pessoa de outra unidade", 
                isPastor ? "ph-user-focus" : "ph-arrows-left-right"
            );
            html += `
                <div class="input-group">
                    <label>Pesquisar Pessoa (Global)</label>
                    <input type="text" id="inputBuscaGlobal" placeholder="Digite o nome..." class="form-control" autocomplete="off">
                    <input type="hidden" name="${isPastor ? 'pastor_id' : 'pessoa_id'}" id="remanejar_pessoa_id">
                    <div id="listaGlobalResultados" class="results-list" style="margin-top:10px;"></div>
                </div>
            `;
        }

        this.fields.innerHTML = html;
        this.drawer.classList.add('open');
        this.overlay.classList.add('open');

        // Ativa a busca global se o campo foi criado
        if (document.getElementById('inputBuscaGlobal')) {
            this.initGlobalSearch();
        }
    },

    closeDrawer: function() {
        if (this.drawer) this.drawer.classList.remove('open');
        if (this.overlay) this.overlay.classList.remove('open');
    },

    initCloseEvents: function() {
        if (this.overlay) {
            this.overlay.onclick = () => this.closeDrawer();
        }
    },

    updateHeader: function(title, sub, icon) {
        const t = document.getElementById('drawerTitle');
        const s = document.getElementById('drawerSubtitle');
        const i = document.getElementById('drawerIcon');
        if (t) t.innerText = title;
        if (s) s.innerText = sub;
        if (i) i.className = `ph-bold ${icon}`;
    },

    initGlobalSearch: function() {
        const input = document.getElementById('inputBuscaGlobal');
        const container = document.getElementById('listaGlobalResultados');
        if (!input) return;

        input.oninput = (e) => {
            const termo = e.target.value.trim();
            if (termo.length < 3) {
                container.innerHTML = "";
                return;
            }

            fetch(`/igrejas/api/busca-lideranca/?busca=${termo}`)
                .then(res => res.json())
                .then(data => {
                    if (data.length === 0) {
                        container.innerHTML = '<p style="padding:10px; font-size:12px; color:gray;">Ninguém encontrado.</p>';
                        return;
                    }
                    container.innerHTML = data.map(p => `
                        <div class="pastor-option" onclick="unidadeModule.selecionarItem('${p.id}', '${p.nome}')">
                            <div class="pastor-avatar">${p.nome.slice(0,2).toUpperCase()}</div>
                            <div class="pastor-info-modal">
                                <strong>${p.nome}</strong>
                                <span>${p.cargo} • ${p.unidade}</span>
                            </div>
                        </div>
                    `).join('');
                });
        };
    },

    selecionarItem: function(id, nome) {
        const hiddenId = document.getElementById('remanejar_pessoa_id');
        const inputBusca = document.getElementById('inputBuscaGlobal');
        if (hiddenId) hiddenId.value = id;
        if (inputBusca) inputBusca.value = nome;
        document.getElementById('listaGlobalResultados').innerHTML = `<p style="color:green; padding:10px; font-weight:700;">✅ Selecionado</p>`;
    },

    initMiniSearch: function() {
        const input = document.getElementById('miniSearchMembro');
        if (input) {
            input.oninput = (e) => {
                const termo = e.target.value.toLowerCase();
                document.querySelectorAll('.mini-row').forEach(row => {
                    const nome = row.getAttribute('data-nome') || "";
                    row.style.display = nome.includes(termo) ? '' : 'none';
                });
            };
        }
    }
};

document.addEventListener('DOMContentLoaded', () => unidadeModule.init());

var UnidadeIntelligence = {
    abrirModalPastor: () => unidadeModule.openDrawer('atribuir_pastor'),
    fecharModal: () => unidadeModule.closeDrawer()
};