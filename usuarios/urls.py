from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Cadastros
    path('solicitar-acesso/',  views.cadastro_usuarios,         name='cadastro_usuarios'),
    path('cadastrar/',         views.cadastro_usuarios_sistema,  name='cadastro_usuarios_sistema'),

    # Gestão
    path('acessos/',                    views.lista_solicitacoes, name='lista_solicitacoes'),
    path('acessos/<int:pk>/aprovar/',   views.aprovar_usuario,    name='aprovar'),
    path('acessos/<int:pk>/negar/',     views.negar_usuario,      name='negar'),
    path('acessos/<int:pk>/revogar/',   views.revogar_usuario,    name='revogar'),
    path('acessos/<int:pk>/reativar/',  views.reativar_usuario,   name='reativar'),

    # API
    path('api/buscar-pessoa/', views.api_buscar_pessoa, name='api_buscar_pessoa'),
]