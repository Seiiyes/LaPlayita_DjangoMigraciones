# Generated manually to fix database inconsistency

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_usuario_is_staff'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE usuario ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT 0",
            reverse_sql="ALTER TABLE usuario DROP COLUMN is_superuser",
        )
    ]
