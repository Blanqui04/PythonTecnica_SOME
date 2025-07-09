# src/data_processing/data_transformer.py
import os
import re
import pandas as pd
from datetime import datetime, timedelta
import configparser
from pathlib import Path
import logging
from ..exceptions import TransformationError

class DataTransformer:
    def __init__(self, client, ref_project, config_path='config/config.ini'):
        self.client = client
        self.ref_project = ref_project
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Setup paths
        self.base_dir = Path(self.config['PATHS']['base_dir'])
        self.datasheets_dir = self.base_dir / self.config['PATHS']['datasheets_dir']
        self.db_export_dir = self.base_dir / self.config['PATHS']['db_export_dir']
        
        # Ensure output directory exists
        self.db_export_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_dir = self.base_dir / self.config['PATHS']['log_dir']
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=log_dir / 'data_transformer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Column mappings would be loaded from config/column_mappings/
        self.col_elim = self._load_column_mappings()

    def _load_column_mappings(self):
        """Load column elimination mappings from config files"""
        # Implementation would read from JSON/CSV in config/column_mappings/
        return ['Unnamed: 0', 'Unnamed: 1']  # Example columns to eliminate

    def cw_date(self, cw):
        """Convert calendar week format to YYYY-MM-DD"""
        try:
            if isinstance(cw, str) and cw.lower().replace(' ', '').startswith('cw'):
                match = re.search(r'cw\s*0*(\d{1,2})\D+(\d{2,4})', cw, re.IGNORECASE)
                if match:
                    week = int(match.group(1))
                    year = int(match.group(2))
                    if year < 100:
                        year += 2000
                    first_day_of_year = datetime(year, 1, 1)
                    date = first_day_of_year + timedelta(weeks=week - 2)
                    return (date - timedelta(days=date.weekday())).strftime('%Y-%m-%d')
            return cw
        except Exception as e:
            logging.error(f"Date conversion error: {e}")
            return cw

    def extract_cavitats(self, val):
        """Extract number of cavities from various formats"""
        if pd.isnull(val):
            return ""
        s = str(val)
        if m := re.match(r'^\s*(\d+)', s):
            return int(m.group(1))
        if "+" in s:
            return sum(int(n) for n in re.findall(r'\d+', s))
        if nums := re.findall(r'\d+', s):
            return int(nums[0])
        return ""

    def transform_datasheet(self, datasheet_name):
        """Main transformation workflow"""
        try:
            csv_path = self.datasheets_dir / f"{datasheet_name}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Datasheet not found: {csv_path}")
                
            df = self._preprocess_datasheet(csv_path)
            
            return {
                'embalatge': self.info_embalatge(df),
                'oferta': self.info_oferta(df),
                'matriu': self.info_matriu(df),
                'material': self.info_material(df),
                'escandalloferta': self.info_escandalloferta(df),
                'lifetime': self.info_lifetime(df),
                'tractaments': self.info_tractaments(df),
                'produccio': self.info_produccio(df),
                'part': self.info_part(df),
                'planol': self.info_planol(df),
                'tipus': self.info_tipus(df)
            }
        except Exception as e:
            logging.exception("Transformation failed")
            raise TransformationError(f"Data transformation error: {e}") from e

    def _preprocess_datasheet(self, csv_path):
        """Load and clean datasheet"""
        df = pd.read_csv(csv_path)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.where(pd.notnull(df), None)
        df.drop(columns=self.col_elim, errors='ignore', inplace=True)
        df.dropna(inplace=True)
        return df


    def info_embalatge(self, df):
        col_bbdd_emb = ['regio', 'peces_caixa', 'caixa_codi', 'caixa_descripcio',
                        'pallet_codi', 'pallet_descripcio', 'tapa_altres', 'caixes_pallet']

        embalatge_cols = ['regio_exp', 'pcs_cx', 'codi_caixa', 'descripcio_caixa',
                        'codi_pallet', 'descripcio_pallet', 'Tapa / Altres:', 'Caixes / Pallet:']
        
        pc_1 = 'Peces / Caixa:'
        pc_2 = 'Peces / Caixa:.1'
        if pc_1 not in df.columns:
            df[pc_1] = 0
        if pc_2 not in df.columns:
            df[pc_2] = 0

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

        df[['regio_exp', 'pcs_cx']] = df.apply(calcula_regio_pcs, axis=1)

        if 'Caixa:' in df.columns and 'Pallet:' in df.columns:
            df['codi_caixa'] = df['Caixa:'].astype(str).str.extract(r'(\d+)')
            df['descripcio_caixa'] = df['Caixa:'].astype(str).str.extract(r'\d+ - (.+)')
            df['codi_pallet'] = df['Pallet:'].astype(str).str.extract(r'(\d+)')
            df['descripcio_pallet'] = df['Pallet:'].astype(str).str.extract(r'\d+ - (.+)')

            embalatge_df = df[embalatge_cols].copy()
            embalatge_df.columns = col_bbdd_emb
            embalatge_df['id_referencia_client'] = self.ref_project

            out_csv = self.db_export_dir / f"{self.ref_project}_embalatge.csv"
            embalatge_df.to_csv(out_csv, index=False)

            return embalatge_df
        else:
            raise ValueError("The DataFrame does not contain the 'Caixa:' and/or 'Pallet:' columns.")

    def info_oferta(self, dg, tract_df = None):
        ct_cols = [f'* Centre Treball{"" if i == 0 else f".{i}"}' for i in range(5)]
        d_cols = [f'* Descripció CT{"" if i == 0 else f".{i}"}' for i in range(5)]
        cpm_cols = [f'* cpm o (peces/hora) per CT{"" if i == 0 else f".{i}"}' for i in range(5)]
        
        press_map = {
        '250': 'PR250',
        '400': 'PR400',
        '500': 'PR500',
        '160': 'PR160',
        '100': 'PR100',
        '125': 'PR125'}

        for col in ct_cols:
            if col not in dg.columns:
                dg[col] = ""
        for col in d_cols:
            if col not in dg.columns:
                dg[col] = ""
        for col in cpm_cols:
            if col not in dg.columns:
                dg[col] = ""

        ctoferta_rows = []
        oferta_rows = []

        for idx, row in dg.iterrows():
            ref_id = row['13 - Nº Expedient:'] if '13 - Nº Expedient:' in row and pd.notnull(row['13 - Nº Expedient:']) else idx

            ct_count = 0    # Collect CT rows for ofertact
            for i in range(5):
                ct_val = row[ct_cols[i]]
                d_val = row[d_cols[i]]
                cpm_val = row[cpm_cols[i]]

                if pd.notnull(ct_val) and str(ct_val).strip() != "" and pd.notnull(d_val) and str(d_val).strip() != "":
                    ct_val_clean = re.sub(r'^\s*c\.?t\.?-\s*', '', str(ct_val), flags=re.IGNORECASE)
                    match = re.match(r'Premsa\s*(\d{3})\s*Tn', ct_val_clean, re.IGNORECASE)
                    if match and match.group(1) in press_map:
                        ct_val_clean = press_map[match.group(1)]
                    cpm = None
                    oee = None

                    if pd.notnull(cpm_val) and str(cpm_val).strip() != "":
                        cpm_str = str(cpm_val).strip()
                        if "/" in cpm_str:
                            parts = cpm_str.split("/")
                            cpm = parts[0].strip()
                            oee_part = parts[1].strip() if len(parts) > 1 else ""
                            if "OEE:" in oee_part:
                                oee_str = oee_part.replace("OEE:", "").replace("%", "").replace(",", ".").strip()
                                try:
                                    oee = float(oee_str)
                                except Exception:
                                    oee = None
                            else:
                                oee = 100.0
                            try:
                                cpm = float(cpm.replace(",", "."))
                            except Exception:
                                cpm = None
                        else:
                            try:
                                cpm = float(cpm_str.replace(",", "."))
                            except Exception:
                                cpm = None
                            oee = 100.0
                    else:
                        cpm = None
                        oee = None

                    ctoferta_rows.append({
                        'num_oferta': ref_id,
                        'centretreball': ct_val_clean,
                        'descripcio': d_val,
                        'cicles': cpm,
                        'oee': oee
                    })
                    ct_count += 1

            tract_count = 0 # Count tractaments for this oferta (externalized processes)
            if (
                tract_df is not None
                and not tract_df.empty
                and 'num_oferta' in tract_df.columns
            ):
                tract_count = tract_df[tract_df['num_oferta'] == ref_id].shape[0]

            oferta_rows.append({
                'num_oferta': ref_id,
                'num_processos': ct_count + tract_count,
                'id_referencia_client': self.ref_project,
                'num_escandall': ref_id,
                'id_client': self.client.capitalize() if isinstance(self.client, str) else self.client
            })

        oferta_df = pd.DataFrame(oferta_rows)
        ctoferta_df = pd.DataFrame(ctoferta_rows)

        #print(f"Oferta: \n {oferta_df} \n")
        #print(f"Oferta_ct: \n {ofertact_df} \n")

        oferta_out_csv = f"{self.ref_project}_oferta.csv"
        ctoferta_out_csv = f"{self.ref_project}_ctoferta.csv"
        
        oferta_df.to_csv(oferta_out_csv, index=False)
        ctoferta_df.to_csv(ctoferta_out_csv, index=False)
        
        #print(f"DataFrame processed and saved to: {oferta_out_csv}, {ofertact_out_csv} and {ctoferta_out_csv} \n")

        return oferta_df, ctoferta_df
    
    
    def _get_column_or_alternative(self, df, primary, alternative):
        """Retorna la millor columna disponible entre la primària i l’alternativa"""
        if primary in df.columns:
            return df[primary]
        elif alternative in df.columns:
            return df[alternative]
        else:
            return pd.Series([""] * len(df))


    def info_matriu(self, dg):
        """Transforma informació de matriu del datasheet"""

        col_bbdd_mt = [
            'nom_matriu', 'num_picades', 'volum_anual', 'volum_projecte',
            'cavitats', 'responsable', 'matricer']

        # Definim parelles de columnes: versió original i alternativa (v2)
        column_map = {
            '1 - Nº Matriu:': '1 - Nº Matriu:',
            '4 - Tool Lifetime': '4 - Tool Lifetime',
            '5 - Volum Anual:': '5 - Quantitat Anual:',
            '6 - Volum total Projecte:': '6 - Quantitat Total Projecte:',
            '8 - Cavitats:': '8 - Cavitats:',
            '14 - Responsable Projecte:': '14 - Responsable Projecte:',
            '9 - Matricer:': '9 - Matricer:'}

        extracted_columns = []

        for col, alt_col in column_map.items():
            extracted_col = self._get_column_or_alternative(dg, col, alt_col)
            
            # Si és la columna de cavitats, extraiem el valor amb la funció dedicada
            if col == '8 - Cavitats:':
                extracted_col = extracted_col.apply(self.extract_cavitats)

            extracted_columns.append(extracted_col)

        # Construcció del DataFrame final
        matriu_df = pd.concat(extracted_columns, axis=1)
        matriu_df.columns = col_bbdd_mt

        out_csv = f"{self.ref_project}_matriu.csv"
        matriu_df.to_csv(out_csv, index=False)

        return matriu_df


    def info_client(self, dg):
        col_bbdd_cl = ['id_client', 'nom_contacte']  # 'email_contacte'
        cols = ['1 - Client:', 'RESPONSABLE COMPRES CLIENT']
        cols_v2 = ['22 - Client:', 'RESPONSABLE COMPRES CLIENT']
        
        # Check which version of columns exist
        versio_2 = False
        for i, col in enumerate(cols):
            if col not in dg.columns:
                v2_col = cols_v2[i] # Check if the corresponding v2 column exists
                if v2_col in dg.columns:
                    dg[col] = dg[v2_col]
                    versio_2 = True
                else:
                    dg[col] = ""
                    
        if versio_2:
            client_df = dg[cols_v2].copy()
        else:
            client_df = dg[cols].copy()
        
        client_df.columns = col_bbdd_cl

        # Set id_client to the variable client
        client_df['id_client'] = self.client
        #print(f"Client: \n {client_df} \n")
        
        out_csv = f"{self.ref_project}_client.csv"
        client_df.to_csv(out_csv, index = False)
        #print(f"DataFrame processed and saved to: {out_csv} \n")
        
        return client_df


    def info_material(self, dg):
        """Transforma informació de material del datasheet"""

        col_bbdd_mtl = ['id_material', 'dimensiox', 'dimensioy',
                        'dimensioz', 'proveidor', 'pes', 'preu']

        # Mapeig entre columna principal i la seva alternativa v2
        column_map = {
            '1 - Descripció material:': '15 - Descripció material:',
            'BANDA': 'BANDA',
            'PAS': 'PAS',
            'GRUIX': 'GRUIX',
            '3 - Proveïdor:': '17 - Proveïdor:',
            '7 - Pes estimat del Rull:': '21 - Pes estimat del Rull:',
            '4 - Preu actualitzat:': '18 - Preu actualitzat:'}

        # Extracció automàtica de dimensions si cal
        for full_column in ['2 - Mides (BANDA x PAS x GRUIX):', '16 - Mides (BANDA x PAS x GRUIX):']:
            if full_column in dg.columns:
                parts = dg[full_column].str.split('x', expand=True)
                if parts.shape[1] == 3:
                    dg['BANDA'] = parts[0].str.strip().str.replace(',', '.', regex=False)
                    dg['PAS'] = parts[1].str.strip().str.replace(',', '.', regex=False)
                    dg['GRUIX'] = parts[2].str.strip().str.replace(',', '.', regex=False)

        extracted_columns = []

        for col, alt_col in column_map.items():
            col_data = self._get_column_or_alternative(dg, col, alt_col)

            # Neteja específica per a la columna del pes
            if col in ['7 - Pes estimat del Rull:', '21 - Pes estimat del Rull:']:
                col_data = (
                    col_data.astype(str)
                    .str.extract(r'(\d+)')[0]
                    .fillna(0)
                    .astype(int)
                )

            extracted_columns.append(col_data)

        # Construcció del DataFrame final
        material_df = pd.concat(extracted_columns, axis=1)
        material_df.columns = col_bbdd_mtl

        out_csv = f"{self.ref_project}_material.csv"
        material_df.to_csv(out_csv, index=False)

        return material_df


    def info_escandalloferta(self, dg):
        col_bbdd_eo = ['num_escandall', 'preuvenda']

        eo_cols = ['13 - Nº Expedient:', '17 - Preu Peça (Oferta a Client)']
        
        for col in eo_cols:
            if col not in dg.columns:
                dg[col] = ""
        
        escandalloferta_df = dg[eo_cols].copy()
        escandalloferta_df.columns = col_bbdd_eo
        #print(f"Escandall oferta: \n {escandalloferta_df} \n")
        
        out_csv = f"{self.ref_project}_escandalloferta.csv"
        escandalloferta_df.to_csv(out_csv, index = False)
        #print(f"DataFrame processed and saved to: {out_csv} \n")
        
        return escandalloferta_df


    def info_escandallofertatecnics(self, dg):
        col_bbdd_eo = ['num_escandall', 'num_tecnic']

        eo_cols = ['13 - Nº Expedient:', 'RESPONSABLE DE PROJECTE']
        
        for col in eo_cols:
            if col not in dg.columns:
                dg[col] = ""
        
        escandallofertatecnics_df = dg[eo_cols].copy()
        escandallofertatecnics_df.columns = col_bbdd_eo
        #print(f"Escandall oferta: \n {escandalloferta_df} \n")
        
        out_csv = f"{self.ref_project}_escandallofertatecnics.csv"
        escandallofertatecnics_df.to_csv(out_csv, index = False)
        #print(f"DataFrame processed and saved to: {out_csv} \n")
        
        return escandallofertatecnics_df


    def info_lifetime(self, dg):
        col_bbdd_lft = ['num_oferta', 'datainici', 'datafinal', 'dataentregamatriu']
        cols_lft = ['13 - Nº Expedient:', 'S.O.P. CLIENT', 'E.O.P. CLIENT', '10 - Data entrega matriu:']
        dates = ['S.O.P. CLIENT', 'E.O.P. CLIENT', '10 - Data entrega matriu:']  # Define the date columns

        for column in dates:
            if column in dg.columns:
                dg[column] = dg[column].apply(self.cw_date)
                dg[column] = pd.to_datetime(dg[column], errors='coerce')
                dg[column] = dg[column].where(dg[column].notna(), None)

        for col in cols_lft:
            if col not in dg.columns:
                dg[col] = None

        lifetime_df = dg[cols_lft].copy()
        lifetime_df.columns = col_bbdd_lft

        out_csv = f"{self.ref_project}_lifetime.csv"
        lifetime_df.to_csv(out_csv, index=False)

        return lifetime_df

        
    def info_tractaments(self, dg):
        # Define the columns for each tractament
        tractament_cols = [
            '* Descripció complerta del tractament 1:',
            '* Descripció complerta del tractament 2:',
            '* Descripció complerta del tractament 3:'
        ]
        proveidor_cols = [
            '* proveïdor SQB:',
            '* proveïdor SQB:.1',
            '* proveïdor SQB:.2'
        ]
        preu_cols = [
            '* preu SQB:',
            '* preu SQB:.1',
            '* preu SQB:.2'
        ]

        for col in tractament_cols + proveidor_cols + preu_cols:
            if col not in dg.columns:
                dg[col] = None

        def is_empty(val):
            return pd.isnull(val) or str(val).strip() == "" or str(val).strip() == "0" or str(val).strip() == "0.0"

        rows = []
        for idx, row in dg.iterrows():
            ordre = row.get('13 - Nº Expedient:', None)
            for i in range(3):
                desc = row[tractament_cols[i]]
                prov = row[proveidor_cols[i]]
                preu = row[preu_cols[i]]
                # Only add if at least one field is not empty and not "0"
                if not (is_empty(desc) and is_empty(prov) and is_empty(preu)):
                    rows.append({
                        #'num_oferta': ordre,
                        'ordre': i + 1,
                        'descripcio': desc,
                        'proveidor': prov,
                        'preu': preu,
                        'id_referencia_client': self.ref_project
                    })
        tractaments_df = pd.DataFrame(rows)   
        #print(f"Tractaments: \n {tractaments_df} \n")
        
        out_csv = f"{self.ref_project}_tractaments.csv"
        tractaments_df.to_csv(out_csv, index = False)
        #print(f" DataFrame processed and saved to: {out_csv} \n")
        
        return tractaments_df


    def info_produccio(dg):
        # Define the possible columns for matriu and material
        matriu_cols = ['1 - Nº Matriu:']
        material_cols = ['1 - Descripció material:']

        # Check for v2 columns if needed
        if '15 - Descripció material:' in dg.columns:
            material_cols = ['15 - Descripció material:']
        if '1 - Nº Matriu:' not in dg.columns and '1 - Nº Matriu:' in dg.columns:
            matriu_cols = ['1 - Nº Matriu:']

        # Build the DataFrame
        produccio_df = pd.DataFrame({
            'id_referencia_client': ref_project,
            'id_matriu': dg[matriu_cols[0]],
            'id_material': dg[material_cols[0]]
        })

        #print(f"Producció: \n {produccio_df} \n")
        
        out_csv = f"{ref_project}_produccio.csv"
        produccio_df.to_csv(out_csv, index=False)
        #print(f"DataFrame processed and saved to: {out_csv}\n")

        return produccio_df

    
    def info_part(dg):
        # Define the output column names
        col_bbdd_pt = [
            'nom_client', 'planta', 'nom_projecte', 'facturacio',
            'quantitats', 'descripcio', 'costos', 'pes',
            'id_tipus', 'id_embalatge', 'id_tractament', 'id_referencia_client'
        ]
        # Define the input column names (matching your CSV structure)
        part_cols = [
            '1 - Client:', '2 - Tipus:  SQB / KSW / MIXTE:', '11 - Projecte:', '3 - Tipus Facturació: A / B / C:',
            'LOT PRODUCCIÓ INFORMAT A CLIENT', '6 - Descripció actualitzada:',
            '16 - Cost Peça (Intern SOME)', '13 - Pes Net:', '12 - Jerarquía:'
        ]

        part_cols_v2 = [
            '22 - Client:', '23 - Tipus:  SQB / KSW / MIXTE:', '11 - Projecte:', '24 - Tipus Facturació: A / B / C:',
            'LOT PRODUCCIÓ INFORMAT A CLIENT', '26 - Descripció actualitzada:',
            '33 - Cost Peça (Intern SOME)', '30 - Pes Net:', '12 - Jerarquía:'
        ]

        # Decide which set of columns to use based on existence
        use_v2 = all(col in dg.columns for col in part_cols_v2)

        # If neither set is fully present, fill missing columns with default values
        if use_v2:
            selected_cols = part_cols_v2
        else:
            selected_cols = part_cols

        for col in selected_cols:
            if col not in dg.columns:
                # Use 0 for numeric-like columns, else empty string
                if any(word in col.lower() for word in ['cost', 'pes', 'quantitat', 'jerarquia']):
                    dg[col] = 0
                else:
                    dg[col] = ""

        # Assign planta if possible
        planta_col = None
        if '2 - Tipus:  SQB / KSW / MIXTE:' in dg.columns:
            planta_col = '2 - Tipus:  SQB / KSW / MIXTE:'
        elif '23 - Tipus:  SQB / KSW / MIXTE:' in dg.columns:
            planta_col = '23 - Tipus:  SQB / KSW / MIXTE:'

        if planta_col:
            def assign_plant(value):
                try:
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
                except Exception:
                    return 1000
            dg[planta_col] = dg[planta_col].apply(assign_plant)

        try:
            part_df = dg[selected_cols].copy()
        except Exception:
            # If there's a problem, return a DataFrame with zeros/None
            part_df = pd.DataFrame([{k: 0 if 'cost' in k or 'pes' in k or 'quantitat' in k else None for k in col_bbdd_pt}])
            
        part_df['id_embalatge'] = None
        part_df['id_tractament'] = None  # Leave id_tractament as None/blank/null
        part_df['id_referencia_client'] = ref_project  # Add the reference project column

        # Rename columns to output names (truncate if needed)
        try:
            part_df.columns = col_bbdd_pt
        except Exception:
            part_df = part_df.iloc[:, :len(col_bbdd_pt)]
            part_df.columns = col_bbdd_pt

        #print(f"Part: \n{part_df}\n")

        out_csv = f"{ref_project}_part.csv"
        part_df.to_csv(out_csv, index=False)
        #print(f"DataFrame processed and saved to: {out_csv}\n")

        return part_df
        

    def info_planol(dg):
        pl_col = '15 - Plànol actualitzat'
        # If the column does not exist, create it with empty values
        if pl_col not in dg.columns:
            dg[pl_col] = ""

        # If all values are empty or NaN, fill with ref_project
        if dg[pl_col].isnull().all() or (dg[pl_col] == "").all():
            dg[pl_col] = ref_project

        # If some values are empty, fill those with ref_project
        dg[pl_col] = dg[pl_col].replace("", ref_project)
        dg[pl_col] = dg[pl_col].fillna(ref_project)

        planol_df = pd.DataFrame({
            'num_planol': dg[pl_col],
            'id_referencia_client': ref_project
        })

        out_csv = f"{ref_project}_planol.csv"
        planol_df.to_csv(out_csv, index=False)
        #print(f"DataFrame processed and saved to: {out_csv}\n")

        return planol_df


    def info_tipus(dg):
        # Ensure the required columns exist
        if '12 - Jerarquía:' not in dg.columns:
            dg['12 - Jerarquía:'] = ""
        # Prefer '6 - Descripció actualitzada:', fallback to '26 - Descripció actualitzada:'
        if '6 - Descripció actualitzada:' in dg.columns:
            descripcio_col = '6 - Descripció actualitzada:'
        elif '26 - Descripció actualitzada:' in dg.columns:
            descripcio_col = '26 - Descripció actualitzada:'
        else:
            dg['6 - Descripció actualitzada:'] = ""
            descripcio_col = '6 - Descripció actualitzada:'

        tipus_df = pd.DataFrame({
            'id_tipus': dg['12 - Jerarquía:'],
            'descripcio': dg[descripcio_col],
            'id_referencia_client': ref_project
        })

        out_csv = f"{ref_project}_tipus.csv"
        tipus_df.to_csv(out_csv, index=False)
        #print(f"DataFrame processed and saved to: {out_csv}\n")

        return tipus_df
        
# Other methods (info_oferta, info_matriu, etc.) would follow similar pattern