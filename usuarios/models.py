from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioSistemaManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O usuário precisa de um E-mail válido.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # Criptografa a senha
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'ATIVO')
        extra_fields.setdefault('perfil', 'presidente')
        return self.create_user(email, password, **extra_fields)

class UsuarioSistema(AbstractBaseUser, PermissionsMixin):
    PERFIL_CHOICES = [
        ('presidente', 'Pastor Presidente / Diretoria'),
        ('pastor_unidade', 'Pastor de Unidade'),
        ('tesoureiro', 'Tesoureiro (Finanças da Unidade)'),
        ('lider_departamento', 'Líder de Departamento'),
        ('midia', 'Mídia (Cultos Locais)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente (Aguardando Aprovação)'),
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo / Bloqueado'),
    ]

    email = models.EmailField(unique=True, verbose_name="E-mail de Acesso")
    nome_solicitante = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    # Chaves Estrangeiras (Pulo do Gato)
    igreja = models.ForeignKey('igrejas.Igreja', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    pessoa = models.ForeignKey('pessoas.Pessoa', on_delete=models.SET_NULL, null=True, blank=True, related_name='conta_acesso')

    perfil = models.CharField(max_length=30, choices=PERFIL_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')

    is_active = models.BooleanField(default=True) 
    is_staff = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
   
    # BLINDAGEM CONTRA O ERRO E304 (Conflito de Permissões)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="usuario_sistema_groups" # Nome exclusivo!
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="usuario_sistema_permissions" # Nome exclusivo!
    )
    objects = UsuarioSistemaManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_solicitante']

    class Meta:
        db_table = 'usuarios_sistema'
        verbose_name = 'Usuário do Sistema'
        verbose_name_plural = 'Usuários do Sistema'

    def __str__(self):
        return f"{self.nome_solicitante} ({self.email})"