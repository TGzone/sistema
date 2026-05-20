# financeiro/urls.py

from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('',                              views.financeiro,     name='financeiro'),
    path('movimentacoes/',                views.movimentacoes,  name='movimentacoes'),
    path('contas/',                       views.contas,         name='contas'),
    path('contas/<int:conta_id>/',        views.conta_detalhes, name='conta_detalhes'),
    path('contas/<int:conta_id>/pagar/',  views.pagar_conta,    name='pagar_conta'),
    path('contas/<int:conta_id>/deletar/', views.deletar_conta, name='deletar_conta'),
    path('banco/',                        views.banco,          name='banco'),
    path('banco/nova-conta/',             views.nova_conta,     name='nova_conta'),
    path('manutencao/',                   views.manutencao,     name='manutencao'),

    # API interna — usada pelo autocomplete e futuramente pelo n8n
    path('api/membros/',                  views.api_buscar_membro, name='api_membros'),
]