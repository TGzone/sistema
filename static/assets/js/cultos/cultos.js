const cultoModule = {
    init: function() {
        console.log("Módulo de Cultos Iniciado - Versão Forçada Cache-Busting");
        this.bindCalendarClicks();
        this.startTimers();
    },

    bindCalendarClicks: function() {
        const dayCells = document.querySelectorAll('.cg-day-cell:not(.cg-empty)');
        const dateInput = document.getElementById('eventDate');
        const titleInput = document.getElementById('eventTitle');

        dayCells.forEach(cell => {
            cell.addEventListener('click', function(e) {
                // Não dispara se clicar em um evento existente
                if(e.target.closest('.cg-event-pill')) return;

                const d = this.dataset.dia.padStart(2, '0');
                const m = this.dataset.mes.padStart(2, '0');
                const a = this.dataset.ano;

                if(dateInput && titleInput) {
                    dateInput.value = `${a}-${m}-${d}`;
                    titleInput.focus();
                    
                    // Feedback visual temporário de clique
                    const originalBg = this.style.backgroundColor;
                    this.style.backgroundColor = '#e0f2fe';
                    setTimeout(() => { this.style.backgroundColor = originalBg; }, 300);
                }
            });
        });
    },

    startTimers: function() {
        const updateAll = () => {
            const cards = document.querySelectorAll('.cg-monitor-item');
            
            cards.forEach(card => {
                const targetDate = new Date(card.dataset.datetime);
                const now = new Date();
                const diff = targetDate - now;
                
                const timerSpan = card.querySelector('.cg-countdown');
                if (!timerSpan) return;

                if (diff > 0) {
                    // Calculando horas totais, minutos e segundos restantes
                    const h = Math.floor(diff / 3600000).toString().padStart(2, '0');
                    const m = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
                    const s = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');
                    
                    timerSpan.innerText = `${h}:${m}:${s}`;
                    timerSpan.classList.remove('cg-live-text');
                } else {
                    timerSpan.innerText = "LIVE";
                    timerSpan.classList.add('cg-live-text');
                }
            });
        };

        updateAll(); // Roda a primeira vez imediato
        setInterval(updateAll, 1000); // Atualiza a cada segundo
    }
};
document.querySelectorAll(".submenu-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const submenu = btn.nextElementSibling;
    submenu.classList.toggle("active");
  });
});