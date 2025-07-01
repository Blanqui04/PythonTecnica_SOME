# ------- Llibreries
import pandas as pd
# ------- Classes (connexio a la bbdd)
from connexio_bbdd import PostgresConn
# ------- Funcions

# ------- Diccionaris de consultes i fitxers
consultes = {
    "clients": ("SELECT * FROM clients;", None),
    "peces": ("SELECT * FROM peca WHERE estat = %s;", ('actiu',)),
    # Afegeix més consultes segons necessitis
}
fitxers_csv = {nom: f"{nom}.csv" for nom in consultes}

# ------- Paràmetres de connexió
db_params = {
    'host': '172.26.5.159',
    'database': 'documentacio_tecnica',
    'user': 'administrador',
    'password': 'Some2025.!$%'
}

def obtenir_dades(query, params=None):
    """Llegeix dades de la base de dades i retorna un DataFrame de pandas."""
    db = PostgresConn(**db_params)
    try:
        conn = db.connect()
        df = pd.read_sql_query(query, conn, params=params)
        # Substitueix valors None per espai en blanc
        df = df.where(pd.notnull(df), '')
        return df
    except Exception as e:
        print(f"Error llegint dades: {e}")
        return pd.DataFrame()
    finally:
        db.close()


def main():
    for nom, (consulta, params) in consultes.items():
        df = obtenir_dades(consulta, params)
        if not df.empty:
            print(f"{nom}: {len(df)} files llegides.")
            # Desa a CSV amb el nom dinàmic
            df.to_csv(fitxers_csv[nom], index=False)
        else:
            print(f"No s'han trobat dades per {nom}.")


if __name__ == "__main__":
    main()
    