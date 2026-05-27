# financeiro/views.py

import json
import os
import uuid
import base64
import io
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Movimentacao, Obrigacao, Manutencao, DadosBancarios
from igrejas.models import Igreja
from pessoas.models import Pessoa
from usuarios.permissoes import perfil_requerido, PERFIS_GERENCIAIS
import json
import uuid
import re
import logging
from decimal import Decimal
import requests
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
 
from .models import PagamentoPix, Movimentacao
from igrejas.models import Igreja
 
logger = logging.getLogger(__name__)
 

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def _igreja(request):
    return request.user.igreja


def _saldo_gaveta(igreja, categoria):
    e = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    s = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA',   categoria=categoria).aggregate(Sum('valor'))['valor__sum'] or 0
    return e - s


def _label_tipo(tipo):
    return {
        'DIZIMO':      'Dízimo',
        'OFERTA':      'Oferta',
        'MISSIONARIA': 'Oferta Missionária',
        'AVULSA':      'Fundo de Construção',
    }.get(tipo, 'Contribuição')


# ─────────────────────────────────────────────────────────────
# 0. DASHBOARD FINANCEIRO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def financeiro(request):
    igreja = _igreja(request)
    hoje = timezone.now().date()
    primeiro_dia_mes = hoje.replace(day=1)

    total_entradas = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0

    entradas_mes = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_mes   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA',   data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0

    ultimas              = Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')[:10]
    manutencoes_urgentes = Manutencao.objects.filter(igreja=igreja, status='URGENTE')

    return render(request, 'financeiro/financeiro.html', {
        'igreja':                igreja,
        'saldo_atual':           total_entradas - total_saidas,
        'entradas_mes':          entradas_mes,
        'saidas_mes':            saidas_mes,
        'ultimas_movimentacoes': ultimas,
        'manutencoes_urgentes':  manutencoes_urgentes,
    })


# ─────────────────────────────────────────────────────────────
# 1. FLUXO DE REGISTROS
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def movimentacoes(request):
    igreja = _igreja(request)

    if request.method == 'POST':
        tipo_raw  = request.POST.get('tipo', 'OUTROS').upper()
        categoria = tipo_raw if tipo_raw in dict(Movimentacao.CATEGORIA_CHOICES) else 'OUTROS'
        ocasiao   = request.POST.get('ocasiao', '')
        justif    = request.POST.get('justificativa', '')
        descricao = justif if ocasiao == 'atipico' else f"{categoria.capitalize()} - {ocasiao}"

        membro_id = request.POST.get('membro_id')
        membro    = Pessoa.objects.filter(pk=membro_id).first() if membro_id else None

        Movimentacao.objects.create(
            igreja         = igreja,
            tipo           = 'ENTRADA',
            categoria      = categoria,
            descricao      = descricao,
            valor          = request.POST.get('valor'),
            data           = request.POST.get('data') or timezone.now().date(),
            membro         = membro,
            autorizado_por = request.user,
        )
        return redirect('financeiro:movimentacoes')

    membros = Pessoa.objects.filter(unidade=igreja, ativo=True).order_by('nome')
    movs    = Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')

    return render(request, 'financeiro/movimentacoes.html', {
        'movimentacoes': movs,
        'membros':       membros,
        'igreja':        igreja,
    })


# ─────────────────────────────────────────────────────────────
# 2. CENTRAL DE OBRIGAÇÕES
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def contas(request):
    igreja = _igreja(request)

    if request.method == 'POST':
        acao        = request.POST.get('acao')
        conta_id    = request.POST.get('conta_id')
        comprovante = request.FILES.get('comprovante') or request.FILES.get('comprovante_gallery')

        if conta_id:
            conta = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja)

            if acao == 'pagar':
                conta.status         = 'pago'
                conta.autorizado_por = request.user
                if comprovante:
                    conta.comprovante = comprovante
                conta.save()
                Movimentacao.objects.create(
                    igreja         = igreja,
                    tipo           = 'SAIDA',
                    categoria      = request.POST.get('gaveta', 'OUTROS'),
                    descricao      = f"Pgto: {conta.nome}",
                    valor          = conta.valor,
                    data           = timezone.now().date(),
                    autorizado_por = request.user,
                )
                return redirect('financeiro:contas')

            # Edição
            conta.nome        = request.POST.get('nome')
            conta.empresa     = request.POST.get('fornecedor')
            conta.valor       = request.POST.get('valor')
            conta.vencimento  = request.POST.get('vencimento')
            conta.categoria   = request.POST.get('categoria', 'Outros')
            conta.recorrencia = request.POST.get('cg-recorrencia', 'unica')
            conta.tipo        = request.POST.get('tipo', 'SAIDA')
            if comprovante:
                conta.comprovante = comprovante
            conta.save()

        else:
            Obrigacao.objects.create(
                igreja         = igreja,
                nome           = request.POST.get('nome'),
                empresa        = request.POST.get('fornecedor', ''),
                valor          = request.POST.get('valor'),
                vencimento     = request.POST.get('vencimento'),
                categoria      = request.POST.get('categoria', 'Outros'),
                recorrencia    = request.POST.get('cg-recorrencia', 'unica'),
                tipo           = request.POST.get('tipo', 'SAIDA'),
                status         = 'pendente',
                comprovante    = comprovante,
                autorizado_por = request.user,
            )

        return redirect('financeiro:contas')

    hoje       = timezone.now().date()
    obrigacoes = Obrigacao.objects.filter(igreja=igreja).order_by('vencimento')
    obrigacoes.filter(vencimento__lt=hoje, status='pendente').update(status='atrasado')

    total_pagar     = obrigacoes.filter(tipo='SAIDA',   status__in=['pendente', 'atrasado']).aggregate(Sum('valor'))['valor__sum'] or 0
    total_receber   = obrigacoes.filter(tipo='ENTRADA', status__in=['pendente', 'atrasado']).aggregate(Sum('valor'))['valor__sum'] or 0
    contas_vencidas = obrigacoes.filter(status='atrasado').count()

    gavetas = [
        {'valor': 'DIZIMO',      'label': 'Dízimos',    'saldo': _saldo_gaveta(igreja, 'DIZIMO')},
        {'valor': 'OFERTA',      'label': 'Ofertas',    'saldo': _saldo_gaveta(igreja, 'OFERTA')},
        {'valor': 'MISSIONARIA', 'label': 'Missões',    'saldo': _saldo_gaveta(igreja, 'MISSIONARIA')},
        {'valor': 'AVULSA',      'label': 'Construção', 'saldo': _saldo_gaveta(igreja, 'AVULSA')},
        {'valor': 'OUTROS',      'label': 'Outros',     'saldo': _saldo_gaveta(igreja, 'OUTROS')},
    ]

    return render(request, 'financeiro/contas.html', {
        'contas':          obrigacoes,
        'total_pagar':     total_pagar,
        'total_receber':   total_receber,
        'contas_vencidas': contas_vencidas,
        'gavetas':         gavetas,
        'igreja':          igreja,
    })


# ─────────────────────────────────────────────────────────────
# 3. DELETAR CONTA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def deletar_conta(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    if request.method == 'POST':
        conta.delete()
    return redirect('financeiro:contas')


# ─────────────────────────────────────────────────────────────
# 4. PAGAR CONTA (rota legada via form)
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def pagar_conta(request, conta_id):
    igreja = _igreja(request)
    conta  = get_object_or_404(Obrigacao, id=conta_id, igreja=igreja)
    if request.method == 'POST':
        conta.status         = 'pago'
        conta.autorizado_por = request.user
        conta.save()
        Movimentacao.objects.create(
            igreja         = igreja,
            tipo           = 'SAIDA',
            categoria      = request.POST.get('gaveta', 'OUTROS'),
            descricao      = f"Pgto: {conta.nome}",
            valor          = conta.valor,
            data           = timezone.now().date(),
            autorizado_por = request.user,
        )
    return redirect('financeiro:contas')


# ─────────────────────────────────────────────────────────────
# 5. COCKPIT BANCÁRIO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def banco(request):
    igreja = _igreja(request)

    total_entradas = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0

    return render(request, 'financeiro/banco.html', {
        'saldo_atual':      total_entradas - total_saidas,
        'entradas':         total_entradas,
        'saidas':           total_saidas,
        'contas':           DadosBancarios.objects.filter(igreja=igreja),
        'extrato':          Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')[:20],
        'saldo_dizimos':    _saldo_gaveta(igreja, 'DIZIMO'),
        'saldo_ofertas':    _saldo_gaveta(igreja, 'OFERTA'),
        'saldo_missoes':    _saldo_gaveta(igreja, 'MISSIONARIA'),
        'saldo_construcao': _saldo_gaveta(igreja, 'AVULSA'),
        'igreja':           igreja,
    })


# ─────────────────────────────────────────────────────────────
# 6. NOVA CONTA BANCÁRIA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def nova_conta(request):
    if request.method == 'POST':
        DadosBancarios.objects.update_or_create(
            igreja=_igreja(request),
            defaults={
                'banco':     request.POST.get('banco'),
                'agencia':   request.POST.get('agencia'),
                'conta':     request.POST.get('conta'),
                'chave_pix': request.POST.get('chave_pix', ''),
            }
        )
    return redirect('financeiro:banco')


# ─────────────────────────────────────────────────────────────
# 7. DETALHE DE CONTA
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def conta_detalhes(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    return render(request, 'financeiro/conta_detalhes.html', {'conta': conta})


# ─────────────────────────────────────────────────────────────
# 8. MANUTENÇÃO
# ─────────────────────────────────────────────────────────────
@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def manutencao(request):
    igreja = _igreja(request)
    if request.method == 'POST':
        Manutencao.objects.create(
            igreja     = igreja,
            item       = request.POST.get('title'),
            status     = request.POST.get('urgency', 'NECESSARIO').upper(),
            observacao = request.POST.get('description', ''),
        )
        return redirect('financeiro:manutencao')

    necessidades = Manutencao.objects.filter(igreja=igreja).order_by('-status')
    return render(request, 'financeiro/manutencao.html', {'manutencao': necessidades})


# ─────────────────────────────────────────────────────────────
# 9. API — autocomplete de membros
# ─────────────────────────────────────────────────────────────
@login_required
def api_buscar_membro(request):
    termo  = request.GET.get('q', '').strip()
    igreja = _igreja(request)
    if len(termo) < 2:
        return JsonResponse([], safe=False)
    pessoas = Pessoa.objects.filter(nome__icontains=termo, unidade=igreja, ativo=True)[:10]
    return JsonResponse(
        [{'id': p.id, 'nome': p.nome, 'tipo': p.get_tipo_display(), 'unidade': p.unidade.nome if p.unidade else ''} for p in pessoas],
        safe=False,
    )


# ─────────────────────────────────────────────────────────────
# 10. PÁGINA PÚBLICA DE PAGAMENTO PIX
# ─────────────────────────────────────────────────────────────
def pagamento_pix(request):
    """Pública — qualquer pessoa pode acessar para contribuir."""
    igreja = Igreja.objects.filter(status='ATIVO').first()
    return render(request, 'financeiro/pagamento_pix.html', {'igreja': igreja})


# ─────────────────────────────────────────────────────────────
# 11. API — gerar cobrança PIX
# ─────────────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def api_gerar_pix(request):
    """
    Recebe JSON: { nome, valor, tipo, igreja_id }
    Retorna:     { pagamento_id, qr_code_url, pix_code }

    Com MP_ACCESS_TOKEN no .env → Mercado Pago real.
    Sem token → modo simulação (QR gerado localmente).
    """
    try:
        body      = json.loads(request.body)
        valor     = float(body.get('valor', 0))
        tipo      = body.get('tipo', 'OFERTA')
        nome      = body.get('nome') or 'Contribuinte Anônimo'
        igreja_id = body.get('igreja_id')

        if valor < 1:
            return JsonResponse({'error': 'Valor mínimo: R$ 1,00'}, status=400)

        igreja = (
            Igreja.objects.filter(id=igreja_id, status='ATIVO').first()
            or Igreja.objects.filter(status='ATIVO').first()
        )
        if not igreja:
            return JsonResponse({'error': 'Nenhuma unidade ativa encontrada.'}, status=400)

        MP_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')

        if MP_TOKEN and not MP_TOKEN.startswith('COLE_SEU'):
            # ── MODO REAL: Mercado Pago ──────────────────────
            import mercadopago
            sdk = mercadopago.SDK(MP_TOKEN)

            result   = sdk.payment().create({
                "transaction_amount": valor,
                "description":        f"{_label_tipo(tipo)} - {igreja.nome}",
                "payment_method_id":  "pix",
                "payer": {
                    "email":      "pagador@contribuicao.com",
                    "first_name": nome.split()[0],
                    "last_name":  nome.split()[-1] if ' ' in nome else '',
                },
            })
            response = result["response"]

            if response.get("status") not in ("pending", "approved"):
                return JsonResponse({'error': 'Erro ao criar cobrança no Mercado Pago.'}, status=500)

            pagamento_id = str(response["id"])
            pix_data     = response["point_of_interaction"]["transaction_data"]
            pix_code     = pix_data["qr_code"]
            qr_code_url  = f"data:image/png;base64,{pix_data['qr_code_base64']}"

        else:
            # ── MODO SIMULAÇÃO ────────────────────────────────
            pagamento_id = str(uuid.uuid4())
            pix_code     = (
                f"00020126580014br.gov.bcb.pix0136{uuid.uuid4()}"
                f"5204000053039865802BR5913{igreja.nome[:13]}"
                f"6009SAO PAULO62070503***6304ABCD"
            )
            qr  = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(pix_code)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            qr_code_url = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

        _salvar_movimentacao_pix(pagamento_id, nome, valor, tipo, igreja)

        return JsonResponse({
            'pagamento_id': pagamento_id,
            'qr_code_url':  qr_code_url,
            'pix_code':     pix_code,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────
# 12. API — status do pagamento (polling)
# ─────────────────────────────────────────────────────────────
def api_status_pix(request, pagamento_id):
    MP_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')

    if MP_TOKEN and not MP_TOKEN.startswith('COLE_SEU'):
        import mercadopago
        sdk    = mercadopago.SDK(MP_TOKEN)
        result = sdk.payment().get(pagamento_id)
        status = result["response"].get("status", "pending")
    else:
        # Simulação: mude para 'approved' pra testar o fluxo completo
        status = 'pending'

    return JsonResponse({'status': status})


# ─────────────────────────────────────────────────────────────
# 13. WEBHOOK — Mercado Pago (e n8n pode usar esta mesma rota)
# ─────────────────────────────────────────────────────────────
@csrf_exempt
def webhook_mercadopago(request):
    """
    MP envia POST aqui quando pagamento é confirmado.
    Configure no painel do MP: https://seudominio.com/financeiro/webhook/mp/
    O n8n também pode chamar esta rota para confirmar manualmente.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': True})

    try:
        data = json.loads(request.body)
        if data.get('type') == 'payment' and data.get('action') == 'payment.updated':
            # Futuramente: buscar a movimentação pelo pagamento_id e marcar como confirmada
            pass
    except Exception:
        pass

    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────────────────────
# HELPERS INTERNOS — PIX
# ─────────────────────────────────────────────────────────────
def _salvar_movimentacao_pix(pagamento_id, nome, valor, tipo, igreja):
    """Salva a movimentação no momento da geração do QR."""
    membro = None
    if nome and nome != 'Contribuinte Anônimo':
        membro = Pessoa.objects.filter(
            nome__icontains=nome.split()[0],
            unidade=igreja,
            ativo=True,
        ).first()

    categoria = tipo if tipo in dict(Movimentacao.CATEGORIA_CHOICES) else 'OUTROS'

    Movimentacao.objects.create(
        igreja          = igreja,
        tipo            = 'ENTRADA',
        categoria       = categoria,
        descricao       = f"[PIX:{pagamento_id[:8]}] {_label_tipo(tipo)} - {nome}",
        valor           = valor,
        membro          = membro,
        origem_whatsapp = False,
        # autorizado_por fica None — contribuição pública não tem usuário logado
    )
    # financeiro/views.py (adições/substituições — seções 10 a 13)
# ────────────────────────────────────────────────────────────────────────────
# Cole estas funções substituindo as seções 10–13 do seu views.py atual.
# As demais views (movimentacoes, contas, banco…) permanecem inalteradas.
# ────────────────────────────────────────────────────────────────────────────


# ── Constantes ───────────────────────────────────────────────────────────────
MP_PAYMENTS_URL = 'https://api.mercadopago.com/v1/payments'
MP_TIMEOUT      = 15   # segundos


# ─────────────────────────────────────────────────────────────
# HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────────

def _mp_headers(idempotency_key: str | None = None) -> dict:
    """
    Monta os headers obrigatórios da API do Mercado Pago.
    Lê o token de settings.MERCADO_PAGO_TOKEN.
    """
    headers = {
        'Authorization':  f"Bearer {settings.MERCADO_PAGO_TOKEN}",
        'Content-Type':   'application/json',
        'X-Idempotency-Key': idempotency_key or str(uuid.uuid4()),
    }
    return headers


def _cpf_limpo(cpf: str) -> str:
    """Remove tudo que não for dígito."""
    return re.sub(r'\D', '', cpf or '')


def _label_tipo(tipo: str) -> str:
    return {
        'DIZIMO':      'Dízimo',
        'OFERTA':      'Oferta',
        'MISSIONARIA': 'Oferta Missionária',
        'AVULSA':      'Construção / Infraestrutura',
    }.get(tipo, 'Contribuição')


def _get_igreja_ativa(igreja_id=None) -> Igreja | None:
    qs = Igreja.objects.filter(status='ATIVO')
    if igreja_id:
        return qs.filter(id=igreja_id).first() or qs.first()
    return qs.first()


def _criar_movimentacao(pagamento: PagamentoPix) -> Movimentacao:
    """Cria a Movimentacao financeira após confirmação do PIX."""
    categoria = pagamento.tipo if pagamento.tipo in dict(Movimentacao.CATEGORIA_CHOICES) else 'OUTROS'
    mov = Movimentacao.objects.create(
        igreja    = pagamento.igreja,
        tipo      = 'ENTRADA',
        categoria = categoria,
        descricao = (
            f"[PIX:{pagamento.mp_pagamento_id[:8]}] "
            f"{pagamento.get_tipo_label()} — {pagamento.pagador_nome or 'Anônimo'}"
        ),
        valor          = pagamento.valor,
        origem_whatsapp= False,
        # autorizado_por = None  (contribuição pública)
    )
    return mov


# ─────────────────────────────────────────────────────────────
# 10. PÁGINA PÚBLICA DE PAGAMENTO PIX
# ─────────────────────────────────────────────────────────────

def pagamento_pix(request):
    """Pública — qualquer pessoa pode acessar para contribuir."""
    igreja = _get_igreja_ativa()
    return render(request, 'financeiro/pagamento_pix.html', {'igreja': igreja})


# ─────────────────────────────────────────────────────────────
# 11. API — GERAR COBRANÇA PIX (Mercado Pago — Produção)
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def api_gerar_pix(request):
    """
    POST /financeiro/api/gerar-pix/

    Body JSON esperado:
    {
        "nome":      "João Silva",
        "email":     "joao@email.com",
        "cpf":       "123.456.789-09",   ← com ou sem formatação
        "telefone":  "11999999999",       ← opcional
        "valor":     50.00,
        "tipo":      "DIZIMO",
        "igreja_id": 1                    ← opcional
    }

    Retorna:
    {
        "pagamento_id": "...",
        "pix_code":     "...",
        "qr_code_url":  "data:image/png;base64,..."
    }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    # ── Validações ──────────────────────────────────────────
    valor = float(body.get('valor', 0))
    if valor < 1:
        return JsonResponse({'error': 'Valor mínimo: R$ 1,00.'}, status=400)

    nome  = (body.get('nome') or '').strip() or 'Contribuinte'
    email = (body.get('email') or '').strip() or 'contribuinte@ziongestao.com'
    cpf   = _cpf_limpo(body.get('cpf', ''))
    tipo  = body.get('tipo', 'OFERTA').upper()

    if cpf and len(cpf) != 11:
        return JsonResponse({'error': 'CPF inválido. Informe 11 dígitos.'}, status=400)

    igreja = _get_igreja_ativa(body.get('igreja_id'))
    if not igreja:
        return JsonResponse({'error': 'Nenhuma unidade ativa encontrada.'}, status=400)

    # ── Idempotency key única por requisição ────────────────
    idempotency_key = str(uuid.uuid4())

    # ── Payload Mercado Pago ────────────────────────────────
    nome_parts = nome.split()
    payload = {
        'transaction_amount': round(valor, 2),
        'description':        f"{_label_tipo(tipo)} — {igreja.nome}",
        'payment_method_id':  'pix',
        'payer': {
            'email':      email,
            'first_name': nome_parts[0],
            'last_name':  ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else '',
            **(
                {'identification': {'type': 'CPF', 'number': cpf}}
                if cpf else {}
            ),
        },
        # Expira em 30 minutos
        'date_of_expiration': (
            timezone.now() + timezone.timedelta(minutes=30)
        ).strftime('%Y-%m-%dT%H:%M:%S.000-03:00'),
    }

    # ── Chamada à API do Mercado Pago ───────────────────────
    try:
        resp = requests.post(
            MP_PAYMENTS_URL,
            headers=_mp_headers(idempotency_key),
            json=payload,
            timeout=MP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        logger.error('Timeout na API do Mercado Pago.')
        return JsonResponse({'error': 'Timeout na API de pagamento. Tente novamente.'}, status=504)
    except requests.HTTPError as exc:
        logger.error('MP HTTP Error: %s — %s', exc.response.status_code, exc.response.text)
        return JsonResponse(
            {'error': f"Erro na API de pagamento ({exc.response.status_code})."},
            status=502,
        )
    except requests.RequestException as exc:
        logger.exception('Erro de rede ao chamar Mercado Pago: %s', exc)
        return JsonResponse({'error': 'Falha de rede. Tente novamente.'}, status=502)

    # ── Extrai dados do PIX ─────────────────────────────────
    if data.get('status') not in ('pending', 'approved'):
        logger.error('MP status inesperado: %s', data)
        return JsonResponse({'error': 'Erro ao gerar cobrança PIX.'}, status=500)

    pix_data    = data['point_of_interaction']['transaction_data']
    pix_code    = pix_data['qr_code']
    qr_base64   = pix_data['qr_code_base64']
    mp_id       = str(data['id'])

    # ── Persiste no banco ───────────────────────────────────
    PagamentoPix.objects.create(
        igreja          = igreja,
        mp_pagamento_id = mp_id,
        pix_code        = pix_code,
        pix_qr_base64   = qr_base64,
        tipo            = tipo,
        valor           = Decimal(str(valor)),
        status          = data.get('status', 'pending'),
        pagador_nome     = nome,
        pagador_email    = email,
        pagador_cpf      = cpf,
        pagador_telefone = body.get('telefone', ''),
    )

    return JsonResponse({
        'pagamento_id': mp_id,
        'pix_code':     pix_code,
        'qr_code_url':  f'data:image/png;base64,{qr_base64}',
    })


# ─────────────────────────────────────────────────────────────
# 12. API — STATUS DO PAGAMENTO (polling do front-end)
# ─────────────────────────────────────────────────────────────

def api_status_pix(request, pagamento_id: str):
    """
    GET /financeiro/api/status-pix/<pagamento_id>/

    Consulta primeiro no banco local; só chama o MP se ainda pending.
    Retorna: { "status": "pending" | "approved" | ... }
    """
    pagamento = PagamentoPix.objects.filter(mp_pagamento_id=pagamento_id).first()

    if not pagamento:
        return JsonResponse({'error': 'Pagamento não encontrado.'}, status=404)

    # Já aprovado localmente — retorna sem chamar o MP
    if pagamento.status == 'approved':
        return JsonResponse({'status': 'approved'})

    # Consulta o MP para atualizar
    try:
        resp = requests.get(
            f'{MP_PAYMENTS_URL}/{pagamento_id}',
            headers=_mp_headers(),
            timeout=MP_TIMEOUT,
        )
        resp.raise_for_status()
        status = resp.json().get('status', 'pending')
    except requests.RequestException:
        # Falha silenciosa: devolve o status local atual
        return JsonResponse({'status': pagamento.status})

    # Atualiza local se mudou
    if status != pagamento.status:
        pagamento.status = status
        if status == 'approved':
            pagamento.confirmado_em = timezone.now()
            # Cria a Movimentacao financeira (idempotente via OneToOne)
            if not pagamento.movimentacao_id:
                mov = _criar_movimentacao(pagamento)
                pagamento.movimentacao = mov
        pagamento.save()

    return JsonResponse({'status': status})


# ─────────────────────────────────────────────────────────────
# 13. WEBHOOK — Mercado Pago + n8n
# ─────────────────────────────────────────────────────────────

@csrf_exempt
def webhook_mercadopago(request):
    """
    POST /financeiro/webhook/mp/

    O Mercado Pago envia aqui quando o status muda.
    O n8n (que já recebe o webhook do MP em produção) pode
    chamar esta mesma rota para confirmar manualmente via POST:

        {
            "type":   "payment",
            "action": "payment.updated",
            "data":   { "id": "<mp_pagamento_id>" }
        }

    Configure no painel do MP:
        URL de notificação → https://seudominio.com/financeiro/webhook/mp/
    """
    if request.method != 'POST':
        return JsonResponse({'ok': True})

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': True})  # ignora silenciosamente

    if body.get('type') != 'payment' or body.get('action') != 'payment.updated':
        return JsonResponse({'ok': True})

    mp_id = str(body.get('data', {}).get('id', ''))
    if not mp_id:
        return JsonResponse({'ok': True})

    pagamento = PagamentoPix.objects.filter(mp_pagamento_id=mp_id).first()
    if not pagamento or pagamento.status == 'approved':
        return JsonResponse({'ok': True})   # já processado ou desconhecido

    # Busca status atualizado no MP para confirmar
    try:
        resp = requests.get(
            f'{MP_PAYMENTS_URL}/{mp_id}',
            headers=_mp_headers(),
            timeout=MP_TIMEOUT,
        )
        resp.raise_for_status()
        status = resp.json().get('status', 'pending')
    except requests.RequestException as exc:
        logger.exception('Webhook: erro ao consultar MP para id=%s: %s', mp_id, exc)
        return JsonResponse({'ok': True})

    pagamento.status = status
    if status == 'approved':
        pagamento.confirmado_em = timezone.now()
        if not pagamento.movimentacao_id:
            mov = _criar_movimentacao(pagamento)
            pagamento.movimentacao = mov
        logger.info('PIX aprovado via webhook: %s R$ %s', mp_id, pagamento.valor)

    pagamento.save()
    return JsonResponse({'ok': True})