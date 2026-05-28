# financeiro/views.py  —  VERSÃO DEFINITIVA (limpa, sem duplicatas)
# ─────────────────────────────────────────────────────────────────────────────
from thefuzz import fuzz
import json
import re
import uuid
import logging
from decimal import Decimal

import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from igrejas.models import Igreja
from pessoas.models import Pessoa
from usuarios.permissoes import PERFIS_GERENCIAIS, perfil_requerido

from .models import DadosBancarios, Manutencao, Movimentacao, Obrigacao, PagamentoPix

logger = logging.getLogger(__name__)

# ── Constantes MP ─────────────────────────────────────────────────────────────
MP_PAYMENTS_URL = 'https://api.mercadopago.com/v1/payments'
MP_TIMEOUT      = 15  # segundos


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS GERAIS
# ═════════════════════════════════════════════════════════════════════════════

def _igreja(request):
    return request.user.igreja


def _saldo_gaveta(igreja, categoria):
    e = Movimentacao.objects.filter(
        igreja=igreja, tipo='ENTRADA', categoria=categoria,
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    s = Movimentacao.objects.filter(
        igreja=igreja, tipo='SAIDA', categoria=categoria,
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    return e - s


def _label_tipo(tipo: str) -> str:
    return {
        'DIZIMO':      'Dízimo',
        'OFERTA':      'Oferta',
        'MISSIONARIA': 'Oferta Missionária',
        'AVULSA':      'Construção / Infraestrutura',
    }.get(tipo, 'Contribuição')


# ── Helpers PIX ───────────────────────────────────────────────────────────────

def _mp_headers(idempotency_key: str | None = None) -> dict:
    return {
        'Authorization':     f"Bearer {settings.MERCADO_PAGO_TOKEN}",
        'Content-Type':      'application/json',
        'X-Idempotency-Key': idempotency_key or str(uuid.uuid4()),
    }


def _cpf_limpo(cpf: str) -> str:
    return re.sub(r'\D', '', cpf or '')


def _get_igreja_ativa(igreja_id=None) -> Igreja | None:
    qs = Igreja.objects.filter(status='ATIVO')
    if igreja_id:
        return qs.filter(id=igreja_id).first() or qs.first()
    return qs.first()


def _criar_movimentacao(pagamento: PagamentoPix) -> Movimentacao:
    """Cria Movimentacao financeira após confirmação. Chamado apenas 1x (via OneToOne)."""
    categoria = (
        pagamento.tipo
        if pagamento.tipo in dict(Movimentacao.CATEGORIA_CHOICES)
        else 'OUTROS'
    )
    return Movimentacao.objects.create(
        igreja          = pagamento.igreja,
        tipo            = 'ENTRADA',
        categoria       = categoria,
        descricao       = (
            f"[PIX:{pagamento.mp_pagamento_id[:8]}] "
            f"{_label_tipo(pagamento.tipo)} — {pagamento.pagador_nome or 'Anônimo'}"
        ),
        valor           = pagamento.valor,
        origem_whatsapp = False,
        # autorizado_por = None (contribuição pública)
    )


# ═════════════════════════════════════════════════════════════════════════════
# 0. DASHBOARD FINANCEIRO
# ═════════════════════════════════════════════════════════════════════════════

@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
@never_cache
def financeiro(request):
    igreja = _igreja(request)
    hoje = timezone.now().date()
    primeiro_dia_mes = hoje.replace(day=1)

    total_entradas = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA').aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas   = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0
    entradas_mes   = Movimentacao.objects.filter(igreja=igreja, tipo='ENTRADA', data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0
    saidas_mes     = Movimentacao.objects.filter(igreja=igreja, tipo='SAIDA',   data__gte=primeiro_dia_mes).aggregate(Sum('valor'))['valor__sum'] or 0

    return render(request, 'financeiro/financeiro.html', {
        'igreja':                igreja,
        'saldo_atual':           total_entradas - total_saidas,
        'entradas_mes':          entradas_mes,
        'saidas_mes':            saidas_mes,
        'ultimas_movimentacoes': Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data')[:10],
        'manutencoes_urgentes':  Manutencao.objects.filter(igreja=igreja, status='URGENTE'),
    })


# ═════════════════════════════════════════════════════════════════════════════
# 1. FLUXO DE REGISTROS
# ═════════════════════════════════════════════════════════════════════════════

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

    return render(request, 'financeiro/movimentacoes.html', {
        'movimentacoes': Movimentacao.objects.filter(igreja=igreja).select_related('membro', 'autorizado_por').order_by('-data'),
        'membros':       Pessoa.objects.filter(unidade=igreja, ativo=True).order_by('nome'),
        'igreja':        igreja,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 2. CENTRAL DE OBRIGAÇÕES
# ═════════════════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════════════════
# 3. DELETAR CONTA
# ═════════════════════════════════════════════════════════════════════════════

@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def deletar_conta(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    if request.method == 'POST':
        conta.delete()
    return redirect('financeiro:contas')


# ═════════════════════════════════════════════════════════════════════════════
# 4. PAGAR CONTA
# ═════════════════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════════════════
# 5. COCKPIT BANCÁRIO
# ═════════════════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════════════════
# 6. NOVA CONTA BANCÁRIA
# ═════════════════════════════════════════════════════════════════════════════

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
            },
        )
    return redirect('financeiro:banco')


# ═════════════════════════════════════════════════════════════════════════════
# 7. DETALHE DE CONTA
# ═════════════════════════════════════════════════════════════════════════════

@login_required
@perfil_requerido(*PERFIS_GERENCIAIS)
def conta_detalhes(request, conta_id):
    conta = get_object_or_404(Obrigacao, id=conta_id, igreja=_igreja(request))
    return render(request, 'financeiro/conta_detalhes.html', {'conta': conta})


# ═════════════════════════════════════════════════════════════════════════════
# 8. MANUTENÇÃO
# ═════════════════════════════════════════════════════════════════════════════

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

    return render(request, 'financeiro/manutencao.html', {
        'manutencao': Manutencao.objects.filter(igreja=igreja).order_by('-status'),
    })


# ═════════════════════════════════════════════════════════════════════════════
# 9. API — autocomplete de membros
# ═════════════════════════════════════════════════════════════════════════════

@login_required
def api_buscar_membro(request):
    termo  = request.GET.get('q', '').strip()
    igreja = _igreja(request)
    if len(termo) < 2:
        return JsonResponse([], safe=False)
    pessoas = Pessoa.objects.filter(nome__icontains=termo, unidade=igreja, ativo=True)[:10]
    return JsonResponse(
        [{'id': p.id, 'nome': p.nome, 'tipo': p.get_tipo_display(),
          'unidade': p.unidade.nome if p.unidade else ''} for p in pessoas],
        safe=False,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 10. PÁGINA PÚBLICA DE PAGAMENTO PIX
# ═════════════════════════════════════════════════════════════════════════════

def pagamento_pix(request):
    """Pública — qualquer pessoa pode acessar para contribuir."""
    igreja = _get_igreja_ativa()
    return render(request, 'financeiro/pagamento_pix.html', {'igreja': igreja})


# ═════════════════════════════════════════════════════════════════════════════
# 11. API — GERAR COBRANÇA PIX
# ═════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def api_gerar_pix(request):
    """
    POST /financeiro/api/gerar-pix/

    Body JSON:
        nome, email, cpf (opcional), telefone (opcional),
        valor, tipo, igreja_id (opcional)

    Retorna:
        pagamento_id, pix_code, qr_code_url
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    # ── Leitura e validação ──────────────────────────────────
    valor = float(body.get('valor', 0))
    if valor < 1:
        return JsonResponse({'error': 'Valor mínimo: R$ 1,00.'}, status=400)

    nome     = (body.get('nome') or '').strip() or 'Contribuinte'
    email    = (body.get('email') or '').strip() or 'contribuinte@ziongestao.com'
    cpf      = _cpf_limpo(body.get('cpf', ''))
    tipo     = body.get('tipo', 'OFERTA').upper()
    telefone = (body.get('telefone') or '').strip()

    if cpf and len(cpf) != 11:
        return JsonResponse({'error': 'CPF inválido. Informe 11 dígitos.'}, status=400)

    igreja = _get_igreja_ativa(body.get('igreja_id'))
    if not igreja:
        return JsonResponse({'error': 'Nenhuma unidade ativa encontrada.'}, status=400)

    # ── Idempotency key ──────────────────────────────────────
    idempotency_key = str(uuid.uuid4())

    # ── Payload enviado ao Mercado Pago ─────────────────────
    # FIX PRINCIPAL:
    #   1. `payer.first_name` / `payer.last_name`  ← nome real do contribuinte
    #   2. `external_reference`                     ← nome aparece no extrato MP e no n8n
    #   3. `description`                            ← tipo + igreja (campo público no QR)
    nome_parts = nome.split()
    payload = {
        'transaction_amount': round(valor, 2),
        'description':        f"{_label_tipo(tipo)} — {igreja.nome}",
        'payment_method_id':  'pix',

        # ↓ external_reference: aparece no dashboard do MP e chega no webhook ao n8n
        'external_reference': f"{nome} | {_label_tipo(tipo)} | R$ {valor:.2f}",

        'payer': {
            'email':      email,
            'first_name': nome_parts[0],
            'last_name':  ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else '',

            # CPF enviado apenas se preenchido (obrigatório para nota fiscal, opcional para PIX)
            **(
                {'identification': {'type': 'CPF', 'number': cpf}}
                if cpf else {}
            ),
        },

        # PIX expira em 30 minutos
        'date_of_expiration': (
            timezone.now() + timezone.timedelta(minutes=30)
        ).strftime('%Y-%m-%dT%H:%M:%S.000-03:00'),

        # Metadados extras — visíveis no n8n via webhook
        'metadata': {
            'tipo_contribuicao': tipo,
            'nome_contribuinte': nome,
            'telefone':          telefone,
            'igreja_id':         str(igreja.id),
            'igreja_nome':       igreja.nome,
        },
    }

    # ── Chamada ao Mercado Pago ──────────────────────────────
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
        logger.error('Timeout ao chamar Mercado Pago.')
        return JsonResponse({'error': 'Timeout na API de pagamento. Tente novamente.'}, status=504)

    except requests.HTTPError as exc:
        logger.error('MP HTTPError %s: %s', exc.response.status_code, exc.response.text)
        return JsonResponse(
            {'error': f"Erro na API de pagamento ({exc.response.status_code})."},
            status=502,
        )

    except requests.RequestException as exc:
        logger.exception('Erro de rede MP: %s', exc)
        return JsonResponse({'error': 'Falha de rede. Tente novamente.'}, status=502)

    # ── Valida resposta ──────────────────────────────────────
    if data.get('status') not in ('pending', 'approved'):
        logger.error('MP status inesperado: %s', data)
        return JsonResponse({'error': 'Erro ao gerar cobrança PIX.'}, status=500)

    pix_data  = data['point_of_interaction']['transaction_data']
    pix_code  = pix_data['qr_code']
    qr_base64 = pix_data['qr_code_base64']
    mp_id     = str(data['id'])

    # ── Persiste PagamentoPix ────────────────────────────────
    PagamentoPix.objects.create(
        igreja           = igreja,
        mp_pagamento_id  = mp_id,
        pix_code         = pix_code,
        pix_qr_base64    = qr_base64,
        tipo             = tipo,
        valor            = Decimal(str(valor)),
        status           = data.get('status', 'pending'),
        pagador_nome     = nome,
        pagador_email    = email,
        pagador_cpf      = cpf,
        pagador_telefone = telefone,
    )

    logger.info('PIX gerado: id=%s nome=%s valor=%.2f tipo=%s', mp_id, nome, valor, tipo)

    return JsonResponse({
        'pagamento_id': mp_id,
        'pix_code':     pix_code,
        'qr_code_url':  f'data:image/png;base64,{qr_base64}',
    })


# ═════════════════════════════════════════════════════════════════════════════
# 12. API — STATUS DO PAGAMENTO (polling do front-end)
# ═════════════════════════════════════════════════════════════════════════════

def api_status_pix(request, pagamento_id: str):
    """
    GET /financeiro/api/status-pix/<pagamento_id>/

    Consulta banco local primeiro. Só vai ao MP se ainda pending.
    """
    pagamento = PagamentoPix.objects.filter(mp_pagamento_id=pagamento_id).first()
    if not pagamento:
        return JsonResponse({'error': 'Pagamento não encontrado.'}, status=404)

    # Já confirmado — responde sem chamar o MP
    if pagamento.status == 'approved':
        return JsonResponse({'status': 'approved'})

    # Consulta status atual no MP
    try:
        resp = requests.get(
            f'{MP_PAYMENTS_URL}/{pagamento_id}',
            headers=_mp_headers(),
            timeout=MP_TIMEOUT,
        )
        resp.raise_for_status()
        status = resp.json().get('status', 'pending')
    except requests.RequestException:
        return JsonResponse({'status': pagamento.status})  # fallback local

    # Atualiza registro se mudou
    if status != pagamento.status:
        pagamento.status = status
        if status == 'approved':
            pagamento.confirmado_em = timezone.now()
            if not pagamento.movimentacao_id:
                pagamento.movimentacao = _criar_movimentacao(pagamento)
        pagamento.save()

    return JsonResponse({'status': status})


# ═════════════════════════════════════════════════════════════════════════════
# 13. WEBHOOK — Mercado Pago + n8n
# ═════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def webhook_mercadopago(request):
    """
    POST /financeiro/webhook/mp/

    Recebe notificações do Mercado Pago quando um pagamento muda de status.
    O n8n pode chamar esta mesma rota para acionar confirmação manual:

        {
            "type":   "payment",
            "action": "payment.updated",
            "data":   { "id": "<mp_pagamento_id>" }
        }

    Configure no painel MP → Webhooks → URL de notificação:
        https://seudominio.com/financeiro/webhook/mp/
    """
    if request.method != 'POST':
        return JsonResponse({'ok': True})

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': True})

    if body.get('type') != 'payment' or body.get('action') != 'payment.updated':
        return JsonResponse({'ok': True})

    mp_id = str(body.get('data', {}).get('id', ''))
    if not mp_id:
        return JsonResponse({'ok': True})

    pagamento = PagamentoPix.objects.filter(mp_pagamento_id=mp_id).first()
    if not pagamento or pagamento.status == 'approved':
        return JsonResponse({'ok': True})  # idempotente

    # Confirma status no MP
    try:
        resp = requests.get(
            f'{MP_PAYMENTS_URL}/{mp_id}',
            headers=_mp_headers(),
            timeout=MP_TIMEOUT,
        )
        resp.raise_for_status()
        status = resp.json().get('status', 'pending')
    except requests.RequestException as exc:
        logger.exception('Webhook: falha ao consultar MP id=%s: %s', mp_id, exc)
        return JsonResponse({'ok': True})

    pagamento.status = status
    if status == 'approved':
        pagamento.confirmado_em = timezone.now()
        if not pagamento.movimentacao_id:
            pagamento.movimentacao = _criar_movimentacao(pagamento)
        logger.info('PIX aprovado via webhook: id=%s R$=%s nome=%s',
                    mp_id, pagamento.valor, pagamento.pagador_nome)

    pagamento.save()
    return JsonResponse({'ok': True})

# ═══════════════════════════════════════════════════════════════════════════
# 14. WEBHOOK N8N — Processar PIX público com match inteligente de membros
# ═══════════════════════════════════════════════════════════════════════════

# Adicione este import junto aos demais no topo do arquivo:
# from thefuzz import fuzz

from thefuzz import fuzz

FUZZY_THRESHOLD = 80  # score mínimo para considerar match de nome


@csrf_exempt
@require_POST
def processar_pix_publico(request):
    """
    POST /financeiro/webhook/n8n/

    Recebe do n8n os dados de um PIX confirmado e:
      1. Evita duplicata pelo id_pagamento
      2. Tenta casar o nome com um Pessoa ativo via fuzzy matching
      3. Registra Movimentacao vinculada ao membro (se achado) ou anônima
      4. Marca o PagamentoPix como aprovado (se existir no banco)

    Body JSON esperado:
        { "nome": "Tiago Aldemino", "valor": 2.00,
          "tipo": "OFERTA", "id_pagamento": "160507761023" }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    # ── Campos obrigatórios ──────────────────────────────────────────────
    id_pagamento = str(body.get('id_pagamento', '')).strip()
    nome_raw     = str(body.get('nome', '') or 'Anônimo').strip()
    tipo         = str(body.get('tipo', 'OFERTA')).upper()
    try:
        valor = Decimal(str(body.get('valor', 0)))
    except Exception:
        return JsonResponse({'error': 'Valor inválido.'}, status=400)

    if not id_pagamento:
        return JsonResponse({'error': 'id_pagamento é obrigatório.'}, status=400)
    if valor < Decimal('0.01'):
        return JsonResponse({'error': 'Valor deve ser maior que zero.'}, status=400)

    # ── Trava anti-duplicata ─────────────────────────────────────────────
    if Movimentacao.objects.filter(descricao__contains=f'[PIX:{id_pagamento[:8]}]').exists():
        logger.info('processar_pix_publico: id_pagamento %s já processado, ignorando.', id_pagamento)
        return JsonResponse({'ok': True, 'status': 'duplicate'})

    # ── Igreja ───────────────────────────────────────────────────────────
    igreja = _get_igreja_ativa()
    if not igreja:
        return JsonResponse({'error': 'Nenhuma unidade ativa.'}, status=400)

    # ── Fuzzy match contra Pessoa ─────────────────────────────────────────
    membro_encontrado = None
    melhor_score      = 0

    candidatos = Pessoa.objects.filter(unidade=igreja, ativo=True).only('id', 'nome')
    for candidato in candidatos:
        score = fuzz.token_set_ratio(nome_raw.lower(), candidato.nome.lower())
        if score > melhor_score:
            melhor_score      = score
            membro_encontrado = candidato

    membro_match = membro_encontrado if melhor_score >= FUZZY_THRESHOLD else None

    logger.info(
        'processar_pix_publico: nome="%s" melhor_match="%s" score=%d match=%s',
        nome_raw,
        membro_encontrado.nome if membro_encontrado else '—',
        melhor_score,
        bool(membro_match),
    )

    # ── Categoria válida ─────────────────────────────────────────────────
    categorias_validas = dict(Movimentacao.CATEGORIA_CHOICES).keys()
    categoria = tipo if tipo in categorias_validas else 'OUTROS'

    # ── Descrição diferencia membro identificado de contribuição avulsa ──
    if membro_match:
        descricao = (
            f"[PIX:{id_pagamento[:8]}] "
            f"{_label_tipo(tipo)} — {membro_match.nome} "
            f"(match: {melhor_score}%)"
        )
    else:
        # Score baixo ou nome anônimo → salva o nome digitado como anotação
        descricao = (
            f"[PIX:{id_pagamento[:8]}] "
            f"{_label_tipo(tipo)} — visitante/anônimo "
            f"[nome digitado: {nome_raw}]"
        )

    # ── Cria Movimentacao ────────────────────────────────────────────────
    movimentacao = Movimentacao.objects.create(
        igreja         = igreja,
        tipo           = 'ENTRADA',
        categoria      = categoria,
        descricao      = descricao,
        valor          = valor,
        data           = timezone.now().date(),
        membro         = membro_match,   # None se não identificado
        origem_whatsapp= False,
        # autorizado_por = None  (contribuição pública, sem usuário logado)
    )

    # ── Sincroniza PagamentoPix se existir ───────────────────────────────
    pagamento = PagamentoPix.objects.filter(mp_pagamento_id=id_pagamento).first()
    if pagamento and pagamento.status != 'approved':
        pagamento.status        = 'approved'
        pagamento.confirmado_em = timezone.now()
        if not pagamento.movimentacao_id:
            pagamento.movimentacao = movimentacao
        pagamento.save()

    return JsonResponse({
        'ok':           True,
        'status':       'created',
        'movimentacao': movimentacao.id,
        'membro_id':    membro_match.id   if membro_match else None,
        'membro_nome':  membro_match.nome if membro_match else None,
        'score':        melhor_score,
    })