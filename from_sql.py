# ------- Llibreries
import random
import pandas as pd
# ------- Classes (connexio a la bbdd)
from connexio_bbdd import PostgresConn
# ------- Funcions
ref_client = '666429400'
# ------- Diccionaris de consultes i fitxers
consultes = {
    "cotes_filtrades": (
        "SELECT * FROM element WHERE classe IN ('CC', 'SC') AND id_referencia_client = %s;",
        (ref_client,)
    ),
}
fitxers_csv = {nom: f"{nom}.csv" for nom in consultes}
# ------- Paràmetres de connexió ------- #
db_params = {
    'host': '172.26.5.159',
    'port': '5433',
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
        df = df.where(pd.notnull(df), '')   # Substitueix valors None per espai en blanc
        return df
    except Exception as e:
        print(f"Error llegint dades: {e}")
        return pd.DataFrame()
    finally:
        db.close()


def cerca_ecap():
    for nom, (consulta, params) in consultes.items():
        df = obtenir_dades(consulta, params)
        if not df.empty:
            if nom == "cotes_filtrades":
                # Reordenar i seleccionar només les columnes desitjades
                columnes_deseades = [
                    'id_element',
                    'classe',
                    'valor_nominal',
                    'tolerancia_superior',
                    'tolerancia_inferior',
                    'descripcio',
                    'propietat'
                ]
                df = df[columnes_deseades]
            print(f"{nom}: {len(df)} files llegides.")
            #df.to_csv(fitxers_csv[nom], index=False)
        else:
            print(f"No s'han trobat dades per {nom}.")
    return df


def df_to_data_list(df):
    """
    Converts a DataFrame with columns:
    ['id_element', 'valor_nominal', 'tolerancia_inferior', 'tolerancia_superior', ...]
    and a column 'valors_mesurats' (list of floats or comma-separated string)
    to a list of dicts in the required format.
    """
    data = []
    for _, row in df.iterrows():
        # If your values are stored as a string, split and convert to float
        # Otherwise, if already a list, just use list(row['valors_mesurats'])
        values = row.get('valors_mesurats', [])
        if isinstance(values, str):
            values = [float(x) for x in values.split(',') if x.strip()]
        elif isinstance(values, list):
            values = [float(x) for x in values]
        else:
            values = []

        data.append({
            'Element': str(row['id_element']),
            'Nominal': float(row['valor_nominal']),
            'Tol-': float(row['tolerancia_inferior']),
            'Tol+': float(row['tolerancia_superior']),
            'Propietat': row.get('propietat', ''),  # Optional, if exists
            'Values': values
        })
    print(data)
    return data


def get_measured_values(ref_client, batch_number, id_element):
    """
    Placeholder: In the future, query the DB for measured values for this dimension.
    For now, returns a sample list of 10 floats.
    """
    # TODO: Query the DB for the real measured values using ref_client, batch_number, id_element
    # Example: SELECT valor FROM mesures WHERE ref_client = ... AND batch_number = ... AND id_element = ...
    # For now, return a sample list:
    return [round(random.uniform(0.018, 0.103), 4) for _ in range(10)]


def build_analysis_data(df, ref_client, batch_number):
    """
    Given a DataFrame of dimensions, build the list of dicts for analysis.
    """
    data = []
    for _, row in df.iterrows():
        id_element = row['id_element']
        # Get measured values (for now, sample data)
        values = get_measured_values(ref_client, batch_number, id_element)
        # TODO: Handle multiple cavities if needed (add a field or logic here)
        data.append({
            'Element': str(id_element),
            'Nominal': float(row['valor_nominal']),
            'Tol-': float(row['tolerancia_inferior']),
            'Tol+': float(row['tolerancia_superior']),
            'Propietat': row.get('propietat', ''),  # Optional, if exists
            'Values': values
        })
    return data

# Example usage:
if __name__ == "__main__":
    ref_client = '666429400'
    batch_number = '1233261'  # Placeholder, replace with real batch number
    df = cerca_ecap()
    if not df.empty:
        data = build_analysis_data(df, ref_client, batch_number)
