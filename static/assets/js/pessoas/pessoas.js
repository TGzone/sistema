// Previne erro de redeclaração caso o script carregue mais de uma vez
var peopleModule = window.peopleModule || {
    init: function () {
        // Elementos da Lista
        this.rows = Array.from(document.querySelectorAll('.person-row'));
        this.filterBtns = Array.from(document.querySelectorAll('.filter-btn'));
        this.counter = document.getElementById('totalCounter');
        this.searchInput = document.getElementById('searchInput');
        this.currentFilter = "todos";
        this.currentSearch = "";

        // Elementos do Drawer
        this.drawer = document.getElementById('personDrawer');
        this.overlay = document.getElementById('drawerOverlay');
        this.closeBtn = document.getElementById('closeDrawer');
        this.btnDesativar = document.getElementById('btnDesativar');
        this.btnAtivar = document.getElementById('btnAtivar'); // Novo
        this.drawerForm = document.getElementById('drawerForm');

        this.initFilters();
        this.initSearch();
        this.initDrawer();
        this.updateView();
    },

    initFilters: function () {
        this.filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentFilter = btn.dataset.category.toLowerCase().trim();
                this.updateView();
            });
        });
    },

    initSearch: function () {
        if (!this.searchInput) return;
        this.searchInput.addEventListener('input', e => {
            this.currentSearch = e.target.value.toLowerCase().trim();
            this.updateView();
        });
    },

    updateView: function () {
        let count = 0;
        this.rows.forEach(row => {
            const category = row.dataset.category.toLowerCase();
            const text = row.innerText.toLowerCase();
            const matchFilter = this.currentFilter === "todos" || category === this.currentFilter;
            const matchSearch = text.includes(this.currentSearch);
            row.style.display = (matchFilter && matchSearch) ? "" : "none";
            if (matchFilter && matchSearch) count++;
        });
        if (this.counter) this.counter.innerText = count;
    },

    openDrawer: async function(id) {
        if (!this.drawer) return;
        try {
            const res = await fetch(`/pessoas/${id}/detail/`);
            const pessoa = await res.json();

            // --- CONFIGURAÇÃO DO FORMULÁRIO ---
            if (this.drawerForm) {
                this.drawerForm.action = `/pessoas/editar/${id}/`;
            }

            // Títulos e Avatar do Header
            document.getElementById('drawerName').innerText = pessoa.nome;
            document.getElementById('drawerAvatar').innerText = pessoa.nome.slice(0,2).toUpperCase();
            document.getElementById('drawerTypeTag').innerText = pessoa.tipo;
            document.getElementById('drawerStatusPill').innerText = pessoa.status_acompanhamento || "-";

            // Função auxiliar para preenchimento
            const fill = (elementId, val) => {
                const el = document.getElementById(elementId);
                if (el) el.value = val || "";
            };

            // 1. Preenchimento de campos básicos
            fill('drawerNameInput', pessoa.nome);
            fill('drawerEmail', pessoa.email);
            fill('drawerTelefone', pessoa.telefone);
            fill('drawerNascimento', pessoa.data_nascimento);
            fill('drawerSexo', pessoa.sexo);
            fill('drawerTipo', pessoa.tipo_raw);
            fill('drawerEstadoCivil', pessoa.estado_civil);
            fill('drawerIgreja', pessoa.igreja_origem);
            fill('drawerMinisterio', pessoa.ministerio);
            fill('drawerObservacoes', pessoa.observacoes);
            fill('drawerStatusAcomp', pessoa.status_raw);

            // 2. REGRA DO RESPONSÁVEL: Só mostra se for < 14 anos ou tipo Kids
            const responsavelGroup = document.getElementById('groupResponsavel');
            const eMenor = pessoa.idade !== "-" && parseInt(pessoa.idade) < 14;
            
            if (responsavelGroup) {
                if (eMenor || pessoa.tipo_raw === 'kids') {
                    responsavelGroup.style.display = 'block';
                    fill('drawerResponsavel', pessoa.responsavel);
                } else {
                    responsavelGroup.style.display = 'none';
                    fill('drawerResponsavel', ""); 
                }
            }

            // 3. Preenchimento Detalhado do Endereço
            if (pessoa.endereco) {
                fill('drawerRua', pessoa.endereco.rua);
                fill('drawerNumero', pessoa.endereco.numero);
                fill('drawerBairro', pessoa.endereco.bairro);
                fill('drawerCidade', pessoa.endereco.cidade);
                fill('drawerEstado', pessoa.endereco.estado);
                fill('drawerCep', pessoa.endereco.cep);
            }

            // 4. LÓGICA DE ATIVAÇÃO/DESATIVAÇÃO (Botões Dinâmicos)
            if (this.btnAtivar && this.btnDesativar) {
                if (pessoa.ativo) {
                    this.btnDesativar.style.display = 'block';
                    this.btnAtivar.style.display = 'none';
                    // Configura clique de desativar
                    this.btnDesativar.onclick = () => {
                        if (confirm(`Deseja realmente desativar ${pessoa.nome}?`)) {
                            window.location.href = `/pessoas/desativar/${id}/`;
                        }
                    };
                } else {
                    this.btnDesativar.style.display = 'none';
                    this.btnAtivar.style.display = 'block';
                    // Configura clique de reativar
                    this.btnAtivar.onclick = () => {
                        if (confirm(`Deseja reativar o membro ${pessoa.nome}?`)) {
                            window.location.href = `/pessoas/ativar/${id}/`;
                        }
                    };
                }
            }

            // Exibe o Drawer
            this.drawer.classList.add('open');
            this.overlay.classList.add('open');
        } catch (err) {
            console.error("Erro ao carregar detalhes da pessoa:", err);
        }
    },

    initDrawer: function () {
        const close = () => {
            if (this.drawer) this.drawer.classList.remove('open');
            if (this.overlay) this.overlay.classList.remove('open');
        };

        if (this.closeBtn) this.closeBtn.addEventListener('click', close);
        if (this.overlay) this.overlay.addEventListener('click', close);
    }
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    peopleModule.init();
});