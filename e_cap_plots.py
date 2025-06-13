import os
import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
# ------------------------------------------ Sample Data Retrieval ------------------------------------------ #
from e_cap import get_sample_data, analisi_mostra, anderson_mostra, pvalor_approx, extrapolar, index_proces
from e_cap import main as main_estudi_cap

output_dir = r'C:\Github\PythonTecnica_SOME\estudi de capacitat'
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------ Constants and Style Setup ------------------------------------------ #
font_name = 'Times new roman'
vermell = "#830B0B"
vermell_clar = "#faa9a9"
verd = "#156315"
blau = "#1f77b4"
negre = "#000000"
gris = "#6B6565"
gold_r = (1 + np.sqrt(5)) / 2 
save = False  # Save plots?
display = True  # Show plots?

# ------------------------------------------ Plot Histogram & Q-Q Plot (mostra real)------------------------------------------ #
def plt_sample_analysis(mostra, v_nominal, tol, n_element, pval_ad = None, ad_res = None, sv = False, dsp = False):
    kde_kwargs = {"fill": True, "linewidth": 1}                             # Arguments for KDE plot: fill area under curve, set line width
    (osm, osr), (slope, intercept, r) = stats.probplot(mostra, dist="norm") # Generate normal probability plot data and fit line
    mean = np.mean(mostra)                                                   # Calculate mean of the sample
    std = np.std(mostra, ddof=1)                                             # Calculate standard deviation of the sample (sample std)
    
    plt.figure(figsize=(10, 5))         # Creates a new figure window with a specific size. The width is 10 units, and the height is 10 divided by 'gold_r' (likely the golden ratio for aesthetics).
# ------------------------------------------ Histogram (mostra real) ------------------------------------------ #    
    plt.subplot(1, 2, 1)                        # Adds a subplot to the figure: 1 row, 2 columns, and this is the first subplot (left side).
    plt.grid(True, linestyle='--', alpha=0.4)   # Adds a grid to the plot, with dashed lines and some transparency.

    sns_hist = sns.histplot(mostra, kde = True, color = blau, edgecolor = negre, **kde_kwargs)   # Plots a histogram of 'sample_data' using seaborn.
    # - 'kde=True' adds a Kernel Density Estimate (KDE) curve to the histogram.
    # - '**kde_kwargs' passes additional keyword arguments to the KDE plot.
    
    # Obté l'eix actual i aplica formatador i paràmetres als ticks X
    ax = plt.gca()
    # Set dynamic decimal formatting for x-ticks based on data range
    x_min, x_max = ax.get_xlim()
    x_range = abs(x_max - x_min)
    if x_range < 0.001:
        fmt = '{x:.4f}'
    elif x_range < 00.1:
        fmt = '{x:.3f}'
    elif x_range < 0.11:
        fmt = '{x:.2f}'
    elif x_range < 1:
        fmt = '{x:.1f}'
    else:
        fmt = '{x:.0f}'
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt.format(x=x)))
    ax.tick_params(axis='x', labelsize=9, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}'))
    ax.tick_params(axis='y', labelsize=9, rotation=0)
    for label in ax.get_xticklabels():
        label.set_fontname('Times New Roman')
    for label in ax.get_yticklabels():
        label.set_fontname('Times New Roman')
    
    kde_line = None # Get the KDE line from the seaborn plot
    for line in sns_hist.lines:
        if line.get_label() == 'KDE':
            kde_line = line
            break
    if kde_line is not None:
        kde_ymax = np.max(kde_line.get_ydata())
    else:
        kde_ymax = 1  # fallback if KDE not found

    # Traça la PDF normal teòrica
    x = np.linspace(min(mostra), max(mostra), 100)
    pdf = stats.norm.pdf(x, loc = mean, scale = std)    # Calculate the PDF of the normal distribution.
    pdf_scaled = pdf * kde_ymax / np.max(pdf)           # Scale PDF to match KDE height
    plt.plot(x, pdf_scaled, color=negre, linewidth=1)   #, label='PDF normal teòrica')
    
    plt.axvline(v_nominal + tol[0], color = vermell, linestyle = '-', linewidth = 1, label = f'LSL ({v_nominal + tol[0]:.2f})')
    plt.axvline(v_nominal + tol[1], color = vermell, linestyle = '-', linewidth = 1, label = f'USL ({v_nominal + tol[1]:.2f})')
    plt.axvline(v_nominal, color = verd, linestyle = '-', linewidth = 1, label = f'Nominal ($x_0$={v_nominal:.2f})')
    plt.axvline(mean, color = negre, linestyle = '--', linewidth = 1, label = f'Mitjana ($\\bar{{x}}$ = {mean:.2f})')  # Adds a vertical line at the mean of the sample data.
    
    plt.title(f'Histograma de la mostra - {n_element}', fontsize=14, fontname=font_name)    # Sets the plot title, using a specific font and size.
    plt.xlabel('Valor', fontsize=11, fontname=font_name)                                    # Sets the x-axis label.
    plt.ylabel('Freqüència', fontsize=11, fontname=font_name)                               # Sets the y-axis label.
    plt.legend(fontsize=8, prop={'family': font_name}, markerscale=0.6, handlelength=0.5,
               borderpad=0.25, labelspacing=0.2, handletextpad=0.5, loc='best')             # Adds a legend to the plot, using a specific font and size.
# ------------------------------------------ Q-Q Plot (mostra real) ------------------------------------------ #
    plt.subplot(1, 2, 2)
    plt.grid(True, linestyle = '--', alpha=0.4)
    # Obté l'eix actual i aplica formatador i paràmetres als ticks X
    ax = plt.gca()
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}'))
    ax.tick_params(axis='x', labelsize=9, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
    ax.tick_params(axis='y', labelsize=9, rotation=0)
    
    for label in ax.get_xticklabels():
        label.set_fontname('Times New Roman')
    for label in ax.get_yticklabels():
        label.set_fontname('Times New Roman')
    
    plt.plot(osm, slope * np.array(osm) + intercept, color = vermell, linewidth = 2, label = fr'r = {r:.3f}')
    plt.scatter(osm, osr, color = blau, edgecolor = negre, linewidths = 0.5, s = 50, label = 'Dades')
    
    plt.title(f'Q-Q Plot - {n_element}', fontsize=14, fontname=font_name)
    plt.xlabel('Quantils teòrics', fontsize=11, fontname=font_name)
    plt.ylabel('Quantils de la mostra', fontsize=11, fontname=font_name)
    plt.legend(fontsize=8, prop={'family': font_name}, markerscale=0.7, handlelength=1,
               borderpad=0.25, labelspacing=0.25, handletextpad=0.4, loc='best')         # Adds a legend to the plot, using a specific font and size.
    
    if pval_ad is not None and ad_res is not None:     # Add Anderson-Darling A² statistic and critical value as text on the Q-Q plot
        txt = f"p-valor = {pval_ad:.4f} \nNormal: {'Yes' if ad_res else 'No'}"
        plt.gca().text(0.025, 0.975, txt, transform=plt.gca().transAxes,
                       fontsize=10, fontname=font_name, verticalalignment='top',
                       bbox=dict(facecolor='white', alpha=0.4, boxstyle='round,pad=0.25'))

    plt.tight_layout()
    if sv:
        filename = os.path.join(output_dir, fr'{n_element}_normalitat.svg')
        plt.savefig(filename, format='svg')
    if dsp:
        plt.show()

# ------------------------------------------ Plot with the extrapolated values ------------------------------------------ #
def plt_extrapolated_sample(ext_dt, nom_vl, tol, mu, std, element_name, sv=True, dsp=False):
    xmin, xmax = min(ext_dt), max(ext_dt)
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, mu, std)

    plt.figure(figsize=(10, 10 / gold_r))
    plt.grid(True, linestyle='--', alpha=0.4)
    ax = plt.gca()

    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
    ax.tick_params(axis='x', labelsize=10, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
    ax.tick_params(axis='y', labelsize=10, rotation=0)
    for label in ax.get_xticklabels():
        label.set_fontname('Times New Roman')
    for label in ax.get_yticklabels():
        label.set_fontname('Times New Roman')
    
    sns.histplot(ext_dt, bins=30, kde=True, stat="count", alpha=0.6, color=blau, edgecolor='k', label='Dades extrapolades')
    plt.plot(x, p * len(ext_dt) * (xmax - xmin) / 30, negre, linewidth=1,
             label=fr'$\bar{{x}}$ = {mu:.4f}     $\sigma$ = {std:.4f}')
    plt.axvline(nom_vl + tol[0], color=vermell, linestyle='--', linewidth=1, label=f'Límit inferior: ({nom_vl + tol[0]:.2f})')
    plt.axvline(nom_vl + tol[1], color=vermell, linestyle='--', linewidth=1, label=f'Límit superior: ({nom_vl + tol[1]:.2f})')
    plt.axvline(nom_vl, color=verd, linestyle='--', linewidth=1, label=fr'Valor nominal: $x_0$ = {nom_vl:.2f}')
    plt.fill_between(x, 0, p * len(ext_dt) * (xmax - xmin) / 30,
                     where=(x < nom_vl + tol[0]) | (x > nom_vl + tol[1]),
                     color=vermell_clar, alpha=0.4)

    plt.xlabel('Mesures de cotes', fontsize=14, fontname=font_name)
    plt.ylabel('Freqüència', fontsize=14, fontname=font_name)
    plt.title(f'Distribució de mesures - {element_name}', fontsize=16, fontname=font_name)
    plt.legend(fontsize=12, prop={'family': font_name})
    plt.tight_layout()
    if sv:
        filename = os.path.join(output_dir, f'{element_name}_extrapolada.svg')
        plt.savefig(filename, format='svg')
    if dsp:
        plt.show()
        
# ------------------------------------------ Plot anàlisi de la mostra extrapolada -------------------------------------- #
def plot_pval(element_name, A2_value=None, save=True, display=False):
    # Prepare A² range and corresponding p-values
    A2_range = np.linspace(0, 1.2, 500)
    p_values = [pvalor_approx(a2) for a2 in A2_range]
    
    # Configure plot style
    plt.rcParams.update({
        'font.family': 'Times New Roman',
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10
    })

    fig, ax = plt.subplots(figsize=(8, 8/gold_r))
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.plot(A2_range, p_values, color=blau, linewidth=1.50)
    ax.set_yscale('linear')  # Set y-axis to linear scale
    ax.set_ylim(1e-2, 1)  # y-axis between 0.01 and 1 for better visualization
    ax.set_xlim(0, 1.2)   # x-axis between 0 and 1.2

    # Add horizontal threshold line at p = 0.05
    ax.axhline(0.05, color = vermell, linestyle='-', linewidth=0.75, label='Llindar p-val = 0.05')

    # Add vertical lines to separate empirical formula regions
    ax.axvline(0.2, color = gris, linestyle='-.', linewidth=0.5)
    ax.axvline(0.34, color = gris, linestyle='-.', linewidth=0.5)
    ax.axvline(0.6, color = gris, linestyle='-.', linewidth=0.5)

    # Highlight the A² value and its p-value if provided
    if A2_value is not None:
        pval = pvalor_approx(A2_value)
        ax.axvline(A2_value, color = verd, linestyle='--', linewidth=1.5, label=f'A² = {A2_value:.3f}')
        ax.plot(A2_value, pval, marker='o', markersize=8, markerfacecolor='white',
                markeredgecolor=negre, markeredgewidth=1, label=f'p-valor ≈ {pval:.4f}')
    # Labels and title
    ax.set_xlabel('Estadístic Anderson-Darling A²')
    ax.set_ylabel('p-valor estimat')
    ax.set_title(f'Relació entre A² i p-valor - {element_name}', fontsize=14, fontname=font_name)
    
    ax.set_xlim(0.1, 1.5)
    ax.legend(fontsize=9)
    plt.tight_layout()
    if save:
        filename = os.path.join(output_dir, f'{element_name}_p-valor.svg')
        plt.savefig(filename, format='svg')
    if display:
        plt.show()

# ------------------------------------------ Main ------------------------------------------ #
def main():
    os.makedirs(output_dir, exist_ok=True)  # Crear carpeta si no existeix

    # For now, use hardcoded sample data
    df = get_sample_data()  # print(f"DataFrame with sample data:\n {df}")

    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        print(f"\nProcessing element: {element} (Row {i+1}/{len(df)})\n")
        nominal = row['Nominal']
        tolerance = [row['Tol-'], row['Tol+']]
        mostra = np.array(row['Values'], dtype=float)

        mu, std, _, a2_stat, is_normal = analisi_mostra(mostra)
        pval_ad = pvalor_approx(a2_stat) # Approximate p-value for A² statistic

        # Gràfics d’anàlisi
        plt_sample_analysis(mostra, nominal, tolerance, element, pval_ad, is_normal, save, display)
        
        final_values, A_2, pval_ad = extrapolar(mostra, nominal, tolerance[0])
        print(f"\nFinal sample n={len(final_values)}")
        if A_2 is None or pval_ad is None:
            print(f"Could not extrapolate {element} to achieve normality.")
            continue
        else:
            print(f"Anderson-Darling A² = {A_2:.4f}, p-valor ≈ {pval_ad:.4f}")
            
        pp, ppk = index_proces(mostra, nominal, tolerance)
        print(f"Process performance: Pp = {pp:.4f}, Ppk = {ppk:.4f}")

        plt_extrapolated_sample(final_values, nominal, tolerance, mu, std, element, sv=save, dsp=display)   # Gràfic d’extrapolació
        plot_pval(element, A2_value=A_2, save=save, display=display)

        # Save to CSV
        out_csv = os.path.join(output_dir, f"{element}_extrapolated.csv")
        pd.DataFrame({'Extrapolated_Value': final_values}).to_csv(out_csv, index=False)


if __name__ == "__main__":
    # You can change n_vals here (e.g., 30, 50, 100, 500)
    main()
