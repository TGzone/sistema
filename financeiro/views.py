# financeiro/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from pessoas.models import Pessoa
from usuarios.permissoes import perfil_requerido, PERFIS_GERENCIAIS


# ─────────────────────────────────────────────────────────────
# HELPER: igreja do usuário logado
# ─────────────────────────────────────────────────────────────
def _igreja(request):
    """Retorna a igreja vinculada ao usuário logado."""
    return request.user.igreja


# ─────────────────────────────────────────────────────────────
# HELPER: saldo por gaveta (categoria)
# ─────────────────────────────────────────────────────────────
def _saldo_gaveta(igreja, categoria):
    e = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    s = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA',   categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    return e - s


# ─────────────────────────────────────────────────────────────
# 0. DASHBOARD FINANCEIRO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def financeiro(request):
    igreja = _igreja(request)

    hoje = timezone.now().date()
    primeiro_dia_mes = hoje.replace(day=1)

    total_entradas = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_atual    = total_entradas - total_saidas

    entradas_mes = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_mes   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA',   data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0

    ultimas = Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')[:10]

    manutencoes_urgentes = Manutencao.objects.filter(igreja=igreja, status='URGENTE')

    return render(request, 'financeiro/financeiro.html', {
        'igreja':               igreja,
        'saldo_atual':          saldo_atual,
        'entradas_mes':         entradas_mes,
        'saidas_mes':           saidas_mes,
        'ultimas_movimentacoes': ultimas,
        'manutencoes_urgentes': manutencoes_urgentes,
    })


# ─────────────────────────────────────────────────────────────
# 1. FLUXO DE REGISTROS (Entradas)
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def movimentacoes(request):
    igreja = _igreja(request)

    if request.method == 'POST':
        tipo_raw  = request.POST.get('tipo', 'OUTROS').upper()
        categoria = tipo_raw if tipo_raw in dict(Movimentacao.CATEGORIA_CHOICES) else 'OUTROS'
        ocasiao   = request.POST.get('ocasiao', '')
        justif    = request.POST.get('justificativa', '')

        descricao = justif if ocasiao == 'atipico' else f"{categoria.capitalize()} - {ocasiao}"

        # Vincula membro se informado pelo ID (campo hidden no form)
        membro_id = request.POST.get('membro_id')
        membro    = Pessoa.objects.filter(pk=membro_id).first() if membro_id else None

        Movimentacao.objects.create(
            igreja         = igreja,
            tipo           = 'ENTRADA',
            categoria      = categoria,
            descricao      = descricao,
            valor          = request.POST.get('valor'),
            data           = request.POST.get('data') or timezone.now().date(),
            membro         = membro,
            autorizado_por = request.user,
        )
        return redirect('financeiro:movimentacoes')

    # Lista membros da unidade para o autocomplete
    membros = Pessoa.objects.filter(unidade=igreja, ativo=True).order_by('nome')
    movs    = Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')

    return render(request, 'financeiro/movimentacoes.html', {
        'movimentacoes': movs,
        'membros':       membros,
        'igreja':        igreja,
    })


# ─────────────────────────────────────────────────────────────
# 2. CENTRAL DE OBRIGAÇÕES
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def contas(request):
    igreja = _igreja(request)

    if request.method == 'POST':
        acao       = request.POST.get('acao')
        conta_id   = request.POST.get('conta_id')
        comprovante = request.FILES.get('comprovante') or request.FILES.get('comprovante_gallery')

        if conta_id:
            conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja)

            if acao == 'pagar':
                conta.status         = 'pago'
                conta.autorizado_por = request.user
                if comprovante:
                    conta.comprovante = comprovante
                conta.save()

                Movimentacao.objects.create(
                    igreja         = igreja,
                    tipo           = 'SAIDA',
                    categoria      = request.POST.get('gaveta', 'OUTROS'),
                    descricao      = f"Pgto: {conta.nome}",
                    valor          = conta.valor,
                    data           = timezone.now().date(),
                    autorizado_por = request.user,
                )
                return redirect('financeiro:contas')

            # Edição
            conta.nome        = request.POST.get('nome')
            conta.empresa     = request.POST.get('fornecedor')
            conta.valor       = request.POST.get('valor')
            conta.vencimento  = request.POST.get('vencimento')
            conta.categoria   = request.POST.get('categoria', 'Outros')
            conta.recorrencia = request.POST.get('cg-recorrencia', 'unica')
            conta.tipo        = request.POST.get('tipo', 'SAIDA')
            if comprovante:
                conta.comprovante = comprovante
            conta.save()

        else:
            Obrigacao.objects.create(
                igreja         = igreja,
                nome           = request.POST.get('nome'),
                empresa        = request.POST.get('fornecedor', ''),
                valor          = request.POST.get('valor'),
                vencimento     = request.POST.get('vencimento'),
                categoria      = request.POST.get('categoria', 'Outros'),
                recorrencia    = request.POST.get('cg-recorrencia', 'unica'),
                tipo           = request.POST.get('tipo', 'SAIDA'),
                status         = 'pendente',
                comprovante    = comprovante,
                autorizado_por = request.user,
            )

        return redirect('financeiro:contas')

    hoje       = timezone.now().date()
    obrigacoes = Obrigacao.objects.filter(igreja=igreja).order_by('vencimento')
    obrigacoes.filter(vencimento__lt=hoje, status='pendente').update(status='atrasado')

    total_pagar   = obrigacoes.filter(tipo='SAIDA',   status__in=['pendente', 'atrasado']).aggregate(Sum('valor'))['valor__sum'] or 0
    total_receber = obrigacoes.filter(tipo='ENTRADA', status__in=['pendente', 'atrasado']).aggregate(Sum('valor'))['valor__sum'] or 0
    contas_vencidas = obrigacoes.filter(status='atrasado').count()

    gavetas = [
        {'valor': 'DIZIMO',      'label': 'Dízimos',    'saldo': _saldo_gaveta(igreja, 'DIZIMO')},
        {'valor': 'OFERTA',      'label': 'Ofertas',    'saldo': _saldo_gaveta(igreja, 'OFERTA')},
        {'valor': 'MISSIONARIA', 'label': 'Missões',    'saldo': _saldo_gaveta(igreja, 'MISSIONARIA')},
        {'valor': 'AVULSA',      'label': 'Construção', 'saldo': _saldo_gaveta(igreja, 'AVULSA')},
        {'valor': 'OUTROS',      'label': 'Outros',     'saldo': _saldo_gaveta(igreja, 'OUTROS')},
    ]

    return render(request, 'financeiro/contas.html', {
        'contas':         obrigacoes,
        'total_pagar':    total_pagar,
        'total_receber':  total_receber,
        'contas_vencidas': contas_vencidas,
        'gavetas':        gavetas,
        'igreja':         igreja,
    })


# ─────────────────────────────────────────────────────────────
# 3. DELETAR CONTA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def deletar_conta(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    if request.method == 'POST':
        conta.delete()
    return redirect('financeiro:contas')


# ─────────────────────────────────────────────────────────────
# 4. PAGAR CONTA (rota legada)
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def pagar_conta(request, conta_id):
    igreja = _igreja(request)
    conta  = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja)
    if request.method == 'POST':
        conta.status         = 'pago'
        conta.autorizado_por = request.user
        conta.save()
        Movimentacao.objects.create(
            igreja         = igreja,
            tipo           = 'SAIDA',
            categoria      = request.POST.get('gaveta', 'OUTROS'),
            descricao      = f"Pgto: {conta.nome}",
            valor          = conta.valor,
            data           = timezone.now().date(),
            autorizado_por = request.user,
        )
    return redirect('financeiro:contas')


# ─────────────────────────────────────────────────────────────
# 5. COCKPIT BANCÁRIO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def banco(request):
    igreja = _igreja(request)

    total_entradas = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0

    return render(request, 'financeiro/banco.html', {
        'saldo_atual':      total_entradas - total_saidas,
        'entradas':         total_entradas,
        'saidas':           total_saidas,
        'contas':           DadosBancarios.objects.filter(igreja=igreja),
        'extrato':          Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')[:20],
        'saldo_dizimos':    _saldo_gaveta(igreja, 'DIZIMO'),
        'saldo_ofertas':    _saldo_gaveta(igreja, 'OFERTA'),
        'saldo_missoes':    _saldo_gaveta(igreja, 'MISSIONARIA'),
        'saldo_construcao': _saldo_gaveta(igreja, 'AVULSA'),
        'igreja':           igreja,
    })


# ─────────────────────────────────────────────────────────────
# 6. NOVA CONTA BANCÁRIA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def nova_conta(request):
    if request.method == 'POST':
        DadosBancarios.objects.update_or_create(
            igreja=_igreja(request),
            defaults={
                'banco':      request.POST.get('banco'),
                'agencia':    request.POST.get('agencia'),
                'conta':      request.POST.get('conta'),
                'chave_pix':  request.POST.get('chave_pix', ''),
            }
        )
    return redirect('financeiro:banco')


# ─────────────────────────────────────────────────────────────
# 7. DETALHE DE CONTA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def conta_detalhes(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    return render(request, 'financeiro/conta_detalhes.html', {'conta': conta})


# ─────────────────────────────────────────────────────────────
# 8. MANUTENÇÃO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def manutencao(request):
    igreja = _igreja(request)
    if request.method == 'POST':
        Manutencao.objects.create(
            igreja     = igreja,
            item       = request.POST.get('title'),
            status     = request.POST.get('urgency', 'NECESSARIO').upper(),
            observacao = request.POST.get('description', ''),
        )
        return redirect('financeiro:manutencao')

    necessidades = Manutencao.objects.filter(igreja=igreja).order_by('-status')
    return render(request, 'financeiro/manutencao.html', {'manutencao': necessidades})


# ─────────────────────────────────────────────────────────────
# 9. API — busca de membros para autocomplete no lançamento
# ─────────────────────────────────────────────────────────────
@login_required
def api_buscar_membro(request):
    from django.http import JsonResponse
    termo  = request.GET.get('q', '').strip()
    igreja = _igreja(request)
    if len(termo) < 2:
        return JsonResponse([], safe=False)
    pessoas = Pessoa.objects.filter(nome__icontains=termo, ativo=True)[:10]
    return JsonResponse(
        [{'id': p.id, 'nome': p.nome, 'tipo': p.get_tipo_display(), 'unidade': p.unidade.nome if p.unidade else 'Sem unidade'} for p in pessoas],
        safe=False,
    )