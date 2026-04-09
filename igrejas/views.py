from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from .models import Igreja, Evento
from pessoas.models import Pessoa 

# 1. DASHBOARD DE UNIDADES (LISTA DE CARDS)
def igrejas_lista(request):
    """Lista as unidades com contagem real de membros e pastores via annotate"""
    igrejas = Igreja.objects.annotate(
        total_membros_unidade=Count('membros'), 
        total_pastores_unidade=Count('membros', filter=Q(membros__tipo__iexact='pastor'))
    ).select_related('pastor').order_by('nome')
    
    total_membros = Pessoa.objects.count()
    
    return render(request, "igrejas/igrejas.html", {
        "igrejas": igrejas,
        "total_membros": total_membros
    })

# 2. CENTRO DE COMANDO (DETALHE DA UNIDADE)
def unidade_detalhe(request, id):
    """Exibe o painel de controle da igreja específica"""
    unidade = get_object_or_404(Igreja, pk=id)
    membros_reais = Pessoa.objects.filter(unidade=unidade, ativo=True).order_by('nome')
    eventos = Evento.objects.filter(igreja=unidade).order_by('data_hora')
    
    return render(request, "igrejas/unidade.html", {
        "unidade": unidade,
        "membros_unidade": membros_reais,
        "eventos": eventos
    })

# 3. AÇÕES DINÂMICAS (Edição, Remanejamento e Liderança)
def unidade_acoes(request, id):
    """Gerencia Edição, trocas de pastores e remanejamento de membros via POST único (Drawer)"""
    unidade = get_object_or_404(Igreja, pk=id)
    
    if request.method == "POST":
        acao = request.POST.get("acao_tipo")
        
        if acao == "editar":
            # Dados Básicos
            unidade.nome = request.POST.get('nome', unidade.nome)
            unidade.cnpj = request.POST.get('cnpj', unidade.cnpj)
            unidade.telefone = request.POST.get('telefone', unidade.telefone)
            unidade.tipo = request.POST.get('tipo', unidade.tipo)
            
            # Localização
            unidade.cep = request.POST.get('cep', unidade.cep)
            unidade.rua = request.POST.get('rua', unidade.rua)
            unidade.numero = request.POST.get('numero', unidade.numero)
            unidade.bairro = request.POST.get('bairro', unidade.bairro)
            unidade.cidade = request.POST.get('cidade', unidade.cidade)
            unidade.estado = request.POST.get('estado', unidade.estado)
            
            # Estrutura e Status
            unidade.capacidade = request.POST.get('capacidade') or 0
            unidade.status = request.POST.get('status', unidade.status)
            unidade.observacoes = request.POST.get('observacoes', unidade.observacoes)
            
            unidade.save()
            messages.success(request, f"Unidade '{unidade.nome}' atualizada com sucesso!")

        elif acao == "remanejar":
            pessoa_id = request.POST.get("pessoa_id")
            if pessoa_id:
                pessoa = get_object_or_404(Pessoa, pk=pessoa_id)
                pessoa.unidade = unidade
                pessoa.save()
                messages.success(request, f"{pessoa.nome} remanejado para {unidade.nome}!")

        elif acao == "atribuir_pastor":
            p_id = request.POST.get("pessoa_id") or request.POST.get("pastor_id")
            if p_id:
                pastor_obj = get_object_or_404(Pessoa, pk=p_id)
                unidade.pastor = pastor_obj 
                unidade.save()
                messages.success(request, f"O {pastor_obj.get_tipo_display()} {pastor_obj.nome} assumiu a liderança!")

    return redirect("igrejas:unidade_detalhe", id=id)

# 4. API DE BUSCA (AJAX)
def api_busca_lideranca(request):
    termo = request.GET.get('busca', '').strip()
    if len(termo) >= 3:
        pessoas = Pessoa.objects.filter(
            Q(nome__icontains=termo) | Q(telefone__icontains=termo),
            ativo=True
        )[:10]
        data = [{
            'id': p.id,
            'nome': p.nome,
            'cargo': p.get_tipo_display(),
            'unidade': p.unidade.nome if p.unidade else "Sem Unidade"
        } for p in pessoas]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

# 5. CADASTRO DE UNIDADES
def cadastro_igreja(request):
    if request.method == 'POST':
        try:
            nova = Igreja.objects.create(
                nome=request.POST.get('nome'),
                cnpj=request.POST.get('cnpj'),
                cidade=request.POST.get('cidade'),
                bairro=request.POST.get('bairro'),
                capacidade=request.POST.get('capacidade') or 0,
                status='ATIVO'
            )
            messages.success(request, f"Unidade '{nova.nome}' cadastrada!")
            return redirect('igrejas:igrejas_lista')
        except Exception as e:
            messages.error(request, f"Erro: {e}")
    return render(request, 'igrejas/cadastro_igrejas.html')