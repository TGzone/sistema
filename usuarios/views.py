from django.shortcuts import render

def login_view(request):
    # Por agora, apenas renderizamos o visual
    return render(request, 'usuarios/login.html')


def cadastro_usuarios(request):
    # Por agora, apenas renderizamos o visual
    return render(request, 'usuarios/cadastro_usuarios.html')


def lista_solicitacoes(request):
    # Por agora, apenas renderizamos o visual
    return render(request, 'usuarios/lista_solicitacoes.html')

def cadastro_usuarios_sistema(request):
    # Por agora, apenas renderizamos o visual
    return render(request, 'usuarios/cadastro_usuarios_sistema.html')
    