/**
 * contas.js - GeanGestão (Versão Integrada com Django)
 * Motor de Interface e UX para a Central de Obrigações
 */

function analisarConta(id, nome, fornecedor, valor, vencimento, categoria, status) {
    // 1. Atualizar o Cabeçalho do Painel Lateral
    
    // NOVO: Injeta o ID no campo oculto
    document.getElementById('cg-conta-id').value = id;
    
    document.querySelector('.cg-card-title').textContent = 'Analisar Conta';
    document.querySelector('.cg-card-note').textContent = `Visualizando registro #${id}`;

    // 2. Preencher os Inputs Básicos
    document.getElementById('cg-nome-despesa').value = nome;
    
    // Tratativa para quando o fornecedor for vazio ou nulo no banco
    document.getElementById('cg-fornecedor').value = (fornecedor !== 'None' && fornecedor !== '') ? fornecedor : '';

    // 3. Formatar Valor (O input type="number" exige ponto no lugar da vírgula)
    let valorTratado = valor.replace(',', '.');
    document.getElementById('cg-valor').value = parseFloat(valorTratado).toFixed(2);

    // 4. Formatar Data (O Django manda DD/MM/YYYY, mas o HTML precisa de YYYY-MM-DD)
    if (vencimento) {
        let partes = vencimento.split('/');
        if (partes.length === 3) {
            let dataFormatada = `${partes[2]}-${partes[1]}-${partes[0]}`;
            document.getElementById('cg-vencimento').value = dataFormatada;
        }
    }

    // 5. Selecionar a Categoria no Dropdown
    let selectCategoria = document.getElementById('cg-categoria');
    for (let i = 0; i < selectCategoria.options.length; i++) {
        if (selectCategoria.options[i].value === categoria) {
            selectCategoria.selectedIndex = i;
            break;
        }
    }

    // 6. Ajustar a UX do Botão Principal baseado no Status
    let btnSubmit = document.querySelector('#cg-form-agendar button[type="submit"]');
    if (status === 'pago') {
        btnSubmit.innerHTML = '<i class="ph ph-check-circle"></i> Fatura já Paga';
        btnSubmit.style.backgroundColor = '#10b981'; // Verde de sucesso
        btnSubmit.style.borderColor = '#10b981';
        btnSubmit.disabled = true; // Bloqueia edição para não corromper histórico
    } else {
        btnSubmit.innerHTML = '<i class="ph ph-warning"></i> Atualizar Pendência';
        btnSubmit.style.backgroundColor = '#f59e0b'; // Amarelo de alerta
        btnSubmit.style.borderColor = '#f59e0b';
        btnSubmit.disabled = false; // Como ainda não temos lógica de UPDATE na View, vamos apenas deixar visível
    }

    // 7. Injetar um botão "Novo Lançamento" para limpar a tela e voltar a cadastrar
    if (!document.getElementById('btn-limpar-form')) {
        let btnLimpar = document.createElement('button');
        btnLimpar.type = 'button';
        btnLimpar.id = 'btn-limpar-form';
        btnLimpar.className = 'btn form-control mt-2';
        btnLimpar.style.border = '1px dashed #94a3b8';
        btnLimpar.style.color = '#64748b';
        btnLimpar.style.fontWeight = '500';
        btnLimpar.style.background = 'transparent';
        btnLimpar.innerHTML = '<i class="ph ph-plus"></i> Cancelar Análise e Novo Cadastro';
        btnLimpar.onclick = resetarPainel;
        document.getElementById('cg-form-agendar').appendChild(btnLimpar);
    }
}

// Função para voltar o painel ao estado normal de "Novo Cadastro"
function resetarPainel() {
    let form = document.getElementById('cg-form-agendar');
    form.reset(); // Limpa todos os campos digitados
     
    // NOVO: Limpa o ID oculto para voltar ao modo "Criar"
    document.getElementById('cg-conta-id').value = '';
    
    // Restaura o cabeçalho original
    document.querySelector('.cg-card-title').textContent = 'Agendar Obrigação';
    document.querySelector('.cg-card-note').textContent = 'Lançamento rápido vindo do banco.';

    // Restaura o botão original de Salvar
    let btnSubmit = form.querySelector('button[type="submit"]');
    btnSubmit.innerHTML = '<i class="ph ph-floppy-disk"></i> Salvar no Banco';
    btnSubmit.style.backgroundColor = ''; // Volta a puxar a cor CSS do cg-btn-primary
    btnSubmit.style.borderColor = '';
    btnSubmit.disabled = false;

    // Esconde o botão de limpar, pois já estamos no estado limpo
    let btnLimpar = document.getElementById('btn-limpar-form');
    if (btnLimpar) btnLimpar.remove();
}