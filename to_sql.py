import os
import glob
import psycopg2
import pandas as pd
from csv_func import main as generate_dataframes
from maps_columnes import table_mappings
from kop_csv import client, ref_project

""" Codi per importar dades dels fitxers CSV genereta a la BBDD PostgreSQL.
"""

csv_dataframes_folder = r'C:\Github\PythonTecnica_SOME'

db_params = {
    'host': '172.26.5.159',
    'database': 'documentacio_tecnica',
    'user': 'administrador',
    'password': 'Some2025.!$%'
}

csv_datasheet = os.path.join(csv_dataframes_folder, fr"dades_escandall {client} {ref_project}.csv") # Ruta del CSV (datasheet) generat

def importar_dataframe_a_sql(df, table_name, columns):
    """Importa un DataFrame a una taula SQL."""
    try:
        # Connecta amb la base de dades utilitzant els paràmetres definits
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        print(f"Inserting data into table: {table_name}")
        # Itera per cada fila del DataFrame
        for _, row in df.iterrows():
            # Crea una cadena de placeholders (%s) per la consulta SQL
            placeholders = ', '.join(['%s'] * len(columns))
            # Construeix la consulta d'inserció SQL amb els noms de les columnes
            insert_query = f"""INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"""
            # Obté els valors de la fila segons l'ordre de les columnes
            row_values = [row[col] for col in columns]
            # Executa la consulta d'inserció amb els valors de la fila
            cursor.execute(insert_query, row_values)
        # Confirma tots els canvis a la base de dades
        connection.commit()
        print(f"Dades importades amb èxit a {table_name}!")
        # Tanca el cursor i la connexió
        cursor.close()
        connection.close()
    except Exception as e:
        # Mostra un missatge d'error si alguna cosa falla
        print(f"Error important dades a {table_name}: {e}")

def main():
    # Obté tots els DataFrames generats pel procés principal
    dfs = generate_dataframes(return_all = True)  # Assegura't que la teva funció main retorna un dict amb tots els DataFrames

    # Per cada taula definida al mapping, importa el DataFrame corresponent
    for table_name, columns in table_mappings.items():
        # Obté el DataFrame corresponent a la taula
        df = dfs.get(table_name)
        # Comprova que el DataFrame existeix i no està buit
        if df is not None and not df.empty:
            # Reordena les columnes del DataFrame segons l'ordre de la taula SQL
            df = df[[col for col in columns if col in df.columns]]
            # Importa el DataFrame a la taula SQL
            importar_dataframe_a_sql(df, table_name, columns)
        else:
            # Mostra un missatge si no hi ha dades per aquesta taula
            print(f"DataFrame per {table_name} no trobat o està buit.")
    
    # Esborra tots els fitxers .csv del directori
    csv_files = glob.glob(os.path.join(csv_dataframes_folder, "*.csv"))
    for f in csv_files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"No s'ha pogut esborrar {f}: {e}")

if __name__ == "__main__":
    # Executa la funció principal si el fitxer s'executa directament
    main()
