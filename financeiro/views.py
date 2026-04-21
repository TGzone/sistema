from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from igrejas.models import Igreja

# =========================================================
# 0. DASHBOARD FINANCEIRO PRINCIPAL
# =========================================================
def financeiro(request):
    return render(request, "financeiro/financeiro.html")  

# =========================================================
# 1. VIEW DE MOVIMENTAÇÕES (Caixa Real / Extrato Geral)
# =========================================================
def movimentacoes(request):
    igreja_atual = Igreja.objects.first() # Gambiarra temporária até ligarmos o auth_user

    # === LÓGICA DE SALVAR LANÇAMENTO REAL NO BANCO ===
    if request.method == 'POST':
        tipo = request.POST.get('tipo') # 'ENTRADA' ou 'SAIDA'
        categoria = request.POST.get('categoria')
        descricao = request.POST.get('descricao')
        valor = request.POST.get('valor')
        data = request.POST.get('data')

        if valor:
            valor = valor.replace(',', '.') # Prevenção contra vírgula do Brasil

        Movimentacao.objects.create(
            igreja=igreja_atual,
            tipo=tipo,
            categoria=categoria,
            descricao=descricao,
            valor=valor,
            data=data
        )
        return redirect('financeiro:movimentacoes')

    # === LÓGICA DE EXIBIÇÃO ===
    historico = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data', '-id')[:15]
    
    context = {
        'historico': historico,
        # Adicionado 'TRANSFERENCIA' caso precise registrar envio de malotes aqui futuramente
        'categorias': ['DIZIMO', 'OFERTA', 'MISSIONARIA', 'AVULSA', 'TRANSFERENCIA', 'OUTROS']
    }
    return render(request, "financeiro/movimentacoes.html", context)

# =========================================================
# 2. VIEW DE CONTAS (Previsões e Obrigações Fixas)
# =========================================================
def contas(request):
    igreja_atual = Igreja.objects.first() 
    
    # === LÓGICA DE SALVAR/ATUALIZAR PREVISÃO NO BANCO ===
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id')
        nome = request.POST.get('nome')
        fornecedor = request.POST.get('fornecedor')
        valor = request.POST.get('valor')
        vencimento = request.POST.get('vencimento')
        categoria = request.POST.get('categoria')
        recorrencia = request.POST.get('cg-recorrencia')
        tipo = request.POST.get('tipo', 'SAIDA') # Define se é A Pagar (SAIDA) ou A Receber (ENTRADA)

        if valor:
            valor = valor.replace(',', '.')

        if conta_id:
            # UPDATE (Atualiza conta existente)
            conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
            conta.nome = nome
            conta.empresa = fornecedor
            conta.valor = valor
            conta.vencimento = vencimento
            conta.categoria = categoria
            conta.recorrencia = recorrencia if recorrencia else 'unica'
            conta.tipo = tipo
            conta.save() 
        else:
            # INSERT (Cria nova conta)
            Obrigacao.objects.create(
                igreja=igreja_atual,
                nome=nome,
                empresa=fornecedor,
                valor=valor,
                vencimento=vencimento,
                categoria=categoria,
                recorrencia=recorrencia if recorrencia else 'unica',
                status='pendente',
                tipo=tipo
            )
            
        return redirect('financeiro:contas')

    # === LÓGICA DE EXIBIÇÃO COM SEPARAÇÃO DE TIPO ===
    contas_lista = Obrigacao.objects.filter(igreja=igreja_atual).order_by('vencimento')
    
    # Filtramos separadamente o que é despesa e o que é receita!
    total_pagar = contas_lista.filter(tipo='SAIDA', status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    total_receber = contas_lista.filter(tipo='ENTRADA', status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    contas_vencidas = contas_lista.filter(tipo='SAIDA', status='atrasado').count() 

    context = {
        'contas': contas_lista,
        'total_pagar': total_pagar,
        'total_receber': total_receber,
        'contas_vencidas': contas_vencidas,
    }
    return render(request, 'financeiro/contas.html', context)


# =========================================================
# 3. VIEWS DE MANUTENÇÃO E DETALHES
# =========================================================
def manutencao(request):
    igreja_atual = Igreja.objects.first()
    necessidades = Manutencao.objects.filter(igreja=igreja_atual).order_by('-status')
    return render(request, "financeiro/manutencao.html", {'manutencao': necessidades})

def conta_detalhes(request, conta_id):
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
    return render(request, "financeiro/conta_detalhes.html", {'conta': conta})      


# =========================================================
# 4. COCKPIT BANCÁRIO (Espelho e Saldo)
# =========================================================
def banco(request):
    igreja_atual = Igreja.objects.first() 
    
    # Puxa TODAS as contas bancárias da unidade (Grid)
    contas_bancarias = DadosBancarios.objects.filter(igreja=igreja_atual)
    
    # Puxa o Extrato (Últimos 10 malotes/movimentações)
    extrato = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data', '-id')[:10]
    
    # Função interna para calcular o saldo de cada gaveta dinamicamente
    def calcular_saldo_gaveta(categoria_nome):
        entradas = Movimentacao.objects.filter(
            igreja=igreja_atual, tipo='ENTRADA', categoria=categoria_nome
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        saidas = Movimentacao.objects.filter(
            igreja=igreja_atual, tipo='SAIDA', categoria=categoria_nome
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        return entradas - saidas

    # Calculando as Gavetas
    saldo_dizimos = calcular_saldo_gaveta('DIZIMO')
    saldo_ofertas = calcular_saldo_gaveta('OFERTA')
    saldo_missoes = calcular_saldo_gaveta('MISSIONARIA')
    saldo_construcao = calcular_saldo_gaveta('OUTROS')
    
    # Saldo Consolidado Final
    saldo_total = saldo_dizimos + saldo_ofertas + saldo_missoes + saldo_construcao

    context = {
        'igreja': igreja_atual,
        'contas': contas_bancarias,
        'extrato': extrato,
        'saldo_dizimos': saldo_dizimos,
        'saldo_ofertas': saldo_ofertas,
        'saldo_missoes': saldo_missoes,
        'saldo_construcao': saldo_construcao,
        'saldo_total': saldo_total,
    }
    
    return render(request, 'financeiro/banco.html', context)


# =========================================================
# 5. CRIAR NOVA CONTA BANCÁRIA (POST Apenas)
# =========================================================
def nova_conta(request):
    if request.method == 'POST':
        igreja_id = request.POST.get('igreja_id')
        nome_banco = request.POST.get('banco')
        agencia = request.POST.get('agencia')
        conta = request.POST.get('conta')
        chave_pix = request.POST.get('chave_pix')

        try:
            igreja_obj = Igreja.objects.get(id=igreja_id)
            
            DadosBancarios.objects.create(
                igreja=igreja_obj,
                banco=nome_banco,
                agencia=agencia,
                conta=conta,
                chave_pix=chave_pix
            )
        except Igreja.DoesNotExist:
            pass 

        # Redireciona de volta ao Cockpit após salvar
        return redirect('financeiro:banco')

    return redirect('financeiro:banco')