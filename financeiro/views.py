from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from igrejas.models import Igreja

# =========================================================
# 0. DASHBOARD FINANCEIRO PRINCIPAL
# =========================================================
def financeiro(request):
    """Renderiza a página principal do módulo financeiro."""
    return render(request, "financeiro/financeiro.html")

# =========================================================
# 1. FLUXO DE REGISTROS (Movimentações / Entradas)
# =========================================================
def movimentacoes(request):
    # Usando a primeira igreja como contexto (ajuste conforme seu sistema de login)
    igreja_atual = Igreja.objects.first()

    if request.method == 'POST':
        # Registra uma Entrada manual (Ex: Dízimos, Ofertas)
        Movimentacao.objects.create(
            igreja=igreja_atual,
            tipo='ENTRADA',
            categoria=request.POST.get('categoria'),
            descricao=request.POST.get('descricao'),
            valor=request.POST.get('valor'),
            data=timezone.now()
        )
        return redirect('financeiro:movimentacoes')

    # Busca o histórico completo para a tabela
    movs = Movimentacao.objects.filter(igreja=igreja_atual).order_by('-data')
    
    # Categorias para o seletor do formulário
    categorias = ['DIZIMO', 'OFERTA', 'MISSIONARIA', 'AVULSA', 'OUTROS']
    
    return render(request, "financeiro/movimentacao.html", {
        'movimentacoes': movs,
        'categorias': categorias
    })

# =========================================================
# 2. CENTRAL DE OBRIGAÇÕES (Contas a Pagar)
# =========================================================
def contas(request):
    igreja_atual = Igreja.objects.first()

    if request.method == 'POST':
        # Adiciona uma nova conta para o mês
        Obrigacao.objects.create(
            igreja=igreja_atual,
            descricao=request.POST.get('descricao'),
            valor=request.POST.get('valor'),
            vencimento=request.POST.get('vencimento'),
            status='pendente',
            recorrencia=request.POST.get('recorrencia', 'unica')
        )
        return redirect('financeiro:contas')

    # Lista de contas para a tabela da esquerda
    obrigacoes = Obrigacao.objects.filter(igreja=igreja_atual).order_by('vencimento')
    
    return render(request, "financeiro/contas.html", {
        'contas': obrigacoes
    })

# =========================================================
# 3. LÓGICA DE PAGAMENTO (A conexão Contas -> Banco)
# =========================================================
def pagar_conta(request, conta_id):
    """
    Função que altera o status da conta e gera a saída automática no banco.
    """
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)

    if request.method == 'POST':
        # 1. Marca a conta como paga
        conta.status = 'pago'
        conta.save()

        # 2. CRIA A SAÍDA NO BANCO (Subtração automática)
        # Isso faz com que o saldo no Cockpit Bancário diminua no mesmo instante.
        Movimentacao.objects.create(
            igreja=igreja_atual,
            tipo='SAIDA',
            categoria='PAGAMENTO',
            descricao=f"Pgto: {conta.descricao}",
            valor=conta.valor,
            data=timezone.now()
        )

    return redirect('financeiro:contas')

# =========================================================
# 4. COCKPIT BANCÁRIO (Saldos e Contas)
# =========================================================
def banco(request):
    igreja_atual = Igreja.objects.first()
    
    # Cálculos matemáticos para os Cards de monitoramento
    total_entradas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = Movimentacao.objects.filter(igreja=igreja_atual, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Saldo Real (Entradas - Saídas)
    saldo_atual = total_entradas - total_saidas
    
    # Dados da conta bancária física da igreja
    dados_bancarios = DadosBancarios.objects.filter(igreja=igreja_atual).first()

    context = {
        'saldo_atual': saldo_atual,
        'entradas': total_entradas,
        'saidas': total_saidas,
        'dados_banco': dados_bancarios
    }
    return render(request, "financeiro/banco.html", context)

# =========================================================
# 5. AUXILIARES: DETALHES E NOVA CONTA BANCÁRIA
# =========================================================
def conta_detalhes(request, conta_id):
    igreja_atual = Igreja.objects.first()
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja_atual)
    return render(request, "financeiro/conta_detalhes.html", {'conta': conta})

def nova_conta(request):
    """Salva os dados bancários institucionais."""
    if request.method == 'POST':
        igreja_atual = Igreja.objects.first()
        DadosBancarios.objects.update_or_create(
            igreja=igreja_atual,
            defaults={
                'nome_banco': request.POST.get('banco'),
                'agencia': request.POST.get('agencia'),
                'conta': request.POST.get('conta'),
                'chave_pix': request.POST.get('chave_pix')
            }
        )
    return redirect('financeiro:banco')

# =========================================================
# 6. CENTRAL DE MANUTENÇÃO
# =========================================================
def manutencao(request):
    igreja_atual = Igreja.objects.first()
    necessidades = Manutencao.objects.filter(igreja=igreja_atual).order_by('-status')
    return render(request, "financeiro/manutencao.html", {'manutencao': necessidades})