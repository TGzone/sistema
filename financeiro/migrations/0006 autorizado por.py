# financeiro/migrations/0006_autorizado_por.py

import django.db.models.deletion
from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0005_obrigacao_comprovante'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='movimentacao',
            name='autorizado_por',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                related_name='movimentacoes_autorizadas',
                verbose_name='Autorizado por'
            ),
        ),
        migrations.AddField(
            model_name='obrigacao',
            name='autorizado_por',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                related_name='obrigacoes_autorizadas',
                verbose_name='Autorizado por'
            ),
        ),
    ]