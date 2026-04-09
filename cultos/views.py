import calendar
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import Culto

def calendario(request):
    hoje = date.today()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))

    # Matriz do Calendário
    cal = calendar.Calendar(firstweekday=6)
    semanas = cal.monthdayscalendar(ano, mes)

    # Cultos do Mês para o Grid
    cultos_mes = Culto.objects.filter(data__year=ano, data__month=mes)
    
    cultos_por_dia = {}
    for culto in cultos_mes:
        dia = culto.data.day
        if dia not in cultos_por_dia:
            cultos_por_dia[dia] = []
        cultos_por_dia[dia].append(culto)

    # Lógica do Monitoramento (Próximos 7 dias)
    # Pega de hoje em diante para mostrar o que está "LIVE" ou por vir
    data_limite = hoje + timedelta(days=7)
    cultos_proximos = Culto.objects.filter(
        data__range=[hoje, data_limite]
    ).order_by('data', 'horario')

    meses_pt = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    context = {
        'semanas': semanas,
        'mes_nome': meses_pt[mes],
        'ano': ano,
        'mes': mes,
        'cultos_por_dia': cultos_por_dia,
        'cultos_proximos': cultos_proximos, # <--- Importante para o painel inferior
        'hoje': hoje,
    }
    return render(request, 'cultos/cultos.html', context)

def criar_culto(request):
    if request.method == "POST":
        titulo = request.POST.get('titulo')
        data_evento = request.POST.get('data')
        horario = request.POST.get('horario')
        tipo = request.POST.get('tipo')
        
        # Aqui você precisa do ID da igreja, vou assumir que você pega da sessão 
        # ou tem uma igreja padrão para o teste
        # Ex: igreja_id = request.user.perfil.igreja.id
        
        Culto.objects.create(
            titulo=titulo,
            data=data_evento,
            horario=horario,
            tipo=tipo,
            igreja_id=1 # Ajuste para a lógica real depois
        )
    return redirect('cultos:calendario')

def detalhe_culto(request, pk):
    culto = get_object_or_404(Culto, pk=pk)
    return render(request, 'cultos/detalhe.html', {'culto': culto})