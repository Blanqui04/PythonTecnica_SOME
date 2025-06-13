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

# Ruta del CSV (datasheet) generat
csv_datasheet = os.path.join(csv_dataframes_folder, fr"dades_escandall {client} {ref_project}.csv") 

def importar_dataframe_a_sql(df, tab_name, cols):
    """Importa un DataFrame a una taula SQL.
    """
    try:
        connection = psycopg2.connect(**db_params) #type: ignore # Connecta amb la base de dades utilitzant els paràmetres definits
        cursor = connection.cursor()
        print(f"Inserting data into table: {tab_name}")
        
        for _, row in df.iterrows():                                                                    # Itera per cada fila del DataFrame
            placeholders = ', '.join(['%s'] * len(cols))                                                # Crea una cadena de placeholders (%s) per la consulta SQL
            insert_query = f"""INSERT INTO {tab_name} ({', '.join(cols)}) VALUES ({placeholders});"""   # Construeix la consulta d'inserció SQL amb els noms de les columnes
            
            row_values = [row[col] if pd.notnull(row[col]) else None for col in cols]
            cursor.execute(insert_query, row_values)    # Executa la consulta d'inserció amb els valors de la fila
            
        connection.commit() # Confirma tots els canvis a la base de dades
        print(f"Dades importades amb èxit a {tab_name}!")
        
        cursor.close()  # Tanca el cursor i la connexió
        connection.close()
        
    except Exception as e:
        print(f"Error important dades a {tab_name}: {e}")   # Mostra un missatge d'error si alguna cosa falla

def main():
    # Obté tots els DataFrames generats pel procés principal
    dfs = generate_dataframes(return_all = True)  # La funció retorna un diccionari amb tots els DataFrames

    # Per cada taula definida al mapping, importa el DataFrame corresponent
    for table_name, columns in table_mappings.items():
        df = dfs.get(table_name)    # type: ignore # Obté el DataFrame corresponent a la taula
        
        if df is not None and not df.empty:                         # Comprova que el DataFrame existeix i no està buit
            df = df[[col for col in columns if col in df.columns]]  # Reordena les columnes del DataFrame segons l'ordre de la taula SQL
            importar_dataframe_a_sql(df, table_name, columns)       # Importa el DataFrame a la taula SQL
            
        else:
            print(f"DataFrame per {table_name} no trobat o està buit.") # Mostra un missatge si no hi ha dades per aquesta taula

    csv_files = glob.glob(os.path.join(csv_dataframes_folder, "*.csv")) # Esborra tots els fitxers .csv del directori
    
    for file in csv_files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"No s'ha pogut esborrar {file}: {e}")

if __name__ == "__main__":
    main()  # Executa la funció principal si el fitxer s'executa directament
