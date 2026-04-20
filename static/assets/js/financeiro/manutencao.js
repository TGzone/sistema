document.addEventListener('DOMContentLoaded', () => {
    const maintForm = document.getElementById('maintForm');
    const ticketList = document.getElementById('ticketList');
    const emptyState = document.getElementById('emptyState');
    const urgentCounter = document.getElementById('urgentCounterBadge');

    let tickets = [];

    maintForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // 1. Captura de Dados
        const formData = new FormData(maintForm);
        const ownerData = formData.get('owner').split('|'); // [Nome, Telefone]
        
        const newTicket = {
            id: Math.floor(1000 + Math.random() * 9000),
            title: formData.get('title'),
            urgency: formData.get('urgency'),
            owner: ownerData[0],
            phone: ownerData[1],
            description: formData.get('description'),
            notify: document.getElementById('notifyWhatsapp').checked,
            date: new Date().toLocaleDateString('pt-BR')
        };

        // 2. Lógica do WhatsApp (O Pulo do Gato)
        if (newTicket.notify && newTicket.phone) {
            enviarNotificacaoWpp(newTicket);
        }

        // 3. Atualizar Interface
        addTicketToUI(newTicket);
        tickets.push(newTicket);
        updateStats();
        
        maintForm.reset();
        showModal(newTicket);
    });

    function addTicketToUI(ticket) {
        emptyState.classList.add('maint-hidden');
        
        const card = document.createElement('div');
        card.className = `maint-ticket-item animate__animated animate__fadeInUp`;
        card.innerHTML = `
            <div class="maint-ticket-info">
                <span class="maint-badge maint-badge--${ticket.urgency}">${ticket.urgency}</span>
                <h3 style="margin-top: 0.5rem; font-size: 1rem;">#${ticket.id} - ${ticket.title}</h3>
                <p style="color: var(--maint-text-muted); font-size: 0.875rem;">Resp: ${ticket.owner}</p>
            </div>
            <div style="text-align: right">
                <small style="display: block; color: var(--maint-text-muted)">${ticket.date}</small>
                <button class="maint-button" style="padding: 5px 10px; font-size: 12px; margin-top: 10px; width: auto;">Ver detalhes</button>
            </div>
        `;
        ticketList.prepend(card);
    }

    function enviarNotificacaoWpp(ticket) {
        const saudacao = "Olá " + ticket.owner + "!";
        const mensagem = `${saudacao}%0A%0A*NOVA SOLICITAÇÃO DE ORÇAMENTO*%0A%0A*Item:* ${ticket.title}%0A*Chamado:* %23${ticket.id}%0A*Descrição:* ${ticket.description}%0A%0AFavor retornar com o valor estimado para provisionamento no sistema.`;
        
        const url = `https://api.whatsapp.com/send?phone=55${ticket.phone}&text=${mensagem}`;
        window.open(url, '_blank');
    }

    function updateStats() {
        const urgentes = tickets.filter(t => t.urgency === 'critico').length;
        urgentCounter.textContent = urgentes;
        document.getElementById('statOpen').textContent = tickets.length;
    }

    // Modal simples
    function showModal(ticket) {
        const modal = document.getElementById('maintModal');
        document.getElementById('modalTicket').textContent = `#${ticket.id}`;
        document.getElementById('modalOwner').textContent = ticket.owner;
        modal.classList.add('maint-modal--active');
    }

    // Fechar Modal
    document.querySelectorAll('[data-action="close-modal"]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('maintModal').classList.remove('maint-modal--active');
        });
    });
});