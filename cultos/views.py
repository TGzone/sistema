import calendar
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import Culto

def calendario(request):
    hoje = date.today()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    
    # ID fixo para fase de testes (Sem Auth por enquanto)
    TEST_IGREJA_ID = 1 

    cal = calendar.Calendar(firstweekday=6)
    semanas = cal.monthdayscalendar(ano, mes)

    # Filtro de Unidade Única aplicado
    cultos_mes = Culto.objects.filter(igreja_id=TEST_IGREJA_ID, data__year=ano, data__month=mes)
    
    cultos_por_dia = {}
    for culto in cultos_mes:
        dia = culto.data.day
        if dia not in cultos_por_dia:
            cultos_por_dia[dia] = []
        cultos_por_dia[dia].append(culto)

    # Monitoramento: 7 dias para gatilho LIVE
    data_limite = hoje + timedelta(days=7)
    cultos_proximos = Culto.objects.filter(
        igreja_id=TEST_IGREJA_ID,
        data__range=[hoje, data_limite]
    ).order_by('data', 'horario')

    meses_pt = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    context = {
        'semanas': semanas,
        'mes_nome': meses_pt[mes],
        'ano': ano,
        'mes': mes,
        'cultos_por_dia': cultos_por_dia,
        'cultos_proximos': cultos_proximos,
        'hoje': hoje,
    }
    return render(request, 'cultos/cultos.html', context)


# ==========================================
# A PONTE DE DADOS (Atualizada com novas cores e observações)
# ==========================================
def criar_culto(request): 
    if request.method == "POST":
        # Dados Básicos
        titulo = request.POST.get('titulo')
        data_evento = request.POST.get('data')
        horario = request.POST.get('horario')
        tipo = request.POST.get('tipo', 'culto_domingo')
        
        # Novos Detalhes (Observações e Opcionais)
        descricao = request.POST.get('descricao', '')
        pregador = request.POST.get('pregador_palestrante', '')
        local = request.POST.get('local', 'Templo Principal')
        
        # O Pulo do Gato (Visual e Cores)
        cor = request.POST.get('cor_personalizada', '#2563eb')
        estilo = request.POST.get('estilo_card', 'solido')
        
        # ID 1 fixo para fase de testes (Unidade Única)
        Culto.objects.create(
            titulo=titulo,
            data=data_evento,
            horario=horario,
            tipo=tipo,
            descricao=descricao,
            pregador_palestrante=pregador,
            local=local,
            cor_personalizada=cor,
            estilo_card=estilo,
            igreja_id=1 
        )
    return redirect('cultos:calendario')


def detalhe_culto(request, pk):
    culto = get_object_or_404(Culto, pk=pk)
    return render(request, 'cultos/detalhe_culto.html', {'culto': culto})

def detalhe_culto(request, pk):
    culto = get_object_or_404(Culto, pk=pk)
    
    if request.method == "POST":
        # Se enviou o formulário, atualiza os dados
        culto.titulo = request.POST.get('titulo')
        culto.data = request.POST.get('data')
        culto.horario = request.POST.get('horario')
        culto.tipo = request.POST.get('tipo')
        culto.descricao = request.POST.get('descricao', '')
        culto.cor_personalizada = request.POST.get('cor_personalizada', '#2563eb')
        culto.estilo_card = request.POST.get('estilo_card', 'solido')
        culto.save()
        return redirect('cultos:calendario')
        
    # Se for GET, apenas mostra a tela preenchida
    return render(request, 'cultos/detalhe_culto.html', {'culto': culto})

def excluir_culto(request, pk):
    culto = get_object_or_404(Culto, pk=pk)
    culto.delete()
    return redirect('cultos:calendario')
