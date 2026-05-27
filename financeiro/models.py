# financeiro/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone




class Movimentacao(models.Model):
    TIPO_CHOICES = [('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')]
    CATEGORIA_CHOICES = [
        ('DIZIMO',      'Dízimo'),
        ('OFERTA',      'Oferta'),
        ('MISSIONARIA', 'Oferta Missionária'),
        ('AVULSA',      'Oferta Avulsa'),
        ('OUTROS',      'Outros'),
    ]

    # --- Vínculos principais ---
    igreja          = models.ForeignKey('igrejas.Igreja',   on_delete=models.CASCADE,  related_name='movimentacoes')
    membro          = models.ForeignKey('pessoas.Pessoa',   on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentacoes', verbose_name='Membro / Doador')
    culto_vinculado = models.ForeignKey('cultos.Culto',     on_delete=models.SET_NULL, null=True, blank=True)

    # --- Quem registrou/autorizou no sistema ---
    autorizado_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes_autorizadas',
        verbose_name='Autorizado por'
    )

    tipo       = models.CharField(max_length=10,  choices=TIPO_CHOICES)
    categoria  = models.CharField(max_length=20,  choices=CATEGORIA_CHOICES)
    descricao  = models.CharField(max_length=255)
    valor      = models.DecimalField(max_digits=10, decimal_places=2)
    data       = models.DateField(default=timezone.now)

    origem_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_tipo_display()} | {self.get_categoria_display()} | R$ {self.valor}"


class Obrigacao(models.Model):
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('pago',      'Pago'),
        ('atrasado',  'Atrasado'),
    ]
    RECORRENCIA_CHOICES = [
        ('unica',   'Única'),
        ('mensal',  'Mensal'),
        ('anual',   'Anual'),
    ]
    TIPO_CHOICES = [('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')]

    igreja    = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE)
    nome      = models.CharField(max_length=100)
    empresa   = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.CharField(max_length=50, default='Outros')

    valor      = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()

    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    recorrencia = models.CharField(max_length=20, choices=RECORRENCIA_CHOICES, default='mensal')
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES, default='SAIDA')

    observacao   = models.TextField(blank=True, null=True)
    comprovante  = models.FileField(upload_to='comprovantes/', blank=True, null=True)

    # --- Quem autorizou o pagamento ---
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='obrigacoes_autorizadas',
        verbose_name='Autorizado por'
    )

    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


class Manutencao(models.Model):
    STATUS_CHOICES = [
        ('URGENTE',    'Urgente'),
        ('NECESSARIO', 'Necessário'),
        ('MELHORIA',   'Melhoria'),
    ]

    igreja             = models.ForeignKey('igrejas.Igreja', on_delete=models.CASCADE)
    item               = models.CharField(max_length=255)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NECESSARIO')
    observacao         = models.TextField()
    orcamento_aprovado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.item} ({self.get_status_display()})"


class DadosBancarios(models.Model):
    igreja     = models.OneToOneField('igrejas.Igreja', on_delete=models.CASCADE)
    banco      = models.CharField(max_length=100)
    agencia    = models.CharField(max_length=20)
    conta      = models.CharField(max_length=50)
    chave_pix  = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.banco} — {self.igreja.nome}"

        # financeiro/models.py
# ─── Adicione esta classe ao seu models.py existente ───────────────────────



class PagamentoPix(models.Model):
    """
    Armazena cada cobrança PIX gerada via Mercado Pago.
    Conecta com o n8n através do `mp_pagamento_id`.
    """

    STATUS_CHOICES = [
        ('pending',     'Aguardando pagamento'),
        ('approved',    'Aprovado'),
        ('cancelled',   'Cancelado'),
        ('rejected',    'Rejeitado'),
        ('refunded',    'Estornado'),
    ]

    TIPO_CHOICES = [
        ('DIZIMO',      'Dízimo'),
        ('OFERTA',      'Oferta'),
        ('MISSIONARIA', 'Oferta Missionária'),
        ('AVULSA',      'Construção / Infraestrutura'),
    ]

    # --- Vínculo com a Igreja ---
    igreja = models.ForeignKey(
        'igrejas.Igreja',
        on_delete=models.CASCADE,
        related_name='pagamentos_pix',
    )

    # --- Dados do MP (preenchidos na geração) ---
    mp_pagamento_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='ID Mercado Pago',
        help_text='Chave que o n8n usa para identificar o pagamento.',
    )
    pix_code = models.TextField(
        verbose_name='Código Copia e Cola',
    )
    pix_qr_base64 = models.TextField(
        verbose_name='QR Code (base64)',
    )

    # --- Dados da transação ---
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OFERTA')
    valor       = models.DecimalField(max_digits=10, decimal_places=2)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # --- Dados do pagador (capturados no formulário) ---
    pagador_nome      = models.CharField(max_length=150, blank=True, default='')
    pagador_email     = models.EmailField(blank=True, default='')
    pagador_cpf       = models.CharField(max_length=11, blank=True, default='', verbose_name='CPF (só números)')
    pagador_telefone  = models.CharField(max_length=20, blank=True, default='')

    # --- Controle ---
    criado_em     = models.DateTimeField(default=timezone.now)
    confirmado_em = models.DateTimeField(null=True, blank=True)

    # --- Movimentação gerada após confirmação (evita duplicação) ---
    movimentacao = models.OneToOneField(
        'financeiro.Movimentacao',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pagamento_pix_origem',
    )

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Pagamento PIX'
        verbose_name_plural = 'Pagamentos PIX'

    def __str__(self):
        return f"[{self.mp_pagamento_id}] R$ {self.valor} — {self.get_status_display()}"

    def get_tipo_label(self):
        return dict(self.TIPO_CHOICES).get(self.tipo, 'Contribuição')