// movimentacoes.js - Lógica para a página de movimentações financeiras

// Dados simulados de membros (substitua por chamada de API real)
const membros = [
    { id: 1, nome: "Tiago Alves", status: "ativo" },
    { id: 2, nome: "Ana Santos", status: "ativo" },
    { id: 3, nome: "Carlos Eduardo", status: "ativo" },
    { id: 4, nome: "Maria Silva", status: "ativo" },
    { id: 5, nome: "João Pedro", status: "ativo" },
    { id: 6, nome: "Fernanda Costa", status: "ativo" },
    { id: 7, nome: "Roberto Lima", status: "ativo" },
    { id: 8, nome: "Patrícia Oliveira", status: "ativo" },
    { id: 9, nome: "Lucas Mendes", status: "ativo" },
    { id: 10, nome: "Juliana Ferreira", status: "ativo" }
];

// Função para inicializar quando DOM estiver pronto
function initMemberSearch() {
    // Elementos DOM
    const memberSearch = document.getElementById('memberSearch');
    const memberDropdown = document.getElementById('memberDropdown');
    const memberId = document.getElementById('memberId');

    if (!memberSearch) {
        console.error('Campo memberSearch não encontrado!');
        return;
    }

    // Teste: adicionar um log para confirmar que está funcionando
    console.log('✅ Busca de membros inicializada com sucesso!');
    memberSearch.style.border = '2px solid #10b981'; // Verde para indicar que está ativo

    // Estado da busca
    let selectedIndex = -1;

    // Função para filtrar membros
    function filterMembers(query) {
        if (query.length < 2) {
            return [];
        }

        const filtered = membros.filter(membro =>
            membro.nome.toLowerCase().includes(query.toLowerCase()) &&
            membro.status === 'ativo'
        );

        return filtered.slice(0, 5); // Limita a 5 resultados
    }

    // Função para renderizar dropdown
    function renderDropdown(results) {
        if (results.length === 0) {
            memberDropdown.innerHTML = '<div class="cg-dropdown-item cg-no-results">Nenhum membro encontrado</div>';
            memberDropdown.classList.add('cg-dropdown-visible');
            return;
        }

        const html = results.map((membro, index) =>
            `<div class="cg-dropdown-item ${index === selectedIndex ? 'cg-dropdown-item-selected' : ''}" data-id="${membro.id}" data-nome="${membro.nome}">
                <div class="cg-member-name">${membro.nome}</div>
                <div class="cg-member-id">ID: ${membro.id}</div>
            </div>`
        ).join('');

        memberDropdown.innerHTML = html;
        memberDropdown.classList.add('cg-dropdown-visible');
    }

    // Função para esconder dropdown
    function hideDropdown() {
        memberDropdown.classList.remove('cg-dropdown-visible');
        selectedIndex = -1;
    }

    // Função para selecionar membro
    function selectMember(membro) {
        memberSearch.value = membro.nome;
        memberId.value = membro.id;
        hideDropdown();
        memberSearch.blur();
    }

    // Event listeners
    memberSearch.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        const results = filterMembers(query);
        renderDropdown(results);

        // Teste visual: mudar cor da borda baseada na busca
        if (query.length >= 2) {
            memberSearch.style.borderColor = '#3b82f6'; // Azul quando há busca ativa
        } else {
            memberSearch.style.borderColor = '#10b981'; // Verde quando inativo
        }
    });

    memberSearch.addEventListener('keydown', function(e) {
        const items = memberDropdown.querySelectorAll('.cg-dropdown-item:not(.cg-no-results)');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            renderDropdown(filterMembers(e.target.value.trim()));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            renderDropdown(filterMembers(e.target.value.trim()));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && items[selectedIndex]) {
                const selectedItem = items[selectedIndex];
                const membroId = selectedItem.dataset.id;
                const membroNome = selectedItem.dataset.nome;
                selectMember({ id: membroId, nome: membroNome });
            }
        } else if (e.key === 'Escape') {
            hideDropdown();
        }
    });

    memberSearch.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            const results = filterMembers(query);
            renderDropdown(results);
        }
    });

    // Event delegation para itens do dropdown
    memberDropdown.addEventListener('click', function(e) {
        const item = e.target.closest('.cg-dropdown-item');
        if (item && !item.classList.contains('cg-no-results')) {
            const membroId = item.dataset.id;
            const membroNome = item.dataset.nome;
            selectMember({ id: membroId, nome: membroNome });
        }
    });

    // Fechar dropdown ao clicar fora
    document.addEventListener('click', function(e) {
        if (!memberSearch.contains(e.target) && !memberDropdown.contains(e.target)) {
            hideDropdown();
        }
    });

    // Lógica para mostrar justificativa se "Atípico" for selecionado
    document.querySelectorAll('input[name="ocasiao"]').forEach((elem) => {
        elem.addEventListener("change", function(event) {
            const extraField = document.getElementById("cg-justificativa");
            if (event.target.value === "atipico") {
                extraField.classList.remove("cg-hidden");
            } else {
                extraField.classList.add("cg-hidden");
            }
        });
    });
}

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMemberSearch);
} else {
    initMemberSearch();
}