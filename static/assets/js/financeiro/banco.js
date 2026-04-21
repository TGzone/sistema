/**
 * ========================================================================
 * banco.js - Lógica do Cockpit Financeiro Standalone
 * ========================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Configuração do Formulário de Nova Conta
    const formNovaConta = document.getElementById('formNovaConta');
    
    if (formNovaConta) {
        // Exemplo de UX: Formatar Conta Bancária automaticamente
        // Adiciona um hífen no último dígito se o usuário esquecer
        const inputConta = formNovaConta.querySelector('input[name="conta"]');
        
        if (inputConta) {
            inputConta.addEventListener('blur', function() {
                let val = this.value.replace(/[^0-9xX]/g, '');
                if (val.length > 1 && !val.includes('-')) {
                    this.value = val.slice(0, -1) + '-' + val.slice(-1);
                }
            });
        }

        // feedback de Loading ao submeter
        formNovaConta.addEventListener('submit', function() {
            const btnSubmit = this.querySelector('button[type="submit"]');
            btnSubmit.innerHTML = '<i class="ph ph-spinner fa-spin"></i> Salvando...';
            btnSubmit.disabled = true;
        });
    }
});