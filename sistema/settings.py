import os
from pathlib import Path
from dotenv import load_dotenv

# 1. CARREGAR VARIÁVEIS DE AMBIENTE (O seu "cofre" .env)
load_dotenv()

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. SEGURANÇA
# Tenta pegar a chave do .env, se não achar, usa a temporária (mantenha a temporária apenas em dev)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-chave-temporaria')

DEBUG = True

ALLOWED_HOSTS = []

# 3. APPS DO DJANGO
INSTALLED_APPS = [ 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Seus apps do projeto Sistema PDB
    'usuarios',
    'pessoas',
    'financeiro',
    'igrejas',
    'relatorios',
    'pastoral',
    'dashboard',
    'cultos',
    'integracoes',
]

# 4. MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema.urls'

# 5. TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema.wsgi.application'

# 6. BANCO DE DADOS (Configurado para MySQL via .env)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# 7. VALIDAÇÃO DE SENHAS
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

# 8. INTERNACIONALIZAÇÃO (PT-BR)
LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True

# 9. ARQUIVOS ESTÁTICOS (CSS, JS, IMAGENS)
#STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

# 10. MEDIA (UPLOADS DE ARQUIVOS)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Tipo padrão de ID para o banco
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'