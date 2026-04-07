from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from .models import Igreja, Evento
from pessoas.models import Pessoa 

# 1. DASHBOARD DE UNIDADES (LISTA DE CARDS)
def igrejas_lista(request):
    """Lista as congregações com estatísticas de membros e pastores via SQL"""
    igrejas = Igreja.objects.annotate(
        total_membros_unidade=Count('membros'),
        total_pastores_unidade=Count('membros', filter=Q(membros__tipo='pastor'))
    ).order_by('nome')
    
    total_membros = Pessoa.objects.count()
    
    return render(request, "igrejas/igrejas.html", {
        "igrejas": igrejas,
        "total_membros": total_membros
    })

# 2. CENTRO DE COMANDO (DETALHE DA UNIDADE)
def unidade_detalhe(request, id):
    """Exibe o painel de controle da igreja específica"""
    unidade = get_object_or_404(Igreja, pk=id)
    
    # Filtra membros ativos desta unidade e eventos agendados
    membros_reais = Pessoa.objects.filter(unidade=unidade, ativo=True).order_by('nome')
    eventos = Evento.objects.filter(igreja=unidade).order_by('data_hora')
    
    return render(request, "igrejas/unidade.html", {
        "unidade": unidade,
        "membros_unidade": membros_reais,
        "eventos": eventos
    })

# 3. PROCESSADOR DE AÇÕES DINÂMICAS (DRAWER POST)
def unidade_acoes(request, id):
    """Gerencia Edição, Remanejamento e Liderança (via ForeignKey)"""
    unidade = get_object_or_404(Igreja, pk=id)
    
    if request.method == "POST":
        acao = request.POST.get("acao_tipo")
        
        # AÇÃO: EDITAR DADOS ESTRUTURAIS
        if acao == "editar":
            unidade.nome = request.POST.get("nome", unidade.nome)
            unidade.cnpj = request.POST.get("cnpj", unidade.cnpj)
            unidade.telefone = request.POST.get("telefone", unidade.telefone)
            unidade.cidade = request.POST.get("cidade", unidade.cidade)
            unidade.bairro = request.POST.get("bairro", unidade.bairro)
            unidade.capacidade = request.POST.get("capacidade") or 0
            
            # Atualiza campos de endereço se existirem no Model
            for campo in ['rua', 'numero', 'cep']:
                if hasattr(unidade, campo):
                    setattr(unidade, campo, request.POST.get(campo, getattr(unidade, campo)))
            
            unidade.save()
            messages.success(request, f"Dados de '{unidade.nome}' atualizados!")

        # AÇÃO: REMANEJAR PESSOA PARA ESTA UNIDADE
        elif acao == "remanejar":
            pessoa_id = request.POST.get("pessoa_id")
            if pessoa_id:
                pessoa = get_object_or_404(Pessoa, pk=pessoa_id)
                pessoa.unidade = unidade
                pessoa.save()
                messages.success(request, f"{pessoa.nome} remanejado com sucesso!")
            else:
                messages.error(request, "Erro: Pessoa não selecionada.")

        # AÇÃO: ATRIBUIR PASTOR DIRIGENTE (Relacionamento de Tabelas)
        elif acao == "atribuir_pastor":
            p_id = request.POST.get("pessoa_id") or request.POST.get("pastor_id")
            if p_id:
                pastor_obj = get_object_or_404(Pessoa, pk=p_id)
                unidade.pastor = pastor_obj # Salva a instância (ForeignKey)
                unidade.save()
                messages.success(request, f"Liderança de {pastor_obj.nome} vinculada!")
            else:
                messages.error(request, "Erro ao identificar o líder.")

    return redirect("igrejas:unidade_detalhe", id=id)

# 4. API DE BUSCA GLOBAL (AJAX)
def api_busca_lideranca(request):
    """Busca em tempo real para o Drawer (Qualquer pessoa ativa)"""
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
                capacidade=request.POST.get('capacidade') or 0,
                status='ATIVO'
            )
            messages.success(request, f"Unidade '{nova.nome}' cadastrada!")
            return redirect('igrejas:lista')
        except Exception as e:
            messages.error(request, f"Erro: {e}")

    return render(request, 'igrejas/cadastro_igrejas.html')