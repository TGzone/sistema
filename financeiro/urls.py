# financeiro/urls.py

from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # ── Dashboard ────────────────────────────────────────────
    path('',                                    views.financeiro,          name='financeiro'),

    # ── Movimentações ─────────────────────────────────────────
    path('movimentacoes/',                      views.movimentacoes,       name='movimentacoes'),

    # ── Contas / Obrigações ───────────────────────────────────
    path('contas/',                             views.contas,              name='contas'),
    path('contas/<int:conta_id>/',              views.conta_detalhes,      name='conta_detalhes'),
    path('contas/<int:conta_id>/pagar/',        views.pagar_conta,         name='pagar_conta'),
    path('contas/<int:conta_id>/deletar/',      views.deletar_conta,       name='deletar_conta'),

    # ── Banco ─────────────────────────────────────────────────
    path('banco/',                              views.banco,               name='banco'),
    path('banco/nova-conta/',                   views.nova_conta,          name='nova_conta'),

    # ── Manutenção ────────────────────────────────────────────
    path('manutencao/',                         views.manutencao,          name='manutencao'),

    # ── APIs internas ─────────────────────────────────────────
    path('api/membros/',                        views.api_buscar_membro,   name='api_membros'),

    # ── PIX — página pública + APIs ───────────────────────────
    path('pagar/',                              views.pagamento_pix,       name='pagamento_pix'),
    path('api/gerar-pix/',                      views.api_gerar_pix,       name='api_gerar_pix'),
    path('api/status-pix/<str:pagamento_id>/',  views.api_status_pix,      name='api_status_pix'),
    path('webhook/mp/',                         views.webhook_mercadopago, name='webhook_mp'),
    path('webhook/n8n/', views.processar_pix_publico, name='webhook_n8n'), 
]