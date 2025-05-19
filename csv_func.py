import os
import pandas as pd
from maps_columnes import col_elim, dates
from kop_csv import client, ref_project, datasheets_folder
from datetime import datetime, timedelta

csv_datasheet = os.path.join(datasheets_folder, fr"dades_escandall {client} {ref_project}.csv") # Ruta del CSV (datasheet) generat
print(f"Ruta del CSV: {csv_datasheet}")  # Imprimir la ruta del fitxer CSV generat 

def cw_date(cw):
    """
    Convert a date in format cwXX/YY (or variations like cw XX/YY, cw.XX/YY) to YYYY-MM-DD.
    """
    try:
        if isinstance(cw, str) and cw.lower().replace(' ', '').startswith('cw'):    # Remove spaces and periods
            cleaned_cw = cw.replace(' ', '').replace('.', '')
            week, year = map(int, cleaned_cw[2:].split('/'))
            # Handle two-digit years
            if year < 100:
                year += 2000
            first_day_of_year = datetime(year, 1, 1)
            date = first_day_of_year + timedelta(weeks=week - 2)
            
            return (date - timedelta(days=date.weekday())).strftime('%Y-%m-%d')
        return cw
    except Exception as e:
        print(f"Error converting {cw}: {e}")
        return cw


def datasheet_dep(csv):
    """
    Tractament del 'datasheet' extret del KOP: Columnes buides, repetides, innecessàries, format de data, etc.
    """
    # Read the CSV file
    dg = pd.read_csv(csv)
    dg = dg.loc[:, ~dg.columns.str.contains('^Unnamed')]  # Remove unnecessary columns
    dg = dg.where(pd.notnull(dg), None)  # Replace NaN with None for SQL compatibility

    # Split the material dimensions column into separate columns (Banda, Pas, Gruix)
    if '2 - Mides (BANDA x PAS x GRUIX):' in dg.columns:
        dg[['BANDA', 'PAS', 'GRUIX']] = dg['2 - Mides (BANDA x PAS x GRUIX):'].str.split('x', expand=True)
        dg['BANDA'] = dg['BANDA'].str.strip().str.replace(',', '.', regex=False)  # Clean up values
        dg['PAS'] = dg['PAS'].str.strip().str.replace(',', '.', regex=False)
        dg['GRUIX'] = dg['GRUIX'].str.strip().str.replace(',', '.', regex=False)
        
    if '2 - Tipus:  SQB / KSW / MIXTE:' in dg.columns:
        def assign_plant(value):
            if pd.isnull(value):
                return 1000  # Default to SQB if missing
            val = str(value).upper()
            if 'MIX SOME SA/KSW' in val:
                return 'Mixt'
            elif 'FULL SOME KSW' in val or 'KSW' in val:
                return 2000
            elif 'FULL SOME SA' in val or 'SQB' in val:
                return 1000
            elif 'MIXT' in val or 'BOTH' in val:
                return 'Mixt'
            else:
                return 1000  # Default to SQB

        dg['planta_produccio'] = dg['2 - Tipus:  SQB / KSW / MIXTE:'].apply(assign_plant)
        dg.drop(columns=['2 - Tipus:  SQB / KSW / MIXTE:'], inplace=True)
        
    dg.drop(columns=col_elim, errors='ignore', inplace=True) # Drop unnecessary columns
   
     # Only process columns in the 'dates' list
    for column in dates:
        if column in dg.columns:
            dg[column] = dg[column].apply(cw_date)
            dg[column] = pd.to_datetime(dg[column], errors='coerce').dt.date

    return dg


def info_embalatge(dg):
    # Comprova que existeixen les columnes necessàries
    pc_1 = 'Peces / Caixa:'
    pc_2 = 'Peces / Caixa:.1'
    # Si alguna columna no existeix, afegeix-la amb valor 0
    if pc_1 not in dg.columns:
        dg[pc_1] = 0
    if pc_2 not in dg.columns:
        dg[pc_2] = 0

    def calcula_regio_pcs(row):
        try:
            v1 = float(row[pc_1]) if row[pc_1] not in [None, '', 'nan'] else 0
        except Exception:
            v1 = 0
        try:
            v2 = float(row[pc_2]) if row[pc_2] not in [None, '', 'nan'] else 0
        except Exception:
            v2 = 0

        if v1 > 0 and v2 == 0:
            return pd.Series(['Europa', v1])
        elif v2 > 0 and v1 == 0:
            return pd.Series(['overseas', v2])
        elif v1 == 0 and v2 == 0:
            return pd.Series(['Europa', 0])
        else:
            return pd.Series(['Na', 0])

    dg[['regio_exp', 'pcs_cx']] = dg.apply(calcula_regio_pcs, axis=1)

    
    if 'Caixa:' and 'Pallet:' in dg.columns:
        
        dg['codi_caixa'] = dg['Caixa:'].str.extract(r'(\d+)')                   # Extract the 'id' using regex to match digits at the start
        dg['descripcio_caixa'] = dg['Caixa:'].str.extract(r'\d+ - (.+)')        # Extract the 'descripcio' using regex to match everything after the id and hyphen

        dg['codi_pallet'] = dg['Pallet:'].str.extract(r'(\d+)')                 # Extract the 'id' using regex to match digits at the start
        dg['descripcio_pallet'] = dg['Pallet:'].str.extract(r'\d+ - (.+)')      # Extract the 'descripcio' using regex to match everything after the id and hyphen
        
        dg.dropna(axis=1, inplace=True)
        
        # Save the updated DataFrame to a new CSV file
        out_csv = "dades_KOP_act.csv"
        dg.to_csv(out_csv, index = False)
        print(f"DataFrame processed and saved to: {out_csv} \n")
        
        return dg   # Return the full DataFrame with the new columns
            
    else:
        raise ValueError("The DataFrame does not contain the 'Caixa:' column.")
    
def info_processos(dg, id_col='13 - Nº Expedient:'):
    ct_cols = [f'* Centre Treball{"" if i == 0 else f".{i}"}' for i in range(5)]                 # Columnes dels centres de treball a l'estructura del KOP
    d_cols = [f'* Descripció CT{"" if i == 0 else f".{i}"}' for i in range(5)]                   # Columnes descripció del centre de treball / activitat al CT
    cpm_cols = [f'* cpm o (peces/hora) per CT{"" if i == 0 else f".{i}"}' for i in range(5)]     # Cicles i OEE / Peces hora - Ritme de producció al centre de treball.
    
    for col in ct_cols:
        if col not in dg.columns:
            dg[col] = ""
    for col in d_cols:
        if col not in dg.columns:
            dg[col] = ""
    for col in cpm_cols:
        if col not in dg.columns:
            dg[col] = ""
    
    rows = []  # This will store the exploded rows

    # Iterate over each row in the DataFrame
    for idx, row in dg.iterrows():
        # Get the unique id for this row (use id_col if it exists, otherwise fallback to index)
        ref_id = row[id_col] if id_col in row and pd.notnull(row[id_col]) else idx

        # For each possible process step (0 to 4)
        for i in range(5):
            ct_val = row[ct_cols[i]]    # Value for Centre Treball i
            d_val = row[d_cols[i]]      # Value for Descripció CT i
            cpm_val = row[cpm_cols[i]]  # Value for CPM i
            
            if pd.notnull(ct_val) and str(ct_val).strip() != "" and pd.notnull(d_val) and str(d_val).strip() != "":
                # Default values
                cpm = None
                oee = None

                if pd.notnull(cpm_val) and str(cpm_val).strip() != "":
                    cpm_str = str(cpm_val).strip()
                    if "/" in cpm_str:
                        # Format like "45 / OEE:45,19%"
                        parts = cpm_str.split("/")
                        cpm = parts[0].strip()
                        oee_part = parts[1].strip() if len(parts) > 1 else ""
                        # Extract OEE value
                        if "OEE:" in oee_part:
                            oee_str = oee_part.replace("OEE:", "").replace("%", "").replace(",", ".").strip()
                            try:
                                oee = float(oee_str)
                            except Exception:
                                oee = None
                        else:
                            oee = 100.0
                        # Try to convert CPM to float/int
                        try:
                            cpm = float(cpm.replace(",", "."))
                        except Exception:
                            cpm = None
                    else:
                        # Only CPM, OEE is 100%
                        try:
                            cpm = float(cpm_str.replace(",", "."))
                        except Exception:
                            cpm = None
                        oee = 100.0
                else:
                    cpm = None
                    oee = None

                rows.append({
                    'num_oferta': ref_id,
                    'num_escandall': ref_id,
                    'id_client': client,
                    'id_referencia_client': ref_project,
                    'num_processos': ct_val,
                    'descripcio': d_val,
                    'cicles': cpm,
                    'oee': oee
                })

    oferta_df = pd.DataFrame(rows)
    out_csv = f"{ref_project}_oferta.csv"
    oferta_df.to_csv(out_csv, index=False)
    return oferta_df


df = datasheet_dep(csv_datasheet)
df = info_embalatge(df)

info_processos(df)
