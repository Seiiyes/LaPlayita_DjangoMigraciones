import os
import re

def find_triggers(directory):
    print(f"Buscando triggers en {directory}...")
    for filename in os.listdir(directory):
        if filename.endswith(".sql"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Buscar triggers que mencionen cantidad_disponible
                    if "TRIGGER" in content.upper() and "cantidad_disponible" in content:
                        print(f"\n--- Encontrado en {filename} ---")
                        # Intentar extraer el bloque del trigger (regex aproximado)
                        triggers = re.findall(r"CREATE\s+TRIGGER\s+.*?END\s*;;", content, re.DOTALL | re.IGNORECASE)
                        if not triggers:
                             triggers = re.findall(r"CREATE\s+TRIGGER\s+.*?END;", content, re.DOTALL | re.IGNORECASE)
                        
                        for trigger in triggers:
                            if "cantidad_disponible" in trigger:
                                print(trigger)
                                print("-" * 40)
            except Exception as e:
                print(f"Error leyendo {filename}: {e}")

if __name__ == "__main__":
    find_triggers(r"c:\Users\Michael\Desktop\PLAYITA PYTHON\LaPlayita_DjangoMigraciones\database")
