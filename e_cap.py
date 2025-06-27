import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import scipy.stats as stats
from scipy.special import gamma
import seaborn as sns
import pandas as pd
import os

output_dir = r'C:\Github\PythonTecnica_SOME\estudi de capacitat'
os.makedirs(output_dir, exist_ok=True)

# 

# ------------------------------------------ Sample Data (for now, hardcoded) ------------------------------------------ #
def get_sample_data():
    # Example: 4 elements, 5 values each
    data = [
    # Diameter (tight tolerance)
    {'Element': 'Diameter_1', 'Nominal': 12.5, 'Tol-': -0.05, 'Tol+': 0.05,
     'Values': [12.41, 12.46, 12.43, 12.47, 12.50, 12.49, 12.44, 12.46, 12.48, 12.48]},
    # Non-normal distribution (bimodal)
    {'Element': 'Dimensio_Anomaly', 'Nominal': 30.0, 'Tol-': -0.2, 'Tol+': 0.2,
     'Values': [29.85, 29.87, 29.86, 30.15, 30.18, 30.17, 30.16, 29.84, 29.88, 30.19]},
    # Linear dimension (normal case)
    {'Element': 'Dimensio_1', 'Nominal': 25.0, 'Tol-': -0.2, 'Tol+': 0.2,
     'Values': [25.02, 24.98, 25.01, 24.99, 25.06, 25.03, 24.97, 25.04, 24.96, 25.04]},
    # Traction test (one-sided tolerance, only minimum required)
    {'Element': 'Traccio_1', 'Nominal': 18000, 'Tol-': 0, 'Tol+': 50000,
     'Values': [18500, 19200, 21000, 19800, 18750, 20200, 19500, 18900, 20000, 19300]},
    # Angle (in degrees)
    {'Element': 'Angle_1', 'Nominal': 90.0, 'Tol-': -1.0, 'Tol+': 1.0,
     'Values': [89.8, 90.1, 90.0, 89.9, 90.2, 89.7, 90.3, 89.6, 90.0, 90.1]},
    # GD&T - flatness (unilateral tolerance)
    {'Element': 'Flatness_1', 'Nominal': 0.0, 'Tol-': 0.0, 'Tol+': 0.3,
     'Values': [0.05, 0.12, 0.09, 0.07, 0.11, 0.13, 0.08, 0.10, 0.06, 0.14]},
    # Linear dimension with asymmetric tolerance
    {'Element': 'Dimensio_2', 'Nominal': 50.0, 'Tol-': -0.3, 'Tol+': 0.1,
     'Values': [49.85, 49.90, 50.05, 49.95, 50.00, 49.80, 49.88, 49.92, 50.01, 49.89]},
    # GD&T - position tolerance
    {'Element': 'Position_1', 'Nominal': 0.0, 'Tol-': 0.0, 'Tol+': 0.2,
     'Values': [0.08, 0.15, 0.12, 0.18, 0.10, 0.14, 0.11, 0.13, 0.09, 0.16]}
    ]
    
    mesures = pd.DataFrame(data) #print(f"DataFrame with sample data:\n{mesures}")
    
    return mesures

# ------------------------------ Corrector de la desviació per mida de mostra ------------------------------ #
def c4(n):
    return np.sqrt(2 / (n - 1)) * (gamma(n / 2) / gamma((n - 1) / 2))

# ------------------------------------------ Statistical Analysis ------------------------------------------ #
def analisi_mostra(mostra):
    """
    Analyze the sample for normality and calculate statistics.

    Args:
        mostra (array-like): Sample data to analyze.

    Returns:
        tuple: (mean, std_long, std_short, is_normal, ad_stat)
            mean: Sample mean
            std_long: Standard deviation (long-term, unbiased)
            std_short: Short-term std (from moving range)
            is_normal: Boolean, True if sample passes Anderson-Darling at 5%
            ad_stat: Anderson-Darling statistic
    """
    mostra = np.asarray(mostra)
    n = len(mostra)
    if n < 5:
        raise ValueError("Sample too small for normality analysis (n < 5).")

    c4_n = c4(n)
    d2 = 1.128

    mu = np.mean(mostra)
    std_long = np.std(mostra, ddof=1)   #std a llarg termini PP i PPK

    # Moving range and short-term std
    mr = np.abs(np.diff(mostra))
    mr_bar = np.mean(mr)
    std_short = mr_bar / d2             #std a curt termini CP i CPK

    # Anderson-Darling test for normality
    ad_test = stats.anderson(mostra, dist='norm')
    ad_stat = ad_test.statistic
    # Find the 5% significance level dynamically (if available)
    try:
        ad_crit = ad_test.critical_values[list(ad_test.significance_level).index(5.0)]
    except (AttributeError, ValueError):
        ad_crit = ad_test.critical_values[2]  # fallback to index 2 (usually 5%)

    is_normal = ad_stat < ad_crit

    return mu, std_long, std_short, is_normal, ad_stat
   
# ------------------------------------------ Anàlisi de normalitat de la mostra extrapolada ------------------------------------------ #
def anderson_mostra(sample, mean = None, std = None):
    """
    Manual calculation of the Anderson-Darling A² statistic for a given sample.
    If mean or std are not provided, use the sample's mean and std.
    Args:
        sample (array-like): Sample data.
        mean (float, optional): Mean of the sample. If None, it will be calculated from the sample.
        std (float, optional): Standard deviation of the sample. If None, it will be calculated from the sample.
    Returns:
        tuple: A² statistic and a DataFrame with intermediate calculations.
    """
    sample = np.asarray(sample)
    n = len(sample)
    if n < 5:
        raise ValueError("Sample too small.")
    sorted_sample = np.sort(sample)
    
    # Use sample mean and std if not provided
    if mean is None:
        mean = np.mean(sample)
    if std is None:
        std = np.std(sample, ddof=1)

    cdf_vals = stats.norm.cdf(sorted_sample, loc=mean, scale=std)
    cdf_vals = np.clip(cdf_vals, 1e-10, 1 - 1e-10)
    i = np.arange(1, n + 1)
    one_minus_cdf = 1 - cdf_vals
    one_minus_cdf_reverse = 1 - cdf_vals[::-1]
    s = (2 * i - 1) * (np.log(cdf_vals) + np.log(one_minus_cdf_reverse))
    A_2 = -n - np.sum(s) / n
    A2_corrected = A_2 * (1 + 0.75 / n + 2.25 / (n ** 2))

    df = pd.DataFrame({
        'i': i,
        'sorted': sorted_sample,
        'F(Xi)': cdf_vals,
        '1-F(Xi)': one_minus_cdf,
        '1-F(Xn-i+1)': one_minus_cdf_reverse,
        'S': s
    })

    return A2_corrected, df

# -------------------------------- Aproximació del p-valor d'Anderson-Darling -------------------------------- #
def pvalor_approx(ad):
    if ad >= 0.6:
        return np.exp(1.2937 - 5.709 * ad + 0.0186 * ad**2)
    elif 0.34 < ad < 0.6:
        return np.exp(0.9177 - 4.279 * ad - 1.38 * ad**2)
    elif 0.2 < ad <= 0.34:
        return 1 - np.exp(-8.318 + 42.796 * ad - 59.938 * ad**2)
    else:  # A2 <= 0.2
        return 1 - np.exp(-13.436 + 101.14 * ad - 223.73 * ad**2)

# ------------------------------------------ Generate Synthetic Data and Plot ------------------------------------------ #
def extrapolar(mostra_orig, nominal, tol_inf, max_attempts=100):
    """ Extrapola la mostra original fins a obtenir una mostra amb p-valor >= 0.05 en el test d'Anderson-Darling.
    Args:
        data_original (array-like): Mostra original.
        n_vals (int): Nombre total de valors desitjats a la mostra final.
        mean (float): Mitjana de la mostra original.
        std (float): Desviació estàndard de la mostra original.
        nominal (float): Valor nominal per a la comparació.
        tol_inf (float): Tolerància inferior per al valor nominal.
        max_attempts (int): Nombre màxim d'intents per generar una mostra normal.
    Returns:
        tuple: Mostra final, estadístic A² d'Anderson-Darling i p-valor aproximat.
    """
    extrap = input("Vols extrapolar? (s/n): ").strip().lower() == 's'
    extrapolate_selected = False  # True if extrap, False otherwise
    n_orig = len(mostra_orig)
    mu = np.mean(mostra_orig)
    std = np.std(mostra_orig, ddof=1)    
    attempt = 0
    avoid_negatives = (nominal == 0 and tol_inf == 0)   # Comprovació per evitar negatius segons els valors oficials
    
    if extrap:
        extrapolate_selected = True
        options = [50, 60, 70, 80, 90, 100]
        print("Selecciona el nombre de valors a extrapolar:")
        for idx, val in enumerate(options):
            print(f"{idx+1}. {val}")
        sel = int(input("Opció (1-6): "))
        n_vals = options[sel-1]
    else:
        n_vals = None  # No extrapolació, només valors reals
    print(extrapolate_selected)
        
    if n_vals is None or n_vals <= len(mostra_orig):
        print("No s'ha seleccionat extrapolació o el nombre de valors és menor o igual a la mostra original.")
        return mostra_orig, None, None, extrapolate_selected
    
    if n_orig > n_vals:
        raise ValueError("La mostra original és més gran que el nombre de valors desitjat per extrapolar.")
    
    if std == 0:
        raise ValueError("Standard deviation of the original data is zero, cannot extrapolate.")
    
    if extrap and n_vals > n_orig:
        while attempt < max_attempts:   # Generate new random values (excluding the originals)
            n_extra = n_vals - n_orig
            if n_extra > 0:
                if avoid_negatives:
                    new_vals = np.abs(np.random.normal(mu, std, n_extra))   # Genera només valors positius
                else:
                    new_vals = np.random.normal(mu, std, n_extra)
                sample = np.concatenate([mostra_orig, new_vals])
            else:
                sample = np.array(mostra_orig[:n_vals])

            # -------------- Calculate Anderson-Darling A² and p-value -------------- #
            A_2, _ = anderson_mostra(sample, mu, std)
            pval = pvalor_approx(A_2)
            print(f"Attempt {attempt+1}: A² = {A_2:.4f}, p ≈ {pval:.4f}")
            if pval >= 0.05:
                print("Sample is probably normal (p >= 0.05).")
                return sample, A_2, pval, extrapolate_selected
            attempt += 1

    print("Warning: Could not achieve p >= 0.05 after max attempts.")
    return sample, A_2, pval, extrapolate_selected


def detect_element_type(element_name):
    """
    Detects if the element is a GD&T or a traction/force/compression/hysteresis property.
    Returns (gdt, traccio)
    """
    name = element_name.lower()
    gdt_keywords = ['flatness', 'position', 'parallelism', 'perpendicularity',
                    'cylindricity', 'concentricity', 'symmetry', 'profile', 'runout']
    traccio_keywords = ['force', 'traction', 'compression', 'hysteresi', 'hysteresis']

    gdt = any(kw in name for kw in gdt_keywords)
    traccio = any(kw in name for kw in traccio_keywords)
    return gdt, traccio

# ------------------------------ Càlcul d'indicadors de capacitat del procés (CP, CPK, PP, PPK) ------------------------------ #
def index_proces(element, nominal_value, mean, desvest, tolerance):
    """
    Calculate process capability indices: Pp, Ppk.
    Args:
        mostra (array-like): Sample data.
        nominal_value (float): Nominal value of the process.
        tolerance (list or tuple): Tolerance limits [lower, upper].
    """
    gdt, traccio = detect_element_type(element)
    
    pk_inf = (mean - (nominal_value + tolerance[0])) / (3 * desvest)
    pk_sup = (nominal_value + tolerance[1] - mean) / (3 * desvest)
    p = (nominal_value + tolerance[1] - (nominal_value + tolerance[0])) / (6 * desvest)
    
    if traccio:
        pk = pk_inf
    elif gdt:
        pk = pk_sup
    else:
        pk = min(pk_sup, pk_inf)
        
    return p, pk

def ppm_calc(nominal_val, tolerance, mean, desvest):
    """
    Calculate ppm
    Args:
        nominal_value (float): Nominal value of the process.
        tolerance (list or tuple): Tolerance limits [lower, upper].
        mean (float): Mean of the analyzed sample.
        desvest (float): Standard deviation estimated for the process."""
    LSL = nominal_val+tolerance[0]
    USL = nominal_val+tolerance[1]
    
    z_lower = (LSL - mean) / desvest
    z_upper = (USL - mean) / desvest
    ppm_lower = stats.norm.cdf(z_lower) * 1e6
    ppm_upper = (1 - stats.norm.cdf(z_upper)) * 1e6
    PPM_total = ppm_lower + ppm_upper
    
    return PPM_total


# --------------------------------------------------------- Main --------------------------------------------------------- #
def main():
    """ Main function to run the analysis and generate output files. """
    os.makedirs(output_dir, exist_ok=True)
    df = get_sample_data()

    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        nominal = row['Nominal']
        tolerance = [row['Tol-'], row['Tol+']]
        sample_data = [float(round(x, 6)) for x in row['Values']]

        mu, std_long, std_short, test_result, ad_stat = analisi_mostra(sample_data)
        print(f"\nL'{element} és normal? - {test_result}")
        
        pvalor_mostra = pvalor_approx(ad_stat)
        cp, cpk = index_proces(element, nominal, mu, std_short, tolerance)
        ppm_short = ppm_calc(nominal, tolerance, mu, std_short)
        print(f"AD:{ad_stat:.4f}, P:{pvalor_mostra:.4f}")
        print(f"\nCurt termini\nMitjana: {mu:.5f}, Desviació estàndard: {std_short:.5f}")
        print(f"Índex de capacitat del procés: CP = {cp:.5f}, CPK = {cpk:.5f}")
        print(f"PPM:{ppm_short:.4f}\n")
        
        pp, ppk = index_proces(element, nominal, mu, std_long, tolerance)
        ppm_long = ppm_calc(nominal, tolerance, mu, std_long)
        mu, std_long, pp, ppk, cp, cpk = [round(x, 6) for x in (mu, std_long, pp, ppk, cp, cpk)]
        print(f"\nLlarg termini\nMitjana: {mu:.5f}, Desviació estàndard: {std_long:.5f}")
        print(f"Índex de rendiment del procés: PP = {pp:.5f}, PPK = {ppk:.5f}")
        print(f"PPM:{ppm_long:.4f}\n")
        
        final_values, A_2, pval, extrap = extrapolar(sample_data, nominal, tolerance[0])
        # If no extrapolation, set extrapolated values to empty list
        if extrap is False:
            final_values = []
            A_2 = ''
            pval = ''
            print(f"Could not extrapolate {element} to achieve normality.")
        else:
            final_values = [float(round(x, 6)) for x in final_values]
            A_2 = float(round(A_2, 6))
            pval = float(round(pval, 6))
            print(f"Anderson-Darling A² = {A_2:.4f}, p-valor ≈ {pval:.4f}")

        # Prepare the DataFrame for this element
        data_dict = {
            'Element': [element],
            'Nominal': [nominal],
            'Tolerance': [tolerance],
            'Original Values': [list(sample_data)],
            'Mean': [mu],
            'Std (short term)': [std_short],
            'CP (long term)': [cp],
            'CPK (long term)': [cpk],
            "ppm (short term)": [ppm_short],
            'Std (long term)': [std_long],
            'PP (long term)': [pp],
            'PPK (long term)': [ppk],
            "ppm (long term)": [ppm_long],
            'Extrapolated Values': [list(final_values)],
            'P-value': [pval]
        }
        element_df = pd.DataFrame(data_dict)

        out_csv = os.path.join(output_dir, f"{element}_summary.csv")
        element_df.to_csv(out_csv, index=False)
        print(f"Saved for {element} to {out_csv}\n")

if __name__ == "__main__":
    main()
