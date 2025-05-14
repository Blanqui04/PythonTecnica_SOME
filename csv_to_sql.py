import os
import psycopg2
import pandas as pd
from maps_columnes import table_mappings, col_map, col_elim, dates
from dades_kop_a_csv import client, ref_project, datasheets_folder

""" Codi per importar dades dels fitxers CSV genereta a la BBDD PostgreSQL.
"""
# Dades de connexió a la BBDD
db_params = {
    'host': '172.26.5.159',
    'database': 'documentacio_tecnica',
    'user': 'administrador',
    'password': 'Some2025.!$%'
}

csv_datasheet = os.path.join(datasheets_folder, fr"dades_escandall {client} {ref_project}.csv") # Ruta del CSV (datasheet) generat
print(f"Ruta del CSV: {csv_datasheet}")  # Imprimir la ruta del fitxer CSV generat

def datasheet_dep(csv):
    """Tractament del 'datasheet' extret del KOP: Columnes buides, repetides, innecessàries, format de data, etc.
    """
    
    df = pd.read_csv(csv)  # Llegir el fitxer CSV
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]    # Elimina les columnes innecessàries
    df = df.where(pd.notnull(df), None)                     # Substitueix NaN per None per compatibilitat SQL

    # Separar la columna de mides del materal en 3 columnes (Banda, Pas, Gruix)
    if '2 - Mides (BANDA x PAS x GRUIX):' in df.columns:
        df[['BANDA', 'PAS', 'GRUIX']] = df['2 - Mides (BANDA x PAS x GRUIX):'].str.split('x', expand=True)
        df['BANDA'] = df['BANDA'].str.strip()               # Elimina espais innecessaris de les noves columnes
        df['PAS'] = df['PAS'].str.strip()                   # "
        df['GRUIX'] = df['GRUIX'].str.strip()               # "
        
    if '* cpm o (peces/hora) per CT' in df.columns:
        df[['CPM', 'OEE']] = df['* cpm o (peces/hora) per CT'].str.split('/', expand=True)
        df['CPM'] = df['CPM'].str.strip()
        df['OEE'] = df['OEE'].str.replace('OEE: ', '', regex=False).str.strip() if 'OEE' in df else None
        
    df = df.drop(columns = col_elim, errors='ignore')   # Elimina les columnes especificades
        
    for col in dates:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date  # Converteix al format de només data (sense hora)

    # Desa el DataFrame actualitzat en un nou fitxer CSV
    output_csv = "dades_escandall_actualitzat.csv"
    df.to_csv(output_csv, index=False)
        
    return df


def importar_csv_a_sql(df, tab, col):
    """ Funció per importar un fitxer CSV a una taula SQL.
    """
    # Conectar a la base de dades
    try:
        connection = psycopg2.connect(
            host=db_params['host'],
            database=db_params['database'],
            user=db_params['user'],
            password=db_params['password']
        )
        print("Visca! Connexió exitosa a la base de dades!! \n")
        cursor = connection.cursor()

        # Itera sobre les assignacions de taula
        for table_name, columns in tab.items():
            print(f"Inserting data into table: {table_name}")
            print(f"Columns to insert: {columns} \n")
            
            # Obté el mapatge de columnes per a la taula actual
            if table_name not in col:
                print(f"Error: No column mapping defined for table {table_name}")
                continue
            
            tab_col_mapping = col[table_name]
            renamed_df = df.rename(columns=tab_col_mapping)     # Reanomena les columnes del DataFrame segons el mapatge
            renamed_df['id_referencia_client'] = ref_project    # Afegir 'id_referencia_client' al DataFrame amb el nom de la referència del client pel projecte
            renamed_df['id_referencia_some'] = 51007698         # Buscar d'alguna manera la referència some, i inserir-la aquí
            
            # Filtra el DataFrame per a les columnes rellevants de la taula actual
            table_df = renamed_df[columns].dropna(how='all')  # Deixeu anar les files on totes les columnes són NaN
            print(f"Data for {table_name}:")
            print(table_df)
            
            out_csv = f"dades_{table_name}.csv"
            table_df.to_csv(out_csv, index=False)

            for index, row in table_df.iterrows():
                # Crea dinàmicament la consulta INSERT
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"""INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"""

                # Inserció de dades
                row_values = [row[col] for col in columns]
                print(f" Executing query: \n {insert_query} \n With values: \n {row_values} \n")
                cursor.execute(insert_query, row_values)

        connection.commit()  # Publica l'operació per desar els canvis
        print("Dades importades amb èxit!")

        cursor.close()  # Tanca el cursor
        connection.close()  # Tanca la connexió a la base de dades
        print("Connexió tancada.")

    except Exception as e:
        print(f"Meeeerda... Error: {e}")


def main():
    """
    Funció principal per executar el procés complet de tractament de dades.
    """
    dataframe = datasheet_dep(csv_datasheet)                 # Cridar la funció per netejar el CSV
    importar_csv_a_sql(dataframe, table_mappings, col_map)   # Cridar la funció per importar el CSV a SQL


# Executar la funció principal només si el fitxer s'executa directament
if __name__ == "__main__":
    main()
