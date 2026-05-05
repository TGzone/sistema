from django.urls import path
from . import views

app_name = 'pessoas'

urlpatterns = [
    # Listagem principal (O seu redirect da view usa 'pessoas:pessoas' ou 'pessoas:lista')
    path('', views.pessoas, name='pessoas'), 
    path('lista/', views.pessoas, name='lista'), # Atalho extra caso use 'lista' no redirect
    
    # Cadastro
    path('cadastro/', views.cadastro, name='cadastro'),
    
    # Detalhes via JSON para o Drawer
    path('<int:pessoa_id>/detail/', views.pessoa_detail, name='detail'),
    
    # Edição (Processamento do Form do Drawer)
    path('editar/<int:pk>/', views.editar_pessoa, name='editar'),
    
    # Ativação e Desativação (As novas funções!)
    path('ativar/<int:pk>/', views.ativar_membro, name='ativar_membro'),
    path('desativar/<int:pk>/', views.desativar_membro, name='desativar_membro'),
    
    path('cadastro-membro/', views.auto_cadastro, name='auto_cadastro'),


]
