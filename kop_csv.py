import os
import openpyxl
import warnings
import pandas as pd

""" Script per extreure l'informació de l'arxiu de l'excel del departament comercial KOP,
    passar-la a SQL per la base de dades de projectes del departament tècnic.
"""
warnings.filterwarnings("ignore", category=UserWarning)

master_folder = r'\\server\SOME\Projectes en curs'
adress_kop = r'5-FOLLOW-UP\1-KOP'
csv_folder = r'C:\Github\PythonTecnica_SOME\dades_escandall_csv'
datasheets_folder = r'C:\Github\PythonTecnica_SOME\datasheets_csv'

client = 'ZF'                           # Nom del client a cercar
ref_project = '004938000151'            # Referència del projecte a cercar

def trobar_arxiu_excel(client, ref_project):
    """
    Funció per cercar l'arxiu Excel (KOP) a client especificat
    dins la carpeta del projecte que contingui la referència especificada.
    Ara també accepta arxius .xlsm (amb macros).
    """
    client_folder = os.path.join(master_folder, client) # Construir la ruta del client
        
    for root, dirs, files in os.walk(client_folder):    # Cercar la carpeta del projecte que contingui la referència especificada
        for dir in dirs:
            if ref_project in dir:
                kop_folder = os.path.join(root, dir, adress_kop)            # Construir la ruta completa del projecte              
                for sub_root, sub_dirs, sub_files in os.walk(kop_folder):   # Cercar l'arxiu Excel dins la carpeta del projecte
                    for file in sub_files:
                        if file.endswith(('.xlsx', '.xls', '.xlsm')):
                            excel_path = os.path.join(sub_root, file)
                            print(f"Arxiu Excel trobat: \n{excel_path} \n")
                            return excel_path
    return None


def dades_kop(xlsx_path):
    """ 
    Funció per extreure les dades necessàries de l'arxiu KOP en format .csv
    """
    # Carrega l'arxiu Excel
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)  # data_only=True per obtenir els valors calculats

    # Desprotegeix els fulls
    for shit_name in ['ESTRUCTURA', 'Entrada Dades - Extres']:
        if shit_name in wb.sheetnames:
            wb[shit_name].protection.sheet = False

    # Guarda l'arxiu temporalment
    temp_path_1 = 'temp_unprotected.xlsx'
    temp_path_2 = 'temp_estructura.csv'
    temp_path_3 = 'temp_dades.csv'

    wb.save(temp_path_1)
    df_estructura = pd.read_excel(temp_path_1, sheet_name='ESTRUCTURA')         # Llegeix els fulls especificats amb pandas
    df_dades = pd.read_excel(temp_path_1, sheet_name='Entrada Dades - Extres')  # Llegeix els fulls especificats amb pandas
    df_estructura.to_csv(temp_path_2, index=False)                              
    df_dades.to_csv(temp_path_3, index=False)   
    
    return temp_path_2, temp_path_3


def tractar_estructura(csv_estructura):
    """
    Funció per netejar el CSV generat de l'estructura, qudant-nos amb les dades importants del full.
    """
    df = pd.read_csv(csv_estructura, header=None)   # Read the CSV file without headers

    # Drop completely empty rows and columns
    df.dropna(how='all', inplace=True)              # Drop rows where all elements are NaN
    df.dropna(how='all', axis=1, inplace=True)      # Drop columns where all elements are NaN
    df.reset_index(drop=True, inplace=True)         # Reset the index of the DataFrame
    
    cleaned_data = []
    for _, row in df.iterrows():                # Iterate through each row of the DataFrame
        filtered_row = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() != '']    # Filter out NaN and empty values, but keep 0
        if len(filtered_row) > 2:
            filtered_row = filtered_row[:2]     # Keep only the first 2 columns if more data exists
        cleaned_data.append(filtered_row)

    csv_post_estructura = os.path.join(csv_folder, fr"estructura {client} {ref_project}.csv")   # Path for the cleaned structure CSV
    
    cleaned_df = pd.DataFrame(cleaned_data)                             # Create a new DataFrame with the cleaned data
    cleaned_df.to_csv(csv_post_estructura, index=False, header=False)   # Save the cleaned data to a new CSV file


def tractar_dades_extra(csv_dades_extra):
    """
    Funció per netejar el CSV generat de les dades extres, quedant-nos amb les dades importants del full.
    """
    df = pd.read_csv(csv_dades_extra, usecols=range(7), header=0)   # Read the CSV file, only the first 7 columns
    df.dropna(how='all', inplace=True)                              # Drop completely empty rows
    df = df.iloc[:, [1, 2, 5, 6]]                                   # Select the relevant columns (1, 2, 5, 6)
    df.dropna(how='all', inplace=True)                              # Drop rows where all 4 columns are NaN
    p_1 = df.iloc[:, :2].dropna(how='all')                          # Part 1: Columns B and C
    p_2 = df.iloc[:, 2:].dropna(how='all')                          # Part 2: Columns F and G

    # Rename columns for consistency
    p_1.columns = ['Key', 'Value']
    p_2.columns = ['Key', 'Value']
    
    csv_post_dades = os.path.join(csv_folder, fr'dades_extra {client} {ref_project}.csv')  # Path for the cleaned extra data CSV
    
    result = pd.concat([p_1, p_2], ignore_index=True)            # Append p_2 below p_1  
    result.to_csv(csv_post_dades, index=False, header=False)     # Save the cleaned data to a new CSV file


def combine_and_transpose_csv(csv_e, csv_d):
    """
    Funció per transposar els fitxers CSV netejats i combinar-los en un únic fitxer CSV, preparat pel datasheet.
    """
    # Llegir els fitxers CSV
    df_estr = pd.read_csv(csv_e, header=None)   # Llegir el CSV de l'estructura
    df_dades = pd.read_csv(csv_d, header=None)  # Llegir el CSV de les dades extres

    # Eliminar salts de línia i espais innecessaris de totes les cel·les
    df_estr = df_estr.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)
    df_dades = df_dades.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)

    df_est_transposed = df_estr.T                                              # Transposar les dades de l'estructura
    df_dades_transposed = df_dades.T                                           # Transposar les dades extres

    # Combinar les dades transposades
    combined_df = pd.concat([df_est_transposed, df_dades_transposed], axis=1)  # Combinar les dades transposades

    # Garantir que només hi hagi dues files al CSV combinat
    if len(combined_df) > 2:
        combined_df = combined_df.iloc[:2]  # Retallar a només dues files

    # Guardar el CSV combinat
    out = os.path.join(datasheets_folder, f'dades_escandall {client} {ref_project}.csv')    # Ruta del fitxer CSV combinat
    combined_df.to_csv(out, index=False, header=False)                                      # Guardar les dades combinades en un nou fitxer CSV
    print(f"Fitxer combinat desat a: {out}")
    return combined_df


def main():
    """
    Funció principal per executar el procés complet de tractament de dades.
    """
    os.makedirs(csv_folder, exist_ok=True)                      # Create the directory if it doesn't exist
    os.makedirs(datasheets_folder, exist_ok=True)               # Create the directory if it doesn't exist
    escandall_path = trobar_arxiu_excel(client, ref_project)    # Trobar l'arxiu Excel
    if not escandall_path:
        print("No s'ha trobat cap arxiu Excel per al client i projecte especificats!")
        return

    csv_est, csv_dds = dades_kop(escandall_path)    # Llegir l'Excel i generar els fitxers CSV temporals
    tractar_estructura(csv_est)                     # Netejar el CSV
    tractar_dades_extra(csv_dds)                    # Netejar el CSV
    csv_post_est = os.path.join(csv_folder, fr"estructura {client} {ref_project}.csv")  # Ruta del CSV (estructura) netejat
    csv_post_dds = os.path.join(csv_folder, fr"dades_extra {client} {ref_project}.csv") # Ruta del CSV (dades extra) netejat 
    
    dst = combine_and_transpose_csv(csv_post_est, csv_post_dds)                                               # Transposar i combinar els fitxers CSV netejats
    csv_datasheet = os.path.join(datasheets_folder, fr"dades_escandall {client} {ref_project}.csv")           # Ruta del CSV (datasheet) generat
    print(f"Processament complet. Fitxers generats:\n- {csv_post_est}\n- {csv_post_dds}\n- {csv_datasheet}")  # Imprimir missatge de finalització del procés
    
    os.remove(csv_est)                  # Eliminar el CSV original
    os.remove(csv_dds)                  # Eliminar el CSV original
    os.remove('temp_unprotected.xlsx')  # Eliminar el fitxer Excel temporal
    
    return csv_datasheet, dst

# Executar la funció principal només si el fitxer s'executa directament
if __name__ == "__main__":
    main()
