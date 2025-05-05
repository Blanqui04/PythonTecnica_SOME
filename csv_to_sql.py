import psycopg2
import pandas as pd

""" Codi per importar dades dels fitxers CSV genereta a la BBDD PostgreSQL.
"""

# Dades de connexió a la BBDD
host = "PC127"
database = "nom_base_dades"
user = "usuari"
password = "contrassenya"

# Ruta del fitxer CSV
csv_file_path = "ruta/del/fitxer.csv"

def importar_csv_a_sql(csv):
    """
    Funció per importar un fitxer CSV a una taula SQL.
    """
    # Llegir el fitxer CSV
    df = pd.read_csv(csv)

    # Conectar a la base de dades
    try:
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        print("Conexió exitosa a la base de dades")
        cursor = connection.cursor()    

        # Crear la taula si no existeix
        create_table_query = """
        CREATE TABLE IF NOT EXISTS nom_taula (
            columna1 VARCHAR(255),
            columna2 INT,
            columna3 DATE
        );
        """
        cursor.execute(create_table_query)
        connection.commit()

        # Importar les dades del CSV a la taula SQL
        for index, row in df.iterrows():
            insert_query = f"""
            INSERT INTO nom_taula (columna1, columna2, columna3)
            VALUES ('{row['columna1']}', {row['columna2']}, '{row['columna3']}');
            """
            cursor.execute(insert_query)

        connection.commit()
        print("Dades importades amb èxit!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Connexió tancada.")
