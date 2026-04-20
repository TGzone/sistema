from django.shortcuts import render, redirect, get_object_or_404
from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from igrejas.models import Igreja
from financeiro.models import Obrigacao, Manutencao, DadosBancarios, Movimentacao
from django.db.models import Sum # Aproveita e já importa isso para calcularmos o Total
# --- MÓDULO FINANCEIRO ---

def financeiro(request):
    return render(request, "financeiro/financeiro.html")  

def movimentacoes(request):
    historico = Movimentacao.objects.all().order_by('-data')[:15]
    
    context = {
        'historico': historico,
        'categorias': ['DIZIMO', 'OFERTA', 'MISSIONARIA', 'AVULSA', 'OUTROS']
    }
    return render(request, "financeiro/movimentacoes.html", context)

def contas(request):
    # Pega a primeira igreja do banco de dados (Gambi temporária para testar)
    igreja_atual = Igreja.objects.first() 
    
    # === LÓGICA DE SALVAR/ATUALIZAR NO BANCO ===
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id') # Pega o ID oculto!
        nome = request.POST.get('nome')
        fornecedor = request.POST.get('fornecedor')
        valor = request.POST.get('valor')
        vencimento = request.POST.get('vencimento')
        categoria = request.POST.get('categoria')
        recorrencia = request.POST.get('cg-recorrencia')

        if valor:
            valor = valor.replace(',', '.')

        if conta_id:
            # MODO ATUALIZAÇÃO (UPDATE)
            conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
            conta.nome = nome
            conta.empresa = fornecedor
            conta.valor = valor
            conta.vencimento = vencimento
            conta.categoria = categoria
            conta.recorrencia = recorrencia if recorrencia else 'unica'
            conta.save() # Salva por cima da antiga!
        else:
            # MODO CRIAÇÃO (INSERT)
            Obrigacao.objects.create(
                igreja=igreja_atual,
                nome=nome,
                empresa=fornecedor,
                valor=valor,
                vencimento=vencimento,
                categoria=categoria,
                recorrencia=recorrencia if recorrencia else 'unica',
                status='pendente'
            )
            
        return redirect('financeiro:contas')

    # === LÓGICA DE EXIBIÇÃO ===
    contas_lista = Obrigacao.objects.filter(igreja=igreja_atual).order_by('vencimento')
    
    total_pagar = contas_lista.filter(status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    contas_vencidas = contas_lista.filter(status='atrasado').count()

    context = {
        'contas': contas_lista,
        'total_pagar': total_pagar,
        'contas_vencidas': contas_vencidas,
    }
    
    return render(request, 'financeiro/contas.html', context)

def manutencao(request):
    necessidades = Manutencao.objects.all().order_by('-status')
    return render(request, "financeiro/manutencao.html", {'manutencao': necessidades})

def bancos(request):
    info_bancaria = DadosBancarios.objects.all()
    return render(request, "financeiro/bancos.html", {'bancos': info_bancaria})

def conta_detalhes(request, conta_id):
    conta = Obrigacao.objects.get(id=conta_id)
    return render(request, "financeiro/conta_detalhes.html", {'conta': conta})      


def banco_espelho(request):
    igreja_atual = Igreja.objects.first() # Temporário até ter o login pronto
    dados_bancarios = DadosBancarios.objects.filter(igreja=igreja_atual).first()
    
    # Busca todas as movimentações da unidade
    movimentacoes = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data', '-id')
    
    # 1. Cálculo do Saldo Total (Entradas - Saídas)
    total_entradas = movimentacoes.filter(tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = movimentacoes.filter(tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_total = total_entradas - total_saidas

    # 2. Cálculo das Gavetas (Buckets)
    # Dizimos
    entradas_dizimo = movimentacoes.filter(tipo='ENTRADA', categoria='DIZIMO').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_dizimo = movimentacoes.filter(tipo='SAIDA', categoria='DIZIMO').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_dizimos = entradas_dizimo - saidas_dizimo

    # Ofertas Locais
    entradas_oferta = movimentacoes.filter(tipo='ENTRADA', categoria='OFERTA').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_oferta = movimentacoes.filter(tipo='SAIDA', categoria='OFERTA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_ofertas = entradas_oferta - saidas_oferta

    # Missões
    entradas_missoes = movimentacoes.filter(tipo='ENTRADA', categoria='MISSIONARIA').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_missoes = movimentacoes.filter(tipo='SAIDA', categoria='MISSIONARIA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_missoes = entradas_missoes - saidas_missoes

    # Construção / Outros
    entradas_outros = movimentacoes.filter(tipo='ENTRADA', categoria='OUTROS').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_outros = movimentacoes.filter(tipo='SAIDA', categoria='OUTROS').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_construcao = entradas_outros - saidas_outros

    context = {
        'igreja': igreja_atual,
        'banco': dados_bancarios,
        'saldo_total': saldo_total,
        'saldo_dizimos': saldo_dizimos,
        'saldo_ofertas': saldo_ofertas,
        'saldo_missoes': saldo_missoes,
        'saldo_construcao': saldo_construcao,
        'extrato': movimentacoes[:10] # Mostra as 10 últimas na tela
    }
    
    return render(request, 'financeiro/banco.html', context)
