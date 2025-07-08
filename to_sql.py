import os
import glob
import pandas as pd
# -------------- Connexió a la BBDD Postgresql -------------- #
from connexio_bbdd import PostgresConn
# -------------- Importar funcions externes al script actual -------------- #
from maps_columnes import table_mappings
from csv_func import main as generate_dataframes

client = 'AUTOLIV'
ref_project = 665220400

""" Codi per importar dades dels fitxers CSV genereta a la BBDD PostgreSQL."""

csv_dataframes_folder = r'C:\Github\PythonTecnica_SOME'

db_params = {
    'host': '172.26.5.159',
    'port': '5433',
    'database': 'documentacio_tecnica',
    'user': 'administrador',
    'password': 'Some2025.!$%'
}
db = PostgresConn(**db_params)

# Ruta del CSV (datasheet) generat
csv_datasheet = os.path.join(csv_dataframes_folder, fr"dades_escandall {client} {ref_project}.csv") 

def importar_dataframe_a_sql(df, tab_name, cols, db):
    """Importa un DataFrame a una taula SQL, fila a fila, gestionant errors de clau duplicada."""
    conn = db.connect()
    success = 0
    errors = 0
    valid_cols = [col for col in cols if col in df.columns] # Filtra només les columnes que existeixen al DataFrame
    for _, row in df.iterrows():
        placeholders = ', '.join(['%s'] * len(valid_cols))
        insert_query = f"""INSERT INTO {tab_name} ({', '.join(valid_cols)}) VALUES ({placeholders});"""
        row_values = [row[col] if pd.notnull(row[col]) else None for col in valid_cols]
        try:
            with conn.cursor() as cursor:
                cursor.execute(insert_query, row_values)
            conn.commit()
            success += 1
        except Exception as e:
            conn.rollback()
            print(f"Fila no inserida a {tab_name}: {e}")
            errors += 1
    print(f"{success} files importades correctament a {tab_name}. {errors} errors.")


def main():
                                                    # Obté tots els DataFrames generats pel procés principal
    dfs = generate_dataframes(return_all = True)    # La funció retorna un diccionari amb tots els DataFrames

    # Per cada taula definida al mapping, importa el DataFrame corresponent
    for table_name, columns in table_mappings.items():
        df = dfs.get(table_name)                                    # type: ignore # Obté el DataFrame corresponent a la taula
        if df is not None and not df.empty:                         # Comprova que el DataFrame existeix i no està buit
            df = df[[col for col in columns if col in df.columns]]  # Reordena les columnes del DataFrame segons l'ordre de la taula SQL
            importar_dataframe_a_sql(df, table_name, columns, db)   # Importa el DataFrame a la taula SQL
            
        else:
            print(f"DataFrame per {table_name} no trobat o està buit.")

    # Esborra tots els fitxers .csv del directori un cop utilitzats
    csv_files = glob.glob(os.path.join(csv_dataframes_folder, "*.csv"))
    for file in csv_files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"No s'ha pogut esborrar {file}: {e}")

if __name__ == "__main__":
    main()  # Executa la funció principal si el fitxer s'executa directament
