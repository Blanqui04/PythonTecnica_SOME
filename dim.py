import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from from_sql import build_analysis_data, cerca_dim

output_dir = r'C:\Github\PythonTecnica_SOME\diemnsional'
os.makedirs(output_dir, exist_ok=True)
save = False  # Set to True to save plots, False to skip saving
display = False  # Set to True to display plots, False to skip displaying

green = "#228B22"
vermell_clar = "#D14D4D"
blue = "#003366"
vermell = "#B22222"

ref_client = '666429400'
batch_number = '1255455'  # Replace with real batch number as needed
dec = 4  # Change this for all rounding

# ------------------------------------------ Sample Data (for now, hardcoded) ------------------------------------------ #
def get_sample_data():
    df = cerca_dim(ref_client)
    if not df.empty:
        data = build_analysis_data(df, ref_client, batch_number)
        return pd.DataFrame(data)
    print("Error: No s'han trobat dades vàlides a la base de dades per a l'anàlisi de capacitat.")
    print(f"Detall del DataFrame rebut: files={df.shape[0]}, columnes={df.shape[1]}")
    print("Comprova la connexió, la consulta SQL, o que existeixin mesures per aquest client i batch.")
    return pd.DataFrame()


def verify_data(mesures):
    if (mesures['Values'].apply(len) < 5).any():
        raise ValueError("All elements must have at least 5 values.")
    if not np.issubdtype(mesures['Nominal'].dtype, np.number):
        raise ValueError("Nominal values must be numeric.")
    if not np.issubdtype(mesures['Tol-'].dtype, np.number) or not np.issubdtype(mesures['Tol+'].dtype, np.number):
        raise ValueError("Tolerance values must be numeric.")
    return True


def round_val(val, decimals=dec):
    return round(float(val), decimals)


def dimensional_analysis(mesures):
    verify_data(mesures)
    results = []
    for _, row in mesures.iterrows():
        values = np.array(row['Values'][:5])
        classe_raw = row.get('Classe', '')
        if isinstance(classe_raw, (list, np.ndarray, pd.Series)):
            classe_raw = classe_raw[0] if len(classe_raw) > 0 else ''
        if pd.isnull(classe_raw):
            classe_raw = ''
        classe = classe_raw if classe_raw in ('CC', 'SC') else ''
        min_val, max_val = np.min(values), np.max(values)
        mean, std_dev = np.mean(values), np.std(values, ddof=1)
        nominal, tol_minus, tol_plus = row['Nominal'], row['Tol-'], row['Tol+']
        in_tol = (min_val >= (nominal + tol_minus)) and (max_val <= (nominal + tol_plus))
        results.append({
            'Item': row['Element'],
            'Classe': classe,
            'Descripcio': row.get('Descripcio', ''),
            'Nominal': round_val(nominal),
            'Tol-': round_val(tol_minus),
            'Tol+': round_val(tol_plus),
            'M1': round_val(values[0]),
            'M2': round_val(values[1]),
            'M3': round_val(values[2]),
            'M4': round_val(values[3]),
            'M5': round_val(values[4]),
            'Min': round_val(min_val),
            'Max': round_val(max_val),
            'Mean': round_val(mean),
            'StdDev': round_val(std_dev),
            'Check': "OK" if in_tol else "NOT OK"
        })
    return pd.DataFrame(results)


def plot_dimension_bars(element, values, nominal, tol_minus, tol_plus, output_dir):
    LSL, USL = nominal + tol_minus, nominal + tol_plus
    indices = range(1, len(values) + 1)
    bar_colors = ["#003366" if LSL <= v <= USL else "#D14D4D" for v in values]
    plt.figure(figsize=(7, 4))
    plt.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.5, zorder=0)
    plt.bar(indices, [v - nominal for v in values], bottom=nominal, color=bar_colors,
            edgecolor='black', width=0.2, linewidth=0.5, zorder=2)
    plt.axhline(LSL, color="#B22222", linestyle='-', linewidth=0.5, zorder=3)
    plt.axhline(USL, color="#B22222", linestyle='-', linewidth=0.5, zorder=3)
    plt.axhline(nominal, color="#228B22", linestyle='-.', linewidth=0.5, zorder=3)
    plt.title(f"{element}", fontsize=13)
    plt.ylabel('Valor', fontsize=11)
    plt.xlabel('Nº Peça', fontsize=11)
    plt.xticks(indices)
    plt.tick_params(axis='both', which='major', labelsize=10)
    plt.tight_layout()
    if save:
        filename = os.path.join(output_dir, f"{element}_barplot.png")
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved plot for {element} to {filename}")
    if display:
        plt.show()
    plt.close()


def main():
    plt.rcParams["font.family"] = "Times New Roman"
    mesures = get_sample_data()
    verify_data(mesures)
    for _, row in mesures.iterrows():
        plot_dimension_bars(
            element=row['Element'],
            values=row['Values'],
            nominal=row['Nominal'],
            tol_minus=row['Tol-'],
            tol_plus=row['Tol+'],
            output_dir=output_dir
        )
    results = dimensional_analysis(mesures)
    out_csv = os.path.join(output_dir, "dimensional_analysis_clean.csv")
    results.to_csv(out_csv, index=False)
    print(f"\nSaved clean dimensional analysis to {out_csv}\n")
    return results


if __name__ == "__main__":
    main()
