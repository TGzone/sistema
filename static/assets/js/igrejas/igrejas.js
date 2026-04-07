/**
 * Gerenciador de Unidades - LuminaGestão
 * Responsável por: Busca em tempo real, Filtro de Saúde e Atualização do Contador.
 */
const churchManager = {
    // 1. ELEMENTOS DO DOM (Referências rápidas)
    ui: {
        searchInput: document.getElementById('searchUnidade'),
        saudeFilter: document.getElementById('filterSaude'),
        counter: document.getElementById('churchCount'),
        // Função para capturar os cards atuais no DOM
        getCards: () => document.querySelectorAll('.unit-card')
    },

    // 2. INICIALIZAÇÃO
    init: function() {
        // Verifica se os elementos essenciais existem na página
        if (!this.ui.searchInput && !this.ui.saudeFilter) return;

        this.bindEvents();
        this.syncCounter(); // Garante o número correto no carregamento inicial
    },

    // 3. EVENTOS DE INTERAÇÃO
    bindEvents: function() {
        // Escuta digitação na busca
        this.ui.searchInput.addEventListener('input', () => this.applyFilters());
        
        // Escuta mudança no seletor de saúde
        this.ui.saudeFilter.addEventListener('change', () => this.applyFilters());
    },

    // 4. LÓGICA DE FILTRAGEM
    applyFilters: function() {
        const termo = this.ui.searchInput.value.toLowerCase();
        const saudeFiltro = this.ui.saudeFilter.value;
        const cards = this.ui.getCards();
        let totalVisivel = 0;

        cards.forEach(card => {
            // Puxa os dados dos atributos 'data-' inseridos pelo Django
            const nomeIgreja = card.getAttribute('data-nome').toLowerCase();
            const statusSaude = card.getAttribute('data-saude');
            
            // Busca também pelo nome do pastor dirigente dentro do card
            const pastorEl = card.querySelector('.pastor-name');
            const nomePastor = pastorEl ? pastorEl.textContent.toLowerCase() : "";
            
            // Critérios de combinação
            const bateBusca = nomeIgreja.includes(termo) || nomePastor.includes(termo);
            const bateSaude = (saudeFiltro === 'todos' || statusSaude === saudeFiltro);

            // Aplica visibilidade baseada no cruzamento dos filtros
            if (bateBusca && bateSaude) {
                card.style.display = '';
                 totalVisivel++;} 
                 else {
                card.style.display = 'none';
}
        });
        
        this.updateCounterDisplay(totalVisivel);
    },

    // 5. ATUALIZAÇÃO DA INTERFACE
    updateCounterDisplay: function(valor) {
        if (this.ui.counter) {
            this.ui.counter.innerText = valor;
        }
    },

    // Sincroniza o número do cabeçalho com a realidade do grid
    syncCounter: function() {
        const cards = this.ui.getCards();
        // Conta apenas os cards que não estão ocultos
        const visiveisAgora = Array.from(cards).filter(c => c.style.display !== 'none').length;
        this.updateCounterDisplay(visiveisAgora);
    }
};

// Inicia o gerenciador assim que o documento estiver pronto
document.addEventListener('DOMContentLoaded', () => churchManager.init());