from django.db import models
from igrejas.models import Igreja  # Importando o modelo de Igreja

class Endereco(models.Model):
    rua = models.CharField(max_length=120)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=80)
    cidade = models.CharField(max_length=80)
    estado = models.CharField(max_length=50)
    cep = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.rua}, {self.numero}"

class Pessoa(models.Model):
    SEXO = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    TIPO = [
        ("visitante", "Visitante"), 
        ("membro", "Membro"),
        ("congregado", "Congregado"), 
        ("kids", "Kids"),
        ("obreiro", "Obreiro"), # Adicionado corretamente como tupla
        ("pastor", "Pastor"), 
        ("presbitero", "Presbítero"),
        ("evangelista", "Evangelista"), 
        ("missionario", "Missionário"),
    ]

    ESTADO_CIVIL = [
        ("solteiro", "Solteiro"),
        ("casado", "Casado"),
        ("divorciado", "Divorciado"),
        ("viuvo", "Viúvo"),
    ]

    STATUS = [
        ("novo", "Novo convertido"),
        ("discipulado", "Em discipulado"),
        ("recorrente", "Visitante recorrente"),
        ("desigrejado", "Desigrejado"),
    ]

    # --- CAMPOS PRINCIPAIS ---
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO)
    
    # --- VÍNCULO COM A UNIDADE (A CONEXÃO) ---
    unidade = models.ForeignKey(
        Igreja, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='membros'
    )
    
    igreja_origem = models.CharField(max_length=120, blank=True) # Mantido para histórico
    ministerio = models.CharField(max_length=120, blank=True)
    
    # --- STATUS E CONTROLE ---
    membro_desta_igreja = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True) 
    
    status_acompanhamento = models.CharField(
        max_length=20,
        choices=STATUS,
        blank=True
    )
    
    estado_civil = models.CharField(
        max_length=20,
        choices=ESTADO_CIVIL,
        blank=True
    )

    # --- RELACIONAMENTOS ---
    responsavel = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    endereco = models.ForeignKey(
        Endereco,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # --- EXTRAS ---
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome