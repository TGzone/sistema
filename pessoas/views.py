from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from datetime import date
from .models import Pessoa, Endereco
from igrejas.models import Igreja 

def calcular_idade(data_nascimento):
    if not data_nascimento:
        return "-"
    hoje = date.today()
    try:
        return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    except:
        return "-"

def pessoas(request):
    pessoas_list = Pessoa.objects.all().order_by("nome")
    for p in pessoas_list:
        p.idade = calcular_idade(p.data_nascimento)
        p.tipo_slug = p.tipo
        p.tipo_nome = p.get_tipo_display()
        p.status_acompanhamento_display = p.get_status_acompanhamento_display() if p.status_acompanhamento else "-"
    
    todas_pessoas = Pessoa.objects.all().order_by("nome")
    
    return render(request, "pessoas/pessoas.html", {
        "pessoas": pessoas_list,
        "todas_pessoas": todas_pessoas
    })

def cadastro(request):
    unidade_pre_selecionada = request.GET.get('unidade_id')

    if request.method == "POST":
        eh_membro_oficial = request.POST.get("membro_desta_igreja") == "on"
        unidade_escolhida = request.POST.get("unidade")

        try:
            novo_end = Endereco.objects.create(
                rua=request.POST.get("rua"),
                numero=request.POST.get("numero"),
                bairro=request.POST.get("bairro"),
                cidade=request.POST.get("cidade"),
                estado=request.POST.get("estado"),
                cep=request.POST.get("cep")
            )

            Pessoa.objects.create(
                nome=request.POST.get("nome"),
                email=request.POST.get("email") or None,
                telefone=request.POST.get("telefone"),
                sexo=request.POST.get("sexo"),
                tipo=request.POST.get("tipo"),
                unidade_id=unidade_escolhida if unidade_escolhida else None,
                data_nascimento=request.POST.get("data_nascimento") or None,
                igreja_origem=request.POST.get("igreja_origem"),
                status_acompanhamento=request.POST.get("status_acompanhamento"),
                membro_desta_igreja=eh_membro_oficial,
                ativo=True,
                responsavel_id=request.POST.get("responsavel") if request.POST.get("responsavel") else None,
                endereco=novo_end,
                observacoes=request.POST.get("observacoes")
            )
            
            messages.success(request, "Cadastro realizado com sucesso!")
            
            # Lógica de redirecionamento inteligente
            if unidade_escolhida:
                return redirect("igrejas:unidade_detalhe", id=unidade_escolhida)
            return redirect("pessoas:pessoas")
            
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar: {e}")

    context = {
        "igrejas": Igreja.objects.all().order_by("nome"),
        "tipos": Pessoa.TIPO,
        "unidade_pre_selecionada": unidade_pre_selecionada
    }
    return render(request, "pessoas/cadastro.html", context)

def editar_pessoa(request, pk):
    pessoa = get_object_or_404(Pessoa, pk=pk)
    
    if request.method == 'POST':
        unidade_escolhida = request.POST.get("unidade")
        
        pessoa.nome = request.POST.get('nome', pessoa.nome)
        pessoa.telefone = request.POST.get('telefone', pessoa.telefone)
        pessoa.email = request.POST.get('email', pessoa.email)
        pessoa.sexo = request.POST.get('sexo', pessoa.sexo)
        pessoa.tipo = request.POST.get('tipo', pessoa.tipo)
        pessoa.unidade_id = unidade_escolhida if unidade_escolhida else None
        pessoa.data_nascimento = request.POST.get('data_nascimento') or None
        pessoa.estado_civil = request.POST.get('estado_civil', pessoa.estado_civil)
        pessoa.igreja_origem = request.POST.get('igreja_origem', pessoa.igreja_origem)
        pessoa.ministerio = request.POST.get('ministerio', pessoa.ministerio)
        pessoa.observacoes = request.POST.get('observacoes', pessoa.observacoes)
        pessoa.status_acompanhamento = request.POST.get('status_acompanhamento', pessoa.status_acompanhamento)
        pessoa.membro_desta_igreja = request.POST.get("membro_desta_igreja") == "on"
        
        resp_id = request.POST.get('responsavel')
        pessoa.responsavel_id = resp_id if resp_id else None
        
        dados_end = {
            'rua': request.POST.get('rua'),
            'numero': request.POST.get('numero'),
            'bairro': request.POST.get('bairro'),
            'cidade': request.POST.get('cidade'),
            'estado': request.POST.get('estado'),
            'cep': request.POST.get('cep'),
        }

        if pessoa.endereco:
            for campo, valor in dados_end.items():
                setattr(pessoa.endereco, campo, valor)
            pessoa.endereco.save()
        else:
            pessoa.endereco = Endereco.objects.create(**dados_end)
        
        pessoa.save()
        messages.success(request, "Dados atualizados!")

        # Redireciona conforme a origem
        if unidade_escolhida:
            return redirect("igrejas:unidade_detalhe", id=unidade_escolhida)
        return redirect("pessoas:pessoas")
    
    return render(request, "pessoas/editar.html", {
        "pessoa": pessoa,
        "igrejas": Igreja.objects.all().order_by("nome"),
        "tipos": Pessoa.TIPO
    })

def ativar_membro(request, pk):
    pessoa = get_object_or_404(Pessoa, pk=pk)
    pessoa.ativo = True
    pessoa.save()
    return redirect("pessoas:pessoas")

def desativar_membro(request, pk):
    pessoa = get_object_or_404(Pessoa, pk=pk)
    pessoa.ativo = False
    pessoa.save()
    return redirect("pessoas:pessoas")

def pessoa_detail(request, pessoa_id):
    pessoa = get_object_or_404(Pessoa, id=pessoa_id)
    end_data = {}
    if pessoa.endereco:
        end_data = {
            "rua": pessoa.endereco.rua or "",
            "numero": pessoa.endereco.numero or "",
            "bairro": pessoa.endereco.bairro or "",
            "cidade": pessoa.endereco.cidade or "",
            "estado": pessoa.endereco.estado or "",
            "cep": pessoa.endereco.cep or "",
        }
    
    data = {
        "id": pessoa.id,
        "nome": pessoa.nome,
        "idade": calcular_idade(pessoa.data_nascimento),
        "telefone": pessoa.telefone or "",
        "email": pessoa.email or "",
        "sexo": pessoa.sexo or "", 
        "data_nascimento": pessoa.data_nascimento.isoformat() if pessoa.data_nascimento else "",
        "estado_civil": pessoa.estado_civil or "",
        "igreja_origem": pessoa.igreja_origem or "",
        "ministerio": pessoa.ministerio or "",
        "observacoes": pessoa.observacoes or "",
        "tipo": pessoa.get_tipo_display(),
        "tipo_raw": pessoa.tipo,
        "ativo": pessoa.ativo,
        "responsavel": pessoa.responsavel.id if pessoa.responsavel else "", 
        "status_acompanhamento": pessoa.get_status_acompanhamento_display() if pessoa.status_acompanhamento else "-",
        "status_raw": pessoa.status_acompanhamento or "",
        "endereco": end_data, 
    }
    return JsonResponse(data)