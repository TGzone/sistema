from django.shortcuts import render
from .models import Movimentacao, ContaFixa, Manutencao, DadosBancarios

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
    contas_list = ContaFixa.objects.all().order_by('vencimento_dia')
    return render(request, "financeiro/contas.html", {'contas': contas_list})

def manutencao(request):
    necessidades = Manutencao.objects.all().order_by('-status')
    return render(request, "financeiro/manutencao.html", {'manutencao': necessidades})

def bancos(request):
    info_bancaria = DadosBancarios.objects.all()
    return render(request, "financeiro/bancos.html", {'bancos': info_bancaria})