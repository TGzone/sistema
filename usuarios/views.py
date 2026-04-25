from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from usuarios.permissoes import perfil_requerido
from .models import UsuarioSistema
from igrejas.models import Igreja
from pessoas.models import Pessoa


# ─────────────────────────────────────────────
# 1. LOGIN
# ─────────────────────────────────────────────


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '')   # HTML usa name="password"

        usuario = authenticate(request, username=email, password=senha)

        if usuario is None:
            messages.error(request, 'E-mail ou senha incorretos.')
            return render(request, 'usuarios/login.html')

        if usuario.status == 'PENDENTE':
            messages.warning(request, 'Sua conta ainda está em análise. Aguarde a aprovação.')
            return render(request, 'usuarios/login.html')

        if usuario.status == 'INATIVO':
            messages.error(request, 'Seu acesso foi revogado. Fale com o administrador.')
            return render(request, 'usuarios/login.html')

        auth_login(request, usuario)
        return redirect('dashboard')

    return render(request, 'usuarios/login.html')


# ─────────────────────────────────────────────
# 2. LOGOUT
# ─────────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


# ─────────────────────────────────────────────
# 3. CADASTRO PÚBLICO (Porta da Rua)
# ─────────────────────────────────────────────
def cadastro_usuarios(request):
    igrejas = Igreja.objects.filter(status='ATIVO').order_by('nome')

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        email     = request.POST.get('email', '').strip()
        telefone  = request.POST.get('telefone', '').strip()
        igreja_id = request.POST.get('igreja_id')
        perfil    = request.POST.get('perfil_solicitado', 'tesoureiro')
        senha     = request.POST.get('senha', '')
        confirma  = request.POST.get('confirmar_senha', '')

        if senha != confirma:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'usuarios/cadastro_usuarios.html', {'igrejas': igrejas})

        if UsuarioSistema.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado ou em análise.')
            return render(request, 'usuarios/cadastro_usuarios.html', {'igrejas': igrejas})

        igreja = Igreja.objects.filter(id=igreja_id).first() if igreja_id else None

        UsuarioSistema.objects.create_user(
            email=email,
            password=senha,
            nome_solicitante=nome,
            telefone=telefone,
            igreja=igreja,
            perfil=perfil,
            status='PENDENTE',
        )
        messages.success(request, 'Solicitação enviada! Aguarde a aprovação da liderança.')
        return redirect('usuarios:login')

    return render(request, 'usuarios/cadastro_usuarios.html', {'igrejas': igrejas})


# ─────────────────────────────────────────────
# 4. CADASTRO INTERNO (Porta VIP)
# ─────────────────────────────────────────────
@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def cadastro_usuarios_sistema(request):
    igrejas = Igreja.objects.filter(status='ATIVO').order_by('nome')

    if request.method == 'POST':
        nome      = request.POST.get('nome', '').strip()
        email     = request.POST.get('email', '').strip()
        telefone  = request.POST.get('telefone', '').strip()
        igreja_id = request.POST.get('igreja_id')
        perfil    = request.POST.get('perfil_solicitado', 'tesoureiro')
        senha     = request.POST.get('senha', '')
        confirma  = request.POST.get('confirmar_senha', '')

        if senha != confirma:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'usuarios/cadastro_usuarios_sistema.html', {'igrejas': igrejas})

        if UsuarioSistema.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já existe no sistema.')
            return render(request, 'usuarios/cadastro_usuarios_sistema.html', {'igrejas': igrejas})

        igreja = Igreja.objects.filter(id=igreja_id).first() if igreja_id else None

        UsuarioSistema.objects.create_user(
            email=email,
            password=senha,
            nome_solicitante=nome,
            telefone=telefone,
            igreja=igreja,
            perfil=perfil,
            status='ATIVO',
        )
        messages.success(request, f'Usuário {nome} criado com sucesso!')
        return redirect('usuarios:lista_solicitacoes')

    return render(request, 'usuarios/cadastro_usuarios_sistema.html', {'igrejas': igrejas})


# ─────────────────────────────────────────────
# 5. LISTA / GESTÃO DE ACESSOS
# ─────────────────────────────────────────────
@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def lista_solicitacoes(request):
    if request.user.perfil == 'presidente':
        pendentes = UsuarioSistema.objects.filter(status='PENDENTE').select_related('igreja')
        ativos    = UsuarioSistema.objects.filter(status='ATIVO').select_related('igreja', 'pessoa')
        inativos  = UsuarioSistema.objects.filter(status='INATIVO').select_related('igreja')
    else:
        pendentes = UsuarioSistema.objects.filter(status='PENDENTE', igreja=request.user.igreja).select_related('igreja')
        ativos    = UsuarioSistema.objects.filter(status='ATIVO',    igreja=request.user.igreja).select_related('igreja', 'pessoa')
        inativos  = UsuarioSistema.objects.filter(status='INATIVO',  igreja=request.user.igreja).select_related('igreja')

    return render(request, 'usuarios/lista_solicitacoes.html', {
        'solicitacoes_pendentes': pendentes,
        'usuarios_ativos':        ativos,
        'usuarios_inativos':      inativos,
    })


# ─────────────────────────────────────────────
# 6. APROVAR
# ─────────────────────────────────────────────
@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def aprovar_usuario(request, pk):
    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    if request.method == 'POST':
        pessoa_id = request.POST.get('pessoa_id')
        usuario.status = 'ATIVO'
        if pessoa_id:
            try:
                usuario.pessoa = Pessoa.objects.get(pk=pessoa_id)
            except Pessoa.DoesNotExist:
                pass
        usuario.save()
        messages.success(request, f'{usuario.nome_solicitante} aprovado!')
    return redirect('usuarios:lista_solicitacoes')


# ─────────────────────────────────────────────
# 7. NEGAR / REVOGAR / REATIVAR
# ─────────────────────────────────────────────
@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def negar_usuario(request, pk):
    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    usuario.status = 'INATIVO'
    usuario.save()
    messages.warning(request, f'Solicitação de {usuario.nome_solicitante} negada.')
    return redirect('usuarios:lista_solicitacoes')


@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def revogar_usuario(request, pk):
    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    usuario.status = 'INATIVO'
    usuario.save()
    messages.warning(request, f'Acesso de {usuario.nome_solicitante} revogado.')
    return redirect('usuarios:lista_solicitacoes')


@login_required
@perfil_requerido('PRESIDENTE', 'PASTOR_UNIDADE')
def reativar_usuario(request, pk):
    usuario = get_object_or_404(UsuarioSistema, pk=pk)
    usuario.status = 'ATIVO'
    usuario.save()
    messages.success(request, f'{usuario.nome_solicitante} reativado.')
    return redirect('usuarios:lista_solicitacoes')


# ─────────────────────────────────────────────
# 8. API — busca de pessoas para vincular
# ─────────────────────────────────────────────
@login_required
def api_buscar_pessoa(request):
    termo = request.GET.get('q', '').strip()
    if len(termo) < 2:
        return JsonResponse([], safe=False)
    pessoas = Pessoa.objects.filter(nome__icontains=termo, ativo=True)[:10]
    return JsonResponse(
        [{'id': p.id, 'nome': p.nome, 'tipo': p.get_tipo_display()} for p in pessoas],
        safe=False
    )