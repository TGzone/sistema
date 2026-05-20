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