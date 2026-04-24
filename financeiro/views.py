from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from igrejas.models import Igreja

# =========================================================
# HELPER: saldo por categoria de gaveta
# =========================================================
def _saldo_gaveta(igreja, categoria):
    e = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    s = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA', categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    return e - s

# =========================================================
# 0. DASHBOARD FINANCEIRO PRINCIPAL
# =========================================================
def financeiro(request):
    return render(request, "financeiro/financeiro.html")

# =========================================================
# 1. FLUXO DE REGISTROS (Movimentações / Entradas)
# =========================================================
def movimentacoes(request):
    igreja_atual = Igreja.objects.first()

    if request.method == 'POST':
        tipo_raw = request.POST.get('tipo', 'OUTROS').upper()
        mapa_categoria = {
            'DIZIMO': 'DIZIMO',
            'OFERTA': 'OFERTA',
            'MISSIONARIA': 'MISSIONARIA',
            'AVULSA': 'AVULSA',
            'OUTROS': 'OUTROS',
        }
        categoria = mapa_categoria.get(tipo_raw, 'OUTROS')
        ocasiao = request.POST.get('ocasiao', '')
        justificativa = request.POST.get('justificativa', '')
        descricao = f"{categoria.capitalize()} - {ocasiao}" if ocasiao != 'atipico' else justificativa

        Movimentacao.objects.create(
            igreja=igreja_atual,
            tipo='ENTRADA',
            categoria=categoria,
            descricao=descricao,
            valor=request.POST.get('valor'),
            data=request.POST.get('data') or timezone.now().date(),
        )
        return redirect('financeiro:movimentacoes')

    movs = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data')
    return render(request, "financeiro/movimentacoes.html", {
        'movimentacoes': movs,
        'igreja': igreja_atual,
    })

# =========================================================
# 2. CENTRAL DE OBRIGAÇÕES (Contas a Pagar)
# =========================================================
def contas(request):
    igreja_atual = Igreja.objects.first()

    if request.method == 'POST':
        acao = request.POST.get('acao')
        conta_id = request.POST.get('conta_id')

        # ✅ Pega o comprovante (câmera ou galeria)
        comprovante = request.FILES.get('comprovante') or request.FILES.get('comprovante_gallery')

        if conta_id:
            conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)

            if acao == 'pagar':
                gaveta = request.POST.get('gaveta', 'OUTROS')
                conta.status = 'pago'
                if comprovante:
                    conta.comprovante = comprovante
                conta.save()
                Movimentacao.objects.create(
                    igreja=igreja_atual,
                    tipo='SAIDA',
                    categoria=gaveta,
                    descricao=f"Pgto: {conta.nome}",
                    valor=conta.valor,
                    data=timezone.now().date(),
                )
                return redirect('financeiro:contas')

            # Edição
            conta.nome = request.POST.get('nome')
            conta.empresa = request.POST.get('fornecedor')
            conta.valor = request.POST.get('valor')
            conta.vencimento = request.POST.get('vencimento')
            conta.categoria = request.POST.get('categoria', 'Outros')
            conta.recorrencia = request.POST.get('cg-recorrencia', 'unica')
            conta.tipo = request.POST.get('tipo', 'SAIDA')
            if comprovante:
                conta.comprovante = comprovante
            conta.save()

        else:
            # Nova conta
            Obrigacao.objects.create(
                igreja=igreja_atual,
                nome=request.POST.get('nome'),
                empresa=request.POST.get('fornecedor', ''),
                valor=request.POST.get('valor'),
                vencimento=request.POST.get('vencimento'),
                categoria=request.POST.get('categoria', 'Outros'),
                recorrencia=request.POST.get('cg-recorrencia', 'unica'),
                tipo=request.POST.get('tipo', 'SAIDA'),
                status='pendente',
                comprovante=comprovante,  # pode ser None, tudo bem
            )

        return redirect('financeiro:contas')

    hoje = timezone.now().date()
    obrigacoes = Obrigacao.objects.filter(igreja=igreja_atual).order_by('vencimento')
    obrigacoes.filter(vencimento__lt=hoje, status='pendente').update(status='atrasado')

    total_pagar = obrigacoes.filter(tipo='SAIDA', status__in=['pendente', 'atrasado']).aggregate(Sum('valor'))['valor__sum'] or 0
    contas_vencidas = obrigacoes.filter(status='atrasado').count()

    total_entradas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_caixa = total_entradas - total_saidas

    gavetas = [
        {'valor': 'DIZIMO',      'label': 'Dízimos',    'saldo': _saldo_gaveta(igreja_atual, 'DIZIMO')},
        {'valor': 'OFERTA',      'label': 'Ofertas',    'saldo': _saldo_gaveta(igreja_atual, 'OFERTA')},
        {'valor': 'MISSIONARIA', 'label': 'Missões',    'saldo': _saldo_gaveta(igreja_atual, 'MISSIONARIA')},
        {'valor': 'AVULSA',      'label': 'Construção', 'saldo': _saldo_gaveta(igreja_atual, 'AVULSA')},
        {'valor': 'OUTROS',      'label': 'Outros',     'saldo': _saldo_gaveta(igreja_atual, 'OUTROS')},
    ]

    return render(request, "financeiro/contas.html", {
        'contas': obrigacoes,
        'total_pagar': total_pagar,
        'contas_vencidas': contas_vencidas,
        'saldo_caixa': saldo_caixa,
        'gavetas': gavetas,
        'igreja': igreja_atual,
    })

# =========================================================
# 3. EXCLUIR CONTA
# =========================================================
def deletar_conta(request, conta_id):
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
    if request.method == 'POST':
        conta.delete()
    return redirect('financeiro:contas')

# =========================================================
# 4. PAGAMENTO DIRETO POR URL (rota legada)
# =========================================================
def pagar_conta(request, conta_id):
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
    if request.method == 'POST':
        gaveta = request.POST.get('gaveta', 'OUTROS')
        conta.status = 'pago'
        conta.save()
        Movimentacao.objects.create(
            igreja=igreja_atual,
            tipo='SAIDA',
            categoria=gaveta,
            descricao=f"Pgto: {conta.nome}",
            valor=conta.valor,
            data=timezone.now().date(),
        )
    return redirect('financeiro:contas')

# =========================================================
# 5. COCKPIT BANCÁRIO
# =========================================================
def banco(request):
    igreja_atual = Igreja.objects.first()

    total_entradas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_atual = total_entradas - total_saidas

    contas_bancarias = DadosBancarios.objects.filter(igreja=igreja_atual)
    extrato = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data')[:20]

    return render(request, "financeiro/banco.html", {
        'saldo_atual': saldo_atual,
        'entradas': total_entradas,
        'saidas': total_saidas,
        'contas': contas_bancarias,
        'extrato': extrato,
        'saldo_dizimos': _saldo_gaveta(igreja_atual, 'DIZIMO'),
        'saldo_ofertas': _saldo_gaveta(igreja_atual, 'OFERTA'),
        'saldo_missoes': _saldo_gaveta(igreja_atual, 'MISSIONARIA'),
        'saldo_construcao': _saldo_gaveta(igreja_atual, 'AVULSA'),
        'igreja': igreja_atual,
    })

# =========================================================
# 6. AUXILIARES
# =========================================================
def conta_detalhes(request, conta_id):
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
    return render(request, "financeiro/conta_detalhes.html", {'conta': conta})

def nova_conta(request):
    if request.method == 'POST':
        igreja_atual = Igreja.objects.first()
        DadosBancarios.objects.update_or_create(
            igreja=igreja_atual,
            defaults={
                'banco': request.POST.get('banco'),
                'agencia': request.POST.get('agencia'),
                'conta': request.POST.get('conta'),
                'chave_pix': request.POST.get('chave_pix', ''),
            }
        )
    return redirect('financeiro:banco')

# =========================================================
# 7. CENTRAL DE MANUTENÇÃO
# =========================================================
def manutencao(request):
    igreja_atual = Igreja.objects.first()
    if request.method == 'POST':
        Manutencao.objects.create(
            igreja=igreja_atual,
            item=request.POST.get('title'),
            status=request.POST.get('urgency', 'NECESSARIO').upper(),
            observacao=request.POST.get('description', ''),
        )
        return redirect('financeiro:manutencao')

    necessidades = Manutencao.objects.filter(igreja=igreja_atual).order_by('-status')
    return render(request, "financeiro/manutencao.html", {'manutencao': necessidades})