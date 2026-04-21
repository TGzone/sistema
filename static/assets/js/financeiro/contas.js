/**
 * contas.js - Lógica de Pesquisa e Preenchimento da Central de Obrigações
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. SISTEMA DE BUSCA EM TEMPO REAL (Filtro)
    const searchInput = document.getElementById('search-contas');
    const listaContas = document.getElementById('lista-contas');

    if (searchInput && listaContas) {
        searchInput.addEventListener('keyup', function(e) {
            const termo = e.target.value.toLowerCase();
            const itens = listaContas.querySelectorAll('.cg-activity-item');

            itens.forEach(item => {
                // Pega todo o texto de dentro do card (Nome, Empresa, Categoria, Valor)
                const textoDoItem = item.textContent.toLowerCase();
                
                // Se o termo digitado existir no texto, mostra; se não, esconde.
                if (textoDoItem.includes(termo)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});

// 2. FUNÇÃO DE PREENCHIMENTO E LÓGICA DE BOTÕES
function preencherFormulario(id, nome, fornecedor, valor, vencimento, categoria, recorrencia, tipo, status) {
    
    // Altera o título
    document.getElementById('form-title').innerText = "Analisar Conta";

    // Preenche os campos
    document.getElementById('conta_id').value = id;
    document.getElementById('nome').value = nome;
    document.getElementById('fornecedor').value = fornecedor;
    
    if(valor) {
        document.getElementById('valor').value = parseFloat(valor.replace(',', '.')).toFixed(2);
    }
    
    document.getElementById('vencimento').value = vencimento;
    document.getElementById('categoria').value = categoria;
    document.getElementById('recorrencia').value = recorrencia;

    if (tipo === 'ENTRADA') {
        document.getElementById('tipo_entrada').checked = true;
    } else {
        document.getElementById('tipo_saida').checked = true;
    }

    // LÓGICA DOS BOTÕES
    const btnSalvar = document.getElementById('btn-salvar');
    const btnPagar = document.getElementById('btn-pagar');

    // Botão de salvar vira "Atualizar"
    btnSalvar.innerHTML = '<i class="ph ph-pencil-simple me-2"></i> Atualizar';
    btnSalvar.style.backgroundColor = '#3b82f6'; // Volta pro azul se estava verde

    // Se a conta não estiver paga, mostra o botão "Marcar como Pago"
    if (status !== 'pago') {
        btnPagar.classList.remove('cg-hidden');
    } else {
        btnPagar.classList.add('cg-hidden');
    }
    
    // Rola a tela no mobile
    window.scrollTo({ top: 0, behavior: 'smooth' });
}