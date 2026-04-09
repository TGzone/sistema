/**
 * Gerenciador de Unidades - LuminaGestão
 * Responsável por: Busca em tempo real, Filtro de Saúde e Atualização do Contador.
 */
(() => {
    const churchManager = {
        // 1. ELEMENTOS DO DOM
        ui: {
            searchInput: document.getElementById('searchUnidade'),
            saudeFilter: document.getElementById('filterSaude'),
            counter: document.getElementById('churchCount'),
            getCards: () => document.querySelectorAll('.unit-card')
        },

        // 2. INICIALIZAÇÃO
        init: function() {
            if (!this.ui.searchInput && !this.ui.saudeFilter) return;
            this.bindEvents();
            this.syncCounter(); 
        },

        // 3. EVENTOS
        bindEvents: function() {
            this.ui.searchInput.addEventListener('input', () => this.applyFilters());
            this.ui.saudeFilter.addEventListener('change', () => this.applyFilters());
        },

        // 4. LÓGICA DE FILTRAGEM
        applyFilters: function() {
            const termo = this.ui.searchInput.value.toLowerCase();
            const saudeFiltro = this.ui.saudeFilter.value;
            const cards = this.ui.getCards();
            let totalVisivel = 0;

            cards.forEach(card => {
                const nomeIgreja = (card.getAttribute('data-nome') || "").toLowerCase();
                const statusSaude = card.getAttribute('data-saude');
                
                const pastorEl = card.querySelector('.pastor-name');
                const nomePastor = pastorEl ? pastorEl.textContent.toLowerCase() : "";
                
                const bateBusca = nomeIgreja.includes(termo) || nomePastor.includes(termo);
                const bateSaude = (saudeFiltro === 'todos' || statusSaude === saudeFiltro);

                if (bateBusca && bateSaude) {
                    card.style.display = '';
                    totalVisivel++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            this.updateCounterDisplay(totalVisivel);
        },

        // 5. INTERFACE
        updateCounterDisplay: function(valor) {
            if (this.ui.counter) {
                this.ui.counter.innerText = valor;
            }
        },

        syncCounter: function() {
            const cards = this.ui.getCards();
            const visiveisAgora = Array.from(cards).filter(c => c.style.display !== 'none').length;
            this.updateCounterDisplay(visiveisAgora);
        }
    };

    // Inicializa o script
    document.addEventListener('DOMContentLoaded', () => churchManager.init());
})();