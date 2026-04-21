from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.financeiro, name='financeiro'),
    
    # Movimentações
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    
    # Contas / Obrigações
    path('contas/', views.contas, name='contas'),
    path('contas/<int:conta_id>/', views.conta_detalhes, name='conta_detalhes'),
    path('contas/<int:conta_id>/pagar/', views.pagar_conta, name='pagar_conta'), # <--- NOVA ROTA DE PAGAMENTO
    
    # Banco
    path('banco/', views.banco, name='banco'),
    path('banco/nova-conta/', views.nova_conta, name='nova_conta'),
    
    # Manutenção
    path('manutencao/', views.manutencao, name='manutencao'),
]