import os
import psycopg2
import pandas as pd
from maps_columnes import table_mappings, column_mapping
from dades_kop_a_csv import client, ref_project, datasheets_folder


""" Codi per importar dades dels fitxers CSV genereta a la BBDD PostgreSQL.
"""
# Dades de connexió a la BBDD
db_params = {
    'host': 'PC127',
    'database': 'documentacio_tecnica',
    'user': 'administrador',
    'password': 'Some2025.!$%'
}

# Ruta del fitxer CSV
csv_datasheet = os.path.join(datasheets_folder, fr"dades_escandall {client} {ref_project}.csv") # Ruta del CSV (datasheet) generat
print(f"Ruta del CSV: {csv_datasheet}")  # Imprimir la ruta del fitxer CSV generat

def datasheet_dep(csv):
    df = pd.read_csv(csv)  # Llegir el fitxer CSV

    # Step 1: Clean the DataFrame
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Elimina les columnes innecessàries
    df = df.where(pd.notnull(df), None)  # Substitueix NaN per None per compatibilitat SQL

    # Step 2: Separar la columna '2 - Mides (BANDA x PAS x GRUIX):' en 3 columnes
    if '2 - Mides (BANDA x PAS x GRUIX):' in df.columns:
        df[['BANDA', 'PAS', 'GRUIX']] = df['2 - Mides (BANDA x PAS x GRUIX):'].str.split('x', expand=True)
        # Elimina espais innecessaris de les noves columnes
        df['BANDA'] = df['BANDA'].str.strip()
        df['PAS'] = df['PAS'].str.strip()
        df['GRUIX'] = df['GRUIX'].str.strip()
        # Noms de les columnes a eliminar
        columns_delete = [r'2 - Mides (BANDA x PAS x GRUIX):', 
                          r'Dades necessàries per estructurar una Matèria prima',
                          r'Dades necessàries per estructurar una Matriu',
                          r'Dades necessàries per estructurar un Component / Material Aux.',
                          r'Dades necessàries per estructurar una peça / conjunt',
                          r'COMPONENT ESTAMPACIÓ 1',
                          r'COMPONENT ESTAMPACIÓ 2',
                          r'COMPONENT 1 COMPRA',
                          r'COMPONENT 2 COMPRA', 
                          r'COMPONENT 3 COMPRA', 
                          r'DADES PER ESTRUCTURAR NOVES PECES', 
                          r'10 - Tractaments:',
                          r'11 - Embalatge:', 
                          r'PD. La resta d\'informació que s\'entra ja l\'aconseguèix la persona que estructura.',
                          r'ENTRADA DADES FORMULARIS',
                          r'7 - SOP:',
                          r'7 - SOP:.1',
                          r'7 - SOP:.2',] 
        df = df.drop(columns = columns_delete, errors='ignore')  # Elimina les columnes especificades
    
    # Step 3: Convertir manualment les columnes de dates
    data_columns = [
        '10 - Data entrega matriu:', 
        'DATA ENTREGA PLANNING MATRIU', 
        'DATA ENTREGA LAYOUT MATRIU', 
        'DATA FOTs MATRICER', 
        'DATA PROBA A SOME MATRICER (PPAP)',
        '2 - SOP projecte',
        '3 - EOP projecte',
        'DATA KOP',
        'DATA ENVIAMENT PSA'
        
    ]  # Afegeix aquí totes les columnes que saps que són dates

    for col in data_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date  # Converteix al format de només data

    # Desa el DataFrame actualitzat en un nou fitxer CSV
    output_csv = "dades_escandall_actualitzat.csv"
    df.to_csv(output_csv, index=False)
    print(f"DataFrame desat al fitxer: {output_csv}")
    
    return df  # Retorna el DataFrame actualitzat


def importar_csv_a_sql(df, tab, col):
    """ Funció per importar un fitxer CSV a una taula SQL.
    """
    # Conectar a la base de dades
    try:
        connection = psycopg2.connect(
            host     = db_params['host'],
            database = db_params['database'],
            user     = db_params['user'],
            password = db_params['password']
        )
        print("Conexió exitosa a la base de dades")
        cursor = connection.cursor()    

        # Itera sobre les assignacions de taula
        for table_name, columns in tab.items():
            print(f"Inserting data into table: {table_name}")
            print(f"Columns to insert: {columns}")
            # Obté el mapatge de columnes per a la taula actual
            if table_name not in col:
                print(f"Error: No column mapping defined for table {table_name}")
                continue
            
            tab_col_mapping = col[table_name]
            renamed_df = df.rename(columns=tab_col_mapping) # Renombra les columnes del DataFrame segons el mapatge

            # Filtra el DataFrame per a les columnes rellevants de la taula actual
            table_df = renamed_df[columns].dropna(how='all')  # Deixeu anar les files on totes les columnes són NaN
            print(f"Data for {table_name}:")
            print(table_df)

            # Insereix dades a la taula SQL
            for index, row in table_df.iterrows():
                # Crea dinàmicament la consulta INSERT
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders});
                """
                # Mapa les columnes del DataFrame a les columnes de la taula
                values = [row[col] for col in columns]
                cursor.execute(insert_query, values)

        connection.commit()  # Publica l'operació per desar els canvis
        print("Dades importades amb èxit!")
        
        cursor.close()  # Tanca el cursor
        connection.close()  # Tanca la connexió a la base de dades
        print("Connexió tancada.")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Funció principal per executar el procés complet de tractament de dades.
    """
    dataframe = datasheet_dep(csv_datasheet)  # Cridar la funció per netejar el CSV
    print(f"DataFrame netejat: \n {dataframe}")
    importar_csv_a_sql(dataframe, table_mappings, column_mapping)  # Cridar la funció per importar el CSV a SQL


# Executar la funció principal només si el fitxer s'executa directament
if __name__ == "__main__":
    main()
