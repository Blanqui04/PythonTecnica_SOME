# ------- Llibreries
import random
import pandas as pd
# ------- Classes (connexio a la bbdd)
from connexio_bbdd import PostgresConn
# ------- Funcions
ref_client = '666429400'
batch_number = '1233261'  # Placeholder, replace with real batch number

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

def cerca_dim(ref_client):
    """
    Returns a DataFrame with all elements for the given ref_client (no classe filter).
    """
    query = "SELECT * FROM element WHERE id_referencia_client = %s;"
    params = (ref_client,)
    df = obtenir_dades(query, params)
    if not df.empty:
        # Select and reorder columns as needed (same as in cerca_ecap)
        columnes_deseades = [
            'id_element',
            'classe',
            'valor_nominal',
            'tolerancia_superior',
            'tolerancia_inferior',
            'descripcio',
            'propietat',
            'classe'
        ]
        # Only keep columns that exist in the DataFrame
        cols = [col for col in columnes_deseades if col in df.columns]
        df = df[cols]
        print(f"Totes les cotes: {len(df)} files llegides.")
    else:
        print("No s'han trobat dades per totes les cotes.")
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
            'classe': row.get('classe', ''),  # Optional, if exists
            'descripcio': row.get('descripcio', ''),  # Optional, if exists
            'Values': values
        })
    return data


def get_measured_values(ref_client, batch_number):
    """
    Placeholder: In the future, query the DB for measured values for this dimension.
    For now, returns a sample list of 10 floats.
    """
    # TODO: Query the DB for the real measured values using ref_client, batch_number
    # Example: SELECT valor FROM mesures WHERE ref_client = ... AND batch_number = ...
    # For now, return a sample list:
    return [round(random.uniform(0.176, 0.204), 4) for _ in range(10)]


def build_analysis_data(df, ref_client, batch_number):
    """
    Given a DataFrame of dimensions, build the list of dicts for analysis.
    Skips rows with missing or invalid numeric fields.
    """
    data = []
    for _, row in df.iterrows():
        try:
            id_element = row['id_element']
            # Skip if any required field is missing or empty
            if (row['valor_nominal'] in [None, ''] or
                row['tolerancia_inferior'] in [None, ''] or
                row['tolerancia_superior'] in [None, '']):
                print(f"Skipped id_element {id_element} for missing nominal/tolerance values.")
                continue

            nominal = float(row['valor_nominal'])
            tol_minus = float(row['tolerancia_inferior'])
            tol_plus = float(row['tolerancia_superior'])
            values = get_measured_values(ref_client, batch_number)
            data.append({
                'Element': str(id_element),
                'Nominal': nominal,
                'Tol-': tol_minus,
                'Tol+': tol_plus,
                'Propietat': row.get('propietat', ''),
                'Classe': row.get('classe', ''),  # Optional, if exists
                'Values': values,
                'Descripcio': row.get('descripcio', '')  # Optional, if exists
            })
        except Exception as e:
            print(f"Skipped id_element {row.get('id_element', '?')} due to error: {e}")
            continue
    return data

if __name__ == "__main__":
    df = cerca_ecap()
    if not df.empty:
        data = build_analysis_data(df, ref_client, batch_number)
        df_data = pd.DataFrame(data)
    df_all = cerca_dim(ref_client)
    if not df_all.empty:
        data_all = build_analysis_data(df_all, ref_client, batch_number)
        df_data_all = pd.DataFrame(data_all)
