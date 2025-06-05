import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import seaborn as sns
import pandas as pd
import os

output_dir = r'C:\Github\PythonTecnica_SOME'
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------ Constants and Style Setup ------------------------------------------ #
font_name = 'Times new roman'
vermell = "#830B0B"
verd = "#156315"
blau = "#1f77b4"
negre = "#000000"
gold_r = (1 + np.sqrt(5)) / 2 
save = False  # Save plots?
display = True  # Show plots?
np.random.seed(42)

# ------------------------------------------ Sample Data (for now, hardcoded) ------------------------------------------ #
def get_sample_data():
    # Example: 4 elements, 5 values each
    data = [
        {'Element': 'Dimensio_1', 'Nominal': 10.0, 'Tol-': -0.1, 'Tol+': 0.2, 'Values': [10.01, 9.98, 10.05, 10.00, 10.02]},
        {'Element': 'Dimensio_2', 'Nominal': 5.0, 'Tol-': -0.05, 'Tol+': 0.05, 'Values': [5.01, 4.99, 5.00, 5.02, 4.98]},
        {'Element': 'Dimensio_3.1', 'Nominal': 24.9, 'Tol-': -0.15, 'Tol+': 0.5, 'Values': [25.19, 25.24, 25.28, 25.21, 25.31]},
        {'Element': 'Dimensio_3.2', 'Nominal': 24.9, 'Tol-': -0.15, 'Tol+': 0.5, 'Values': [25.41, 25.49, 25.38, 25.33, 25.45]},
        {'Element': 'Dimensio_4', 'Nominal': 0, 'Tol-': 0, 'Tol+': 0.5, 'Values': [0.423, 0.394, 0.411, 0.402, 0.386]}
    ]
    return pd.DataFrame(data)

# ------------------------------------------ Statistical Analysis ------------------------------------------ #
def analyze_sample(sample_data):
    mu = np.mean(sample_data)
    std = np.std(sample_data, ddof=1)
    shapiro_test = stats.shapiro(sample_data)
    ks_test = stats.kstest(sample_data, 'norm', args=(mu, std))
    ad_test = stats.anderson(sample_data, dist='norm')
    if len(sample_data) >= 8:
        dagostino_test = stats.normaltest(sample_data)
        dagostino_ok = dagostino_test.pvalue > 0.05
    else:
        dagostino_test = None
        dagostino_ok = np.nan

    normality_checks = {
        "Shapiro-Wilk": shapiro_test.pvalue > 0.05,
        "Kolmogorov-Smirnov": ks_test.pvalue > 0.05,
        "Anderson-Darling": ad_test.statistic < ad_test.critical_values[2],
        "D'Agostino's K²": dagostino_ok
    }

    is_normal = all([v for v in normality_checks.values() if not pd.isna(v)])
    print(is_normal)
    print(f"Mu: {mu:.4f}, Std: {std:.4f}, Normality Checks: {normality_checks}")
    return mu, std, normality_checks, is_normal

# ------------------------------------------ Plot Histogram & Q-Q Plot ------------------------------------------ #
def plt_sample_analysis(sample_data, nominal_value, tolerance, element_name, sv=True, dsp=False):
    kde_kwargs = {"fill": True, "linewidth": 1}
    (osm, osr), (slope, intercept, r) = stats.probplot(sample_data, dist="norm")

    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    sns.histplot(sample_data, kde=True, color=blau, edgecolor=negre, **kde_kwargs)
    plt.axvline(nominal_value + tolerance[0], color=vermell, linestyle='--', linewidth=1, label=f'Límit inferior ({nominal_value + tolerance[0]:.2f})')
    plt.axvline(nominal_value + tolerance[1], color=vermell, linestyle='--', linewidth=1, label=f'Límit superior ({nominal_value + tolerance[1]:.2f})')
    plt.axvline(nominal_value, color=verd, linestyle='--', linewidth=1, label=f'Valor nominal ($x_0$={nominal_value:.2f})')
    plt.title(f'Histograma de la mostra - {element_name}', fontsize=14, fontname=font_name)
    plt.xlabel('Valor', fontsize=11, fontname=font_name)
    plt.ylabel('Freqüència', fontsize=11, fontname=font_name)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=10, prop={'family': font_name})

    plt.subplot(1, 2, 2)
    plt.plot(osm, slope * np.array(osm) + intercept, color=vermell, linewidth=2, label=fr'Ajust lineal (R² = {r**2:.3f})')
    plt.scatter(osm, osr, color=blau, edgecolor='k', linewidths=0.5, s=50, label='Dades')
    plt.title(f'Q-Q Plot - {element_name}', fontsize=14, fontname=font_name)
    plt.xlabel('Quantils teòrics', fontsize=11, fontname=font_name)
    plt.ylabel('Quantils de la mostra', fontsize=11, fontname=font_name)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=10, prop={'family': font_name})
    plt.tight_layout()
    if sv:
        filename = os.path.join(output_dir, f'{element_name}_normalitat.svg')
        plt.savefig(filename, format='svg')
    if dsp:
        plt.show()

# ------------------------------------------ Generate Synthetic Data and Plot ------------------------------------------ #
def ext_sample(mu, std, n_vals=100, non_negative=False):
    if non_negative:
        samples = []
        while len(samples) < n_vals:
            val = np.random.normal(mu, std)
            if val >= 0:
                samples.append(val)
        return np.array(samples)
    else:
        return np.random.normal(mu, std, n_vals)

# ------------------------------------------ Plot with the extrapolated values ------------------------------------------ #
def plt_extrapolated_sample(ext_dt, nom_vl, tol, mu, std, element_name, sv=True, dsp=False):
    xmin, xmax = min(ext_dt), max(ext_dt)
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mu, std)

    plt.figure(figsize=(10, 10 / gold_r))
    plt.hist(ext_dt, bins=30, density=False, alpha=0.6, color=blau, edgecolor='k', label='Dades extrapolades')
    plt.plot(x, p * len(ext_dt) * (xmax - xmin) / 30, negre, linewidth=1,
             label=fr'$\bar{{x}}$ = {mu:.4f}     $\sigma$ = {std:.4f}')
    plt.axvline(nom_vl + tol[0], color=vermell, linestyle='--', linewidth=1, label=f'Límit inferior: ({nom_vl + tol[0]:.2f})')
    plt.axvline(nom_vl + tol[1], color=vermell, linestyle='--', linewidth=1, label=f'Límit superior: ({nom_vl + tol[1]:.2f})')
    plt.axvline(nom_vl, color=verd, linestyle='--', linewidth=1, label=fr'Valor nominal: $x_0$ = {nom_vl:.2f}')
    plt.fill_between(x, 0, p * len(ext_dt) * (xmax - xmin) / 30,
                     where=(x < nom_vl + tol[0]) | (x > nom_vl + tol[1]),
                     color="#fca4a4", alpha=0.4)

    plt.xlabel('Mesures de cotes', fontsize=14, fontname=font_name)
    plt.ylabel('Freqüència', fontsize=14, fontname=font_name)
    plt.title(f'Distribució de mesures - {element_name}', fontsize=16, fontname=font_name)
    plt.legend(fontsize=12, prop={'family': font_name})
    plt.grid(True)
    plt.tight_layout()
    if sv:
        filename = os.path.join(output_dir, f'{element_name}_extrapolada.svg')
        plt.savefig(filename, format='svg')
    if dsp:
        plt.show()

# ------------------------------------------ Main ------------------------------------------ #
def main(n_vals=100):
    os.makedirs(output_dir, exist_ok=True)  # Crear carpeta si no existeix

    # For now, use hardcoded sample data
    df = get_sample_data()

    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        nominal = row['Nominal']
        tolerance = [row['Tol-'], row['Tol+']]
        sample_data = np.array(row['Values'], dtype=float)

        mu, std, _, _ = analyze_sample(sample_data)

        # Gràfics d’anàlisi
        plt_sample_analysis(sample_data, nominal, tolerance, element, save, display)

        # Decide if extrapolation is needed
        if len(sample_data) >= n_vals:
            final_values = sample_data[:n_vals]
        else:
            # Condició per evitar extrapolació negativa
            non_negative = (nominal == 0 and tolerance[0] == 0)
            final_values = ext_sample(mu, std, n_vals=n_vals, non_negative=non_negative)

        # Gràfic d’extrapolació
        plt_extrapolated_sample(final_values, nominal, tolerance, mu, std, element, save, display)

        # Save to CSV
        out_csv = os.path.join(output_dir, f"{element}_extrapolated.csv")
        pd.DataFrame({'Extrapolated_Value': final_values}).to_csv(out_csv, index=False)

if __name__ == "__main__":
    # You can change n_vals here (e.g., 30, 50, 100, 500)
    main(n_vals=1000)
