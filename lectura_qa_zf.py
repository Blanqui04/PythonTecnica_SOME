import re
import os
import glob
import pandas as pd
from kop_csv import ref_project

ref_client = ref_project

cols={'QA-No': 'id_element',
      'Displayed Value': 'descripcio',
      'Classification': 'classe',
      'FeatureType': 'propietat',
      'Nominal Value': 'valor_nominal',
      '+Tolerance': 'tolerancia_superior',
      '-Tolerance': 'tolerancia_inferior',
      'Minimum Value': 'lim_inf',
      'Maximum Value': 'lim_sup'
      }
cols_drop = ['Pos.',
             'Viewname',
             'Displayed Tolerance',
             'Unit']

path = r'C:\Github\PythonTecnica_SOME'

def llegir_qa(cami, ref = None):
    """
    Llegeix l'arxiu excel (informació de cotes del plànol) enviat per client i retorna'l en forma de Dataframe.
    Si 'cami' és una carpeta, busca un fitxer Excel amb 'QA' (i opcionalment ref_project) al nom.
    """
    excel_file = cami

    # Si cami és una carpeta, busca el fitxer
    if os.path.isdir(cami):
        pattern = "*QA*.xls*" if not ref else f"*{ref}*QA*.xls*"
        files = glob.glob(os.path.join(cami, pattern))
        if not files:
            print("No s'ha trobat cap fitxer Excel amb 'QA' al nom.")
            return None
        excel_file = files[0]  # Agafa el primer que trobi

    try:
        df = pd.read_excel(excel_file, engine = 'xlrd' if excel_file.endswith('.xls') else None)
        df = df.dropna(how='all')       # Elimina files buides
        df = df.reset_index(drop=True)  # Reinicia l'índex
        return df
    except Exception as e:
        print(f"Error al llegir l'arxiu: {e}")
        return None


def qa_rename(dg):
    """
    Retorna un DataFrame amb les dades de QA per a la base de dades SQL.
    Converteix tots els NaN a None.
    """
    if dg is not None:
        dg = dg.rename(columns=cols)
        dg = dg.drop(columns=[col for col in cols_drop if col in dg.columns])
        for col in dg.columns:
            dg[col] = dg[col].map(lambda x: None if pd.isna(x) else x)
        return dg


def expand_nx_dimensions(dg):
    """
    Expandeix les files on 'descripcio' comença amb Nx (ex: 3x, 4x, 2X, etc.).
    Clona la fila tantes vegades com indica N, actualitzant 'cota' i netejant 'descripcio'.
    """
    rows = []
    for _, row in dg.iterrows():
        match = re.match(r"^(\d+)[xX]\s*(.*)", str(row['descripcio']), re.IGNORECASE)
        if match:
            n = int(match.group(1))
            desc = match.group(2).strip()
            for i in range(1, n + 1):
                new_row = row.copy()
                new_row['id_element'] = f"{row['id_element']}.{i}"
                new_row['descripcio'] = desc
                rows.append(new_row)
        else:
            rows.append(row)
    return pd.DataFrame(rows)


def neteja_symbols_i_referencia(df, ref_client):
    """
    Substitueix símbols GD&T unicode per (M), (L), (E), el símbol de graus per (gr.) i Ø per (diam.).
    Afegeix la columna 'id_referencia_client'.
    """
    # Diccionari de substitució
    symbol_map = {
        'Ⓜ': '(M)',
        'Ⓛ': '(L)',
        'ⓔ': '(E)',
        'Ⓜ️': '(M)',  # variant emoji
        'Ⓛ️': '(L)',
        'ⓔ️': '(E)',
        'º': '(gr.)',
        '°': '(gr.)',
        'Ø': '(diam.)',
        'ø': '(diam.)'
    }
    def replace_symbols(text):
        if not isinstance(text, str):
            return text
        for k, v in symbol_map.items():
            text = text.replace(k, v)
        return text

    df['descripcio'] = df['descripcio'].apply(replace_symbols)
    df['id_referencia_client'] = ref_client
    return df


import numpy as np

def fix_decimal_separator(df, columns=None):
    """
    Converteix les comes a punts en les columnes numèriques especificades i les converteix a float.
    Si columns és None, intenta detectar totes les columnes numèriques.
    """
    if columns is None:
        columns = ['valor_nominal', 'tolerancia_superior', 'tolerancia_inferior', 'lim_sup', 'lim_inf']
    for col in columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
                .replace(['nan', 'None', '', ' '], np.nan)
                .astype(float)
            )
    return df



df = llegir_qa(path)
qa_df = qa_rename(df)

qa_df_exp = expand_nx_dimensions(qa_df)
qa = neteja_symbols_i_referencia(qa_df_exp, ref_client)
qa = fix_decimal_separator(qa, columns=['valor_nominal', 'tolerancia_superior', 'tolerancia_inferior', 'lim_sup', 'lim_inf'])
qa.to_csv(os.path.join(f"{ref_project}_element.csv"), index=False)
