# Generated migration for adding audit fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('suppliers', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reabastecimientodetalle',
            name='recibido_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reabastecimiento_detalles_recibidos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reabastecimientodetalle',
            name='fecha_recepcion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reabastecimientodetalle',
            name='cantidad_anterior',
            field=models.IntegerField(default=0),
        ),
    ]
