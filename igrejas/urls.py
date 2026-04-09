from django.urls import path
from . import views

# O app_name permite usar o namespace nos templates: {% url 'igrejas:nome_da_rota' %}
app_name = 'igrejas'

urlpatterns = [
    # 1. Dashboard de Unidades (Lista de Cards)
    path('', views.igrejas_lista, name='lista'),
    
    # 2. Cadastro de Novas Unidades (Expansão)
    path('cadastro/', views.cadastro_igreja, name='cadastro'), 
    
    # 3. Centro de Comando da Unidade (Página interna)
    path('unidade/<int:id>/', views.unidade_detalhe, name='unidade_detalhe'),
    
    # 4. Ações do Drawer (Editar, Remanejar, Pastor) - ESSA RESOLVE O ERRO
    path('unidade/<int:id>/acoes/', views.unidade_acoes, name='unidade_acoes'),
    
    # 5. API de Busca de Liderança (Modal e Drawer Inteligente)
    path('api/busca-lideranca/', views.api_busca_lideranca, name='api_busca_lideranca'),

]