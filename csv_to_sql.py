import os
import psycopg2
import pandas as pd
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

# Mapping of tables and their corresponding columns
table_mappings = {
    'table1': ['columna1', 'columna2', 'columna3'], # Columns for table1
    'table2': ['columna4', 'columna5'],             # Columns for table2
    'table3': ['columna6', 'columna7', 'columna8'], # Columns for table3
}

# Ruta del fitxer CSV
csv_datasheet = os.path.join(datasheets_folder, fr"dades_escandall {client} {ref_project}.csv") # Ruta del CSV (datasheet) generat
print(f"Ruta del CSV: {csv_datasheet}")  # Imprimir la ruta del fitxer CSV generat

def importar_csv_a_sql(csv, tab):
    """
    Funció per importar un fitxer CSV a una taula SQL.
    """
    df = pd.read_csv(csv) # Llegir el fitxer CSV
    print(df.head())  # Print the first few rows of the DataFrame for debugging
    
    # Step 1: Clean the DataFrame
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]    # Drop unnecessary columns (example: drop columns with "Unnamed" in their name)
    df = df.where(pd.notnull(df), None) # Replace NaN with None for SQL compatibility# Replace NaN values with NULL (PostgreSQL-compatible)
    print("Cleaned DataFrame:")
    print(df.head())  # Print the cleaned DataFrame for debugging

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

        # Iterate over the table mappings
        for table_name, columns in tab.items():
            print(f"Inserting data into table: {table_name}")

            # Filter the DataFrame for the relevant columns for the current table
            table_df = df[columns].dropna(how='all')  # Drop rows where all columns are NaN
            print(f"Data for {table_name}:")
            print(table_df.head())

            # Insert data into the table
            for index, row in table_df.iterrows():
                # Dynamically create the INSERT query
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders});
                """
                # Map DataFrame columns to table columns
                values = [row[col] for col in columns]
                cursor.execute(insert_query, values)

        connection.commit()  # Commit the transaction to save changes
        print("Dades importades amb èxit!")
        
        cursor.close()
        connection.close()
        print("Connexió tancada.")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Funció principal per executar el procés complet de tractament de dades.
    """
    importar_csv_a_sql(csv_datasheet, table_mappings)  # Cridar la funció per importar el CSV a SQL


# Executar la funció principal només si el fitxer s'executa directament
if __name__ == "__main__":
    main()
