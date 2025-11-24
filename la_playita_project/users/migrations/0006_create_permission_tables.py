from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_usuario_id'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS usuario_groups (
                  id bigint NOT NULL AUTO_INCREMENT,
                  usuario_id bigint NOT NULL,
                  group_id int NOT NULL,
                  PRIMARY KEY (id),
                  UNIQUE KEY usuario_groups_usuario_id_group_id (usuario_id, group_id),
                  KEY usuario_groups_usuario_id (usuario_id),
                  KEY usuario_groups_group_id (group_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS usuario_groups;"
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS usuario_user_permissions (
                  id bigint NOT NULL AUTO_INCREMENT,
                  usuario_id bigint NOT NULL,
                  permission_id int NOT NULL,
                  PRIMARY KEY (id),
                  UNIQUE KEY usuario_user_permissions_usuario_id_permission_id (usuario_id, permission_id),
                  KEY usuario_user_permissions_usuario_id (usuario_id),
                  KEY usuario_user_permissions_permission_id (permission_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """,
            reverse_sql="DROP TABLE IF EXISTS usuario_user_permissions;"
        ),
    ]
