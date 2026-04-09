const cultoModule = {
    init: function() {
        this.bindEvents();
        this.updateTimers();
        setInterval(() => this.updateTimers(), 1000);
    },

    bindEvents: function() {
        const days = document.querySelectorAll('.cg-day-cell:not(.cg-empty)');
        const dateInput = document.getElementById('eventDate');
        const titleInput = document.getElementById('eventTitle');

        days.forEach(day => {
            day.addEventListener('click', () => {
                const d = day.dataset.dia.padStart(2, '0');
                const m = day.dataset.mes.padStart(2, '0');
                const a = day.dataset.ano;

                if(dateInput) {
                    dateInput.value = `${a}-${m}-${d}`;
                    titleInput.focus();
                    
                    document.querySelectorAll('.cg-day-cell').forEach(c => c.classList.remove('cg-selected'));
                    day.classList.add('cg-selected');
                }
            });
        });
    },

    updateTimers: function() {
        const cards = document.querySelectorAll('.cg-monitor-card');
        
        cards.forEach(card => {
            const dateTimeStr = card.dataset.datetime;
            if (!dateTimeStr) return;

            const target = new Date(dateTimeStr);
            const now = new Date();
            const diff = target - now;
            
            const timerElement = card.querySelector('.cg-countdown');
            if (!timerElement) return;

            if (diff > 0) {
                const h = Math.floor(diff / 3600000).toString().padStart(2, '0');
                const m = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
                const s = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');
                
                timerElement.innerText = `${h}:${m}:${s}`;
            } else {
                timerElement.innerText = "ACONTECENDO";
                card.classList.add('status-live'); // Aquela animação que fizemos no CSS
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => cultoModule.init());