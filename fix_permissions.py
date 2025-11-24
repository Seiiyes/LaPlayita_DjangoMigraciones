import pymysql

conn = pymysql.connect(
    host='localhost',
    port=3309,
    user='root',
    password='12345678',
    database='laplayita'
)

cursor = conn.cursor()

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario_groups (
          id bigint NOT NULL AUTO_INCREMENT,
          usuario_id bigint NOT NULL,
          group_id int NOT NULL,
          PRIMARY KEY (id),
          UNIQUE KEY usuario_groups_unique (usuario_id,group_id)
        ) ENGINE=InnoDB
    """)
    print("✅ Tabla usuario_groups creada")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario_user_permissions (
          id bigint NOT NULL AUTO_INCREMENT,
          usuario_id bigint NOT NULL,
          permission_id int NOT NULL,
          PRIMARY KEY (id),
          UNIQUE KEY usuario_permissions_unique (usuario_id,permission_id)
        ) ENGINE=InnoDB
    """)
    print("✅ Tabla usuario_user_permissions creada")
    
    conn.commit()
    print("\n✅ Tablas creadas exitosamente. Ahora puede acceder al admin.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
