import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import scipy.stats as stats
import seaborn as sns
import pandas as pd
import os

output_dir = r'C:\Github\PythonTecnica_SOME\diemnsional'
os.makedirs(output_dir, exist_ok=True)
save = False  # Set to True to save plots, False to skip saving
display = True  # Set to True to display plots, False to skip displaying
green = "#228B22"
vermell_clar = "#D14D4D"
blue = "#003366"
vermell = "#B22222"

# ------------------------------------------ Sample Data (for now, hardcoded) ------------------------------------------ #
def get_sample_data():
    # Example: 4 elements, 5 values each
    data = [
    # Non-normal distribution (bimodal)
    {'Element': 'Dimensio_Anomaly', 'Nominal': 30.0, 'Tol-': -0.15, 'Tol+': 0.15,
     'Values': [30.17, 29.88, 30.16, 29.84, 30.19]},
    # Linear dimension (normal case)
    {'Element': 'Dimensio_1', 'Nominal': 25.0, 'Tol-': -0.2, 'Tol+': 0.2,
     'Values': [25.03, 24.97, 25.04, 24.96, 25.04]},
    # Traction test (one-sided tolerance, only minimum required)
    {'Element': 'Traccio_1', 'Nominal': 18000, 'Tol-': 0, 'Tol+': 50000,
     'Values': [18750, 20200, 19500, 18900, 20000, 19300]},
    # Diameter (tight tolerance)
    {'Element': 'Diameter_1', 'Nominal': 12.5, 'Tol-': -0.05, 'Tol+': 0.05,
     'Values': [12.48, 12.52, 12.50, 12.47, 12.51]},
    # Angle (in degrees)
    {'Element': 'Angle_1', 'Nominal': 90.0, 'Tol-': -1.0, 'Tol+': 1.0,
     'Values': [89.8, 90.1, 90.0, 89.9, 90.2]},
    # GD&T - flatness (unilateral tolerance)
    {'Element': 'Flatness_1', 'Nominal': 0.0, 'Tol-': 0.0, 'Tol+': 0.2,
     'Values': [0.05, 0.12, 0.09, 0.07, 0.11]},
    # Linear dimension with asymmetric tolerance
    {'Element': 'Dimensio_2', 'Nominal': 50.0, 'Tol-': -0.3, 'Tol+': 0.1,
     'Values': [49.85, 49.90, 50.05, 49.95, 50.08]},
    # GD&T - position tolerance
    {'Element': 'Position_1', 'Nominal': 0.0, 'Tol-': 0.0, 'Tol+': 0.15,
     'Values': [0.14, 0.10, 0.18, 0.12, 0.16]}]
    
    mesures = pd.DataFrame(data) #print(f"DataFrame with sample data:\n{mesures}")
    
    return mesures


def verify_data(mesures):
    # Check if all elements have at least 5 values
    for i, row in mesures.iterrows():
        if len(row['Values']) < 5:
            raise ValueError(f"Element {row['Element']} does not have at least 5 values.")
    # Check if all nominal values are numeric
    if not np.issubdtype(mesures['Nominal'].dtype, np.number):
        raise ValueError("Nominal values must be numeric.")
    # Check if all tolerance values are numeric
    if not np.issubdtype(mesures['Tol-'].dtype, np.number) or not np.issubdtype(mesures['Tol+'].dtype, np.number):
        raise ValueError("Tolerance values must be numeric.")
    
    return True


def dimensional_analysis(mesures):
    if verify_data(mesures) is not True:
        raise ValueError("Data verification failed. Please check the input data.")
    else:
        # Perform dimensional analysis on the sample data
        results = []
        
        for i, row in mesures.iterrows():
            nominal = row['Nominal']
            tol_minus = row['Tol-']
            tol_plus = row['Tol+']
            values = np.array(row['Values'])
            
            mean = np.mean(values)
            std_dev = np.std(values, ddof=1)
            min_val = np.min(values)
            max_val = np.max(values)
            
            results.append({
                'Element': row['Element'],
                'Mean': mean,
                'StdDev': std_dev,
                'Min': min_val,
                'Max': max_val,
                'InTolerance': (min_val >= (nominal + tol_minus)) and (max_val <= (nominal + tol_plus))
            })
        
    return pd.DataFrame(results)


def plot_dimension_bars(element, values, nominal, tol_minus, tol_plus, output_dir):
    """
    Plots and saves a bar chart for a single dimension.
    """
    LSL = nominal + tol_minus
    USL = nominal + tol_plus
    indices = range(1, len(values) + 1)
    bar_colors = [blue if LSL <= v <= USL else vermell_clar for v in values]
    edge_colors = ['black'] * len(values)

    plt.figure(figsize=(7, 4))
    plt.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.5, zorder=0)
    plt.bar(
        indices,
        [v - nominal for v in values],
        bottom=nominal,
        color=bar_colors,
        edgecolor=edge_colors,
        width=0.2,
        linewidth=0.5,
        zorder=2
    )
    plt.axhline(LSL, color=vermell, linestyle='-', linewidth=0.5, zorder=3)
    plt.axhline(USL, color=vermell, linestyle='-', linewidth=0.5, zorder=3)
    plt.axhline(nominal, color=green, linestyle='-.', linewidth=0.5, zorder=3)
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
    for i, row in mesures.iterrows():
        plot_dimension_bars(
            element=row['Element'],
            values=row['Values'],
            nominal=row['Nominal'],
            tol_minus=row['Tol-'],
            tol_plus=row['Tol+'],
            output_dir=output_dir
        )
    print(dimensional_analysis(mesures))


if __name__ == "__main__":
    main()
