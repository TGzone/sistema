from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Cadastros
    path('solicitar-acesso/', views.cadastro_usuarios,         name='cadastro_usuarios'),
    path('cadastrar/',        views.cadastro_usuarios_sistema,  name='cadastro_usuarios_sistema'),

    # Gestão — pk DEPOIS da ação para bater com o JS
    path('acessos/',                       views.lista_solicitacoes, name='lista_solicitacoes'),
    path('acessos/aprovar/<int:pk>/',      views.aprovar_usuario,    name='aprovar'),
    path('acessos/vincular/<int:pk>/',     views.vincular_pessoa,    name='vincular'),
    path('acessos/negar/<int:pk>/',        views.negar_usuario,      name='negar'),
    path('acessos/revogar/<int:pk>/',      views.revogar_usuario,    name='revogar'),
    path('acessos/reativar/<int:pk>/',     views.reativar_usuario,   name='reativar'),

    # API
    path('api/buscar-pessoa/', views.api_buscar_pessoa, name='api_buscar_pessoa'),
]