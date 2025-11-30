# Generated migration for adding audit table and lote field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suppliers', '0003_add_audit_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='reabastecimientodetalle',
            name='numero_lote',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS auditoria_reabastecimiento (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                reabastecimiento_id BIGINT NOT NULL,
                usuario_id BIGINT,
                accion VARCHAR(20) NOT NULL,
                cantidad_anterior INT,
                cantidad_nueva INT,
                descripcion LONGTEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_reabastecimiento (reabastecimiento_id),
                INDEX idx_fecha (fecha)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS auditoria_reabastecimiento;"
        ),
    ]
