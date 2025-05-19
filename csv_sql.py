import os
import psycopg2
import pandas as pd
from csv_func import datasheet_dep, info_embalatge, info_processos
from maps_columnes import table_mappings, col_map, col_elim, dates
from kop_csv import client, ref_project, datasheets_folder


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

def importar_csv_a_sql(df, tab, col):
    """ Funció per importar un fitxer CSV a una taula SQL.
    """
    # Conectar a la base de dades
    try:
        connection = psycopg2.connect(
            host = db_params['host'],
            database = db_params['database'],
            user = db_params['user'],
            password = db_params['password']
        )
        print("Visca! Connexió exitosa a la base de dades!! \n")
        cursor = connection.cursor()

        for table_name, columns in tab.items():                 # Itera sobre les assignacions de taula
            print(f"Inserting data into table: {table_name}")
            print(f"Columns to insert: {columns} \n")
            
            if table_name not in col:                           # Obté el mapatge de columnes per a la taula actual
                print(f"Error: No column mapping defined for table {table_name}")
                continue
            
            tab_col_mapping = col[table_name]                   # print(tab_col_mapping) per veure la relacio entre camps per a aquella taula
            renamed_df = df.rename(columns = tab_col_mapping)   # Reanomena les columnes del DataFrame segons el mapatge
            renamed_df['id_referencia_client'] = ref_project    # Afegir 'id_referencia_client' al DataFrame amb el nom de la referència del client pel projecte
            renamed_df['id_referencia_some'] = 51007698         # Buscar d'alguna manera la referència some, i inserir-la aquí
                                  
            # Filtra el DataFrame per a les columnes rellevants de la taula actual
            table_df = renamed_df[columns].dropna(how='all')  # Deixeu anar les files on totes les columnes són NaN
            print(f"Data for {table_name}:")
            print(f"{table_df} \n")
            
            out_csv = f"{ref_project}_{table_name}.csv"
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


def importar_oferta_csv(csv_path, db_params):
    """Importa dades de la taula oferta des d'un CSV i elimina el fitxer si tot va bé."""
    try:
        df = pd.read_csv(csv_path)
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        print("Connexió a la base de dades per a OFERTA establerta.")

        # Assegura't que les columnes coincideixen amb la taula oferta
        oferta_columns = [
            'num_oferta', 'cicles', 'num_processos', 'descripcio',
            'id_client', 'id_referencia_client', 'num_escandall', 'oee'
        ]
        # Si falta alguna columna, afegeix-la amb None
        for col in oferta_columns:
            if col not in df.columns:
                df[col] = None

        for _, row in df.iterrows():
            placeholders = ', '.join(['%s'] * len(oferta_columns))
            insert_query = f"""INSERT INTO oferta ({', '.join(oferta_columns)}) VALUES ({placeholders});"""
            row_values = [row[col] for col in oferta_columns]
            cursor.execute(insert_query, row_values)

        connection.commit()
        print("Dades d'oferta importades amb èxit!")

        cursor.close()
        connection.close()

        # Elimina el fitxer CSV només si tot ha anat bé
        os.remove(csv_path)
        print(f"Fitxer {csv_path} eliminat.")

    except Exception as e:
        print(f"Error important oferta: {e}")


def main():
    """ Funció principal per executar el procés complet de tractament de dades.
    """
    df = datasheet_dep(csv_datasheet)                       # Cridar la funció per netejar el CSV
    dataframe = info_embalatge(df)
    info_processos(dataframe)
    oferta_csv = os.path.join(os.path.dirname(__file__), f"{ref_project}_oferta.csv")
    df_oferta = pd.read_csv(oferta_csv)
    importar_csv_a_sql(df_oferta, {'oferta': table_mappings['oferta']}, col_map)
    os.remove(oferta_csv)
    importar_csv_a_sql(dataframe, table_mappings, col_map)  # Cridar la funció per importar el CSV a SQL


if __name__ == "__main__":  # Executar la funció principal només si el fitxer s'executa directament
    main()
