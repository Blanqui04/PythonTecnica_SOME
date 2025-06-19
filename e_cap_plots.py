import os
import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
# ------------------------------------------ Sample Data Retrieval ------------------------------------------ #
from e_cap import get_sample_data, analisi_mostra, pvalor_approx, extrapolar, index_proces
from e_cap import main as main_estudi_cap

output_dir = r'C:\Github\PythonTecnica_SOME\estudi de capacitat'
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------ Constants and Style Setup ------------------------------------------ #
font_name = 'Times new roman'
taronja = "#B86800"
vermell = "#830B0B"
vermell_clar = "#faa9a9"
verd = "#156315"
blau = "#1f77b4"
negre = "#000000"
gris = "#6B6565"
gold_r = (1 + np.sqrt(5)) / 2 
save = True  # Save plots?
display = False  # Show plots?

# ------------------------------------------ Plot Histogram & Q-Q Plot (mostra real)------------------------------------------ #
def plt_sample_analysis(mostra, nominal, tol, element, pval_ad=None, ad_res=None, save=False, display=False):
    kde_kwargs = {"fill": True, "linewidth": 1}
    mean = np.mean(mostra)
    std = np.std(mostra, ddof=1)

    fig, axs = plt.subplots(1, 2, figsize=(10, 10/gold_r))
    fig.subplots_adjust(top=0.70)  # Leave space for main title and subtitle

    # ----------- Main Title and Subtitle -----------
    fig.suptitle(
        f"Normality Analysis – {element}",
        fontsize=16,
        fontname=font_name,
        y=0.94
    )
    subtitle = ""
    if pval_ad is not None and ad_res is not None:
        subtitle = (
            f"Mean ($\\bar{{x}}$): {mean:.4f}   "
            f"Standard Deviation ($\\sigma$): {std:.4f}   "
            f"p-value: {pval_ad:.4f}   "
            f"Normality: {'Yes' if ad_res else 'No'}"
        )
    if subtitle:
        fig.text(
            0.5, 0.87, subtitle,
            ha='center', va='center',
            fontsize=11, fontname=font_name, color="#444444"
        )

    # ----------- Histogram + KDE -----------
    ax = axs[0]
    ax.grid(True, linestyle='--', alpha=0.4, zorder=0)
    sns_hist = sns.histplot(mostra, kde=True, color=blau, edgecolor=negre, ax=ax, **kde_kwargs)
    x_min, x_max = ax.get_xlim()
    x_range = abs(x_max - x_min)
    
    if x_range < 0.001:
        fmt = '{x:.4f}'
    elif x_range < 0.1:
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
        label.set_fontname(font_name)
    for label in ax.get_yticklabels():
        label.set_fontname(font_name)

    kde_line = None
    for line in sns_hist.lines:
        if line.get_label() == 'KDE':
            kde_line = line
            break
    if kde_line is not None:
        kde_ymax = np.max(kde_line.get_ydata())
    else:
        kde_ymax = 1

    x = np.linspace(min(mostra), max(mostra), 100)
    pdf = stats.norm.pdf(x, loc=mean, scale=std)
    pdf_scaled = pdf * kde_ymax / np.max(pdf)
    ax.plot(x, pdf_scaled, color=negre, linewidth=1)

    ax.axvline(nominal + tol[0], color=vermell, linestyle='-', linewidth=1, label=f'LSL ({nominal + tol[0]:.2f})')
    ax.axvline(nominal + tol[1], color=vermell, linestyle='-', linewidth=1, label=f'USL ({nominal + tol[1]:.2f})')
    ax.axvline(nominal, color=verd, linestyle='-', linewidth=1, label=f'Nominal ($x_0$={nominal:.2f})')
    ax.axvline(mean, color=negre, linestyle='--', linewidth=1)

    ax.set_title("Histogram and KDE", fontsize=13, fontname=font_name)
    ax.set_xlabel('Value', fontsize=11, fontname=font_name)
    ax.set_ylabel('Frequency', fontsize=11, fontname=font_name)
    ax.legend(fontsize=8, prop={'family': font_name}, markerscale=0.8, handlelength=0.5,
              borderpad=0.3, labelspacing=0.2, handletextpad=0.5, loc='best')

    # ----------- Q-Q Plot -----------
    (osm, osr), (slope, intercept, r) = stats.probplot(mostra, dist="norm")
    ax = axs[1]
    ax.grid(True, linestyle='--', alpha=0.4, zorder=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}'))
    ax.tick_params(axis='x', labelsize=9, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
    ax.tick_params(axis='y', labelsize=9, rotation=0)
    for label in ax.get_xticklabels():
        label.set_fontname(font_name)
    for label in ax.get_yticklabels():
        label.set_fontname(font_name)

    # --- Bootstrap confidence bands for Q-Q plot ---
    n_boot = 1000  # Number of bootstrap samples
    boot_lines = []
    for _ in range(n_boot):
        # Resample with replacement from mostra
        sample = np.random.choice(mostra, size=len(mostra), replace=True)
        # Get theoretical and sample quantiles for the bootstrap sample
        osm_b, osr_b = stats.probplot(sample, dist="norm", fit=False)
        # Fit a line to the bootstrap sample's Q-Q plot
        reg_b = stats.linregress(osm_b, osr_b)
        # Calculate the fitted line at the original osm points
        boot_lines.append(reg_b.slope * np.array(osm) + reg_b.intercept)
    boot_lines = np.array(boot_lines)
    # Calculate the 2.5th and 97.5th percentiles for each point (95% confidence interval)
    lower_bound = np.percentile(boot_lines, 2.5, axis=0)
    upper_bound = np.percentile(boot_lines, 97.5, axis=0)

    # Plot the 95% confidence band as a shaded area
    ax.fill_between(osm, lower_bound, upper_bound, color=gris, alpha=0.25, label="95% Confidence Band")

    # Plot the Q-Q line (fit to your data)
    ax.plot(osm, slope * np.array(osm) + intercept, color=vermell, linewidth=2, zorder=2, label="Normal Fit")
    # Plot the sample quantiles as points
    ax.scatter(osm, osr, color=blau, edgecolor=negre, linewidths=0.5, s=50, zorder=3, label="Sample Quantiles")

    ax.set_title("Q-Q Plot", fontsize=13, fontname=font_name)
    ax.set_xlabel('Theoretical Quantiles', fontsize=11, fontname=font_name)
    ax.set_ylabel('Sample Quantiles', fontsize=11, fontname=font_name)
    ax.legend(fontsize=8, prop={'family': font_name}, markerscale=0.7, handlelength=1,
            borderpad=0.25, labelspacing=0.25, handletextpad=0.4, loc='best')

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    if save:
        filename = os.path.join(output_dir, fr'{element}_normalitat.png')
        plt.savefig(filename, format='png')
        plt.close()
    if display:
        plt.show()
        plt.close()

# ------------------------------------------ Plot with the extrapolated values ------------------------------------------ #
def plt_extrapolated_sample(mostra, nominal, tol, mu, std, element_name, pp=None, ppk=None, pval=None, is_normal=None, save=True, display=False):
    xmin, xmax = min(mostra), max(mostra)
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
    
    sns.histplot(mostra, bins=30, kde=True, stat="count", alpha=0.6, color=blau, edgecolor='k') #, label='Dades extrapolades'
    plt.plot(x, p * len(mostra) * (xmax - xmin) / 30, negre, linewidth=1,
             label=fr'$\bar{{x}}$ = {mu:.4f}     $\sigma$ = {std:.4f}')
    plt.axvline(nominal + tol[0], color=vermell, linestyle='--', linewidth=1, label=f'LSL: ({nominal + tol[0]:.2f})')
    plt.axvline(nominal + tol[1], color=vermell, linestyle='--', linewidth=1, label=f'USL: ({nominal + tol[1]:.2f})')
    plt.axvline(nominal, color=verd, linestyle='--', linewidth=1, label=fr'Nominal: $x_0$ = {nominal:.2f}')
    plt.fill_between(x, 0, p * len(mostra) * (xmax - xmin) / 30,
                     where=(x < nominal + tol[0]) | (x > nominal + tol[1]),
                     color=vermell_clar, alpha=0.4)

    plt.xlabel('Mesures de cotes', fontsize=14, fontname=font_name)
    plt.ylabel('Freqüència', fontsize=14, fontname=font_name)
    # Title
    ax.set_title(f'Distribució de mesures - {element_name}', fontsize=16, fontname=font_name, pad=22)

    # Subtitle (as a second text, not superposed)
    subtitle = ""
    if pp is not None and ppk is not None:
        subtitle += f"Pp = {pp:.3f}, Ppk = {ppk:.3f}   "
    if pval is not None:
        subtitle += f"p-value = {pval:.4f}   "
    if is_normal is not None:
        subtitle += f"Normal: {'Yes' if is_normal else 'No'}"

    if subtitle.strip():
        # Place subtitle just below the title, using axes coordinates
        ax.text(
            0.5, 1.01, subtitle.strip(),
            fontsize=11,
            fontname=font_name,
            color="#444444",
            ha='center',
            va='bottom',
            transform=ax.transAxes
        )
    
    plt.legend(fontsize=12, prop={'family': font_name})
    plt.tight_layout()
    if save:
        filename = os.path.join(output_dir, fr'{element_name}_extrapolada.png')
        plt.savefig(filename, format='png')
        plt.close()
    if display:
        plt.show()
        plt.close()
        
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
    ax.set_yscale('linear')     # Set y-axis to linear scale
    ax.set_ylim(1e-2, 1)        # y-axis between 0.01 and 1 for better visualization
    ax.set_xlim(0, 1.2)         # x-axis between 0 and 1.2

    # Add horizontal threshold line at p = 0.05
    ax.axhline(0.05, color = vermell, linestyle='-', linewidth=0.75, label='Llindar p-val = 0.05')

    # Add vertical lines to separate empirical formula regions
    ax.axvline(0.2, color = gris, linestyle='-.', linewidth=0.5)
    ax.axvline(0.34, color = gris, linestyle='-.', linewidth=0.5)
    ax.axvline(0.6, color = gris, linestyle='-.', linewidth=0.5)

    # Highlight the A² value and its p-value if provided
    if A2_value is not None:
        pval = pvalor_approx(A2_value)
        ax.axvline(A2_value, color = verd, linestyle='-', linewidth=1, label=f'A² = {A2_value:.3f}')
        ax.plot(A2_value, pval, marker='o', markersize=8, markerfacecolor='white',
                markeredgecolor=negre, markeredgewidth=1, label=f'p-valor ≈ {pval:.4f}')
    # Labels and title
    ax.set_xlabel('Estadístic Anderson-Darling A²')
    ax.set_ylabel('p-valor estimat')
    ax.set_title(f'Relació entre A² i p-valor - {element_name}', fontsize=14, fontname=font_name)
    ax.set_yscale('log')
    ax.set_xlim(0.1, 1.2)
    ax.legend(fontsize=9)
    plt.tight_layout()
    if save:
        filename = os.path.join(output_dir, f'{element_name}_p-valor.png')
        plt.savefig(filename, format='png')
        plt.close()
    if display:
        plt.show()
        plt.close()


# ------------------------------------------ Gràfic I ------------------------------------------ #
def i_chart(mostra, nominal, tol, mu, MR, element_name, pp=None, ppk=None, save=True, display=False):
    """
    Professional I-Chart for automotive capability studies.
    """
    indices = np.arange(1, len(mostra) + 1)
    LSL = nominal + tol[0]
    USL = nominal + tol[1]
    CL = mu
    UCL = mu + 2.659816 * MR
    LCL = mu - 2.659816 * MR

    # Determine point colors: blue if in spec, red if out of spec
    point_colors = [
        "#1f77b4" if (LSL <= v <= USL) else "#B22222" for v in mostra
    ]

    plt.figure(figsize=(10, 6))
    plt.grid(True, linestyle=":", alpha=0.4, zorder=0)

    # Plot points and lines
    plt.plot(
        indices,
        mostra,
        color="#1f77b4",
        linewidth=1,
        zorder=3
    )
    plt.scatter(
        indices,
        mostra,
        color=point_colors,
        edgecolor="black",
        s=60,
        zorder=4,
        label="Out of Spec" if any(c == "#B22222" for c in point_colors) else "In Spec",
    )

    # Control limits
    plt.axhline(UCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=f"UCL = {UCL:.2f}")
    plt.axhline(LCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=f"LCL = {LCL:.2f}")

    # Specification limits (red solid)
    plt.axhline(USL, color=gris, linestyle="--", alpha=0.5, linewidth=0.5, zorder=5, label=f"USL ({USL:.2f})")
    plt.axhline(LSL, color=gris, linestyle="--", alpha=0.5, linewidth=0.5, zorder=5, label=f"LSL ({LSL:.2f})")

    # Mean (black solid)
    plt.axhline(CL, color="#000000", linestyle="-", linewidth=0.8, zorder=2, label=f"Mean ($\\bar{{x}}$ = {mu:.2f})")

    # Nominal (green dash-dot)
    plt.axhline(nominal, color="#156315", linestyle="-", linewidth=0.8, zorder=2, label=f"Nominal ($x_0$ = {nominal:.2f})")

    # Title and subtitle with blank space between them and the chart
    ax = plt.gca()
    # Title
    ax.set_title(
        f"Diagrama de control individual - {element_name}",
        fontsize=15,
        fontname="Times New Roman",
        pad=30  # More space below title
    )
    # Subtitle (as a second text, not superposed)
    subtitle = f"Capacitat de procés: Pp = {pp:.2f}, Ppk = {ppk:.2f}" if pp is not None and ppk is not None else ""
    if subtitle:
        ax.text(
            0.5, 1.03, subtitle,  # y > 1 for space below title
            fontsize=11,
            fontname="Times New Roman",
            color="#444444",
            ha='center',
            va='bottom',
            transform=ax.transAxes
        )

    plt.xlabel("Índex de peça", fontsize=12, fontname="Times New Roman")
    plt.ylabel("Valor mesurat", fontsize=12, fontname="Times New Roman")
    plt.xticks(indices, fontname="Times New Roman")
    plt.yticks(fontname="Times New Roman")
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Professional, tiny legend
    plt.legend(
        fontsize=6,
        prop={"family": "Times New Roman"},
        loc="upper right",
        frameon=True,
        framealpha=0.95,
        borderpad=0.3,
        labelspacing=0.2,
        handlelength=0.7,
        handletextpad=0.3,
        markerscale=0.7,
    )

    if save:
        filename = os.path.join(output_dir, f"{element_name}_IChart.png")
        plt.savefig(filename, format="png")
        plt.close()
    if display:
        plt.show()
        plt.close()

# ------------------------------------------ Gràfic R_m ------------------------------------------ #
def rm_chart(mostra, element_name, pp=None, ppk=None, save=True, display=False):
    """
    Gràfica de rangos móviles (MR) para estudios de capacidad en automoción.
    La MR chart muestra la variación entre observaciones consecutivas.
    """
    mostra = np.asarray(mostra)
    # Calcular los rangos móviles (MR)
    mr = np.abs(np.diff(mostra))
    indices = np.arange(2, len(mostra) + 1)  # MR está definido desde la segunda observación

    # Línea central (CL): promedio de los rangos móviles
    MR_bar = np.mean(mr)
    # D4 y D3 para n=2 (subgrupo de tamaño 2)
    D4 = 3.267
    D3 = 0
    UCL = D4 * MR_bar
    LCL = D3 * MR_bar  # Siempre 0 para n=2

    plt.figure(figsize=(10, 6))
    plt.grid(True, linestyle=":", alpha=0.4, zorder=0)

    # Dibujar los rangos móviles
    plt.plot(indices, mr, marker='o', color=blau, linewidth=1, zorder=3)
    plt.scatter(indices, mr, color=blau, edgecolor=negre, s=60, zorder=4)

    # Líneas de control
    plt.axhline(UCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=f"UCL = {UCL:.2f}")
    plt.axhline(MR_bar, color=negre, linestyle="-", linewidth=1, zorder=2, label=f"CL = {MR_bar:.2f}")
    plt.axhline(LCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=f"LCL = {LCL:.2f}")

    # Títulos y etiquetas
    ax = plt.gca()
    ax.set_title(
        f"Moving range chart - {element_name}",
        fontsize=15,
        fontname="Times New Roman",
        pad=30
    )
    # Subtítulo opcional
    d2 = 1.128
    sigma_est = MR_bar/d2

    subtitle = (
        f"Estimated deviation: {sigma_est:.4f}")
    if subtitle:
        ax.text(
            0.5, 1.03, subtitle,
            fontsize=11,
            fontname="Times New Roman",
            color="#444444",
            ha='center',
            va='bottom',
            transform=ax.transAxes
        )

    plt.xlabel("Índex de peça", fontsize=12, fontname="Times New Roman")
    plt.ylabel("Rang mòbil", fontsize=12, fontname="Times New Roman")
    plt.xticks(indices, fontname="Times New Roman")
    plt.yticks(fontname="Times New Roman")
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    plt.legend(
        fontsize=7,
        prop={"family": "Times New Roman"},
        loc="upper right",
        frameon=True,
        framealpha=0.95,
        borderpad=0.3,
        labelspacing=0.2,
        handlelength=0.7,
        handletextpad=0.3,
        markerscale=0.7,
    )

    if save:
        filename = os.path.join(output_dir, f"{element_name}_MRChart.png")
        plt.savefig(filename, format="png")
        plt.close()
    if display:
        plt.show()
        plt.close()
    
    return MR_bar

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
        pp, ppk = index_proces(mostra, nominal, tolerance)
        mu, std, pp, ppk = [round(x, 6) for x in (mu, std, pp, ppk)]

        pval_ad = pvalor_approx(a2_stat) # Approximate p-value for A² statistic
        plt_sample_analysis(mostra, nominal, tolerance, element, pval_ad, is_normal, save, display) # Gràfics d’anàlisi
        MR_bar = rm_chart(mostra, element, pp, ppk, save, display)  # Rm-Chart
        i_chart(mostra, nominal, tolerance, mu, MR_bar, element, pp, ppk, save, display)  # I-Chart

        final_values, A_2, pval_e, extrap = extrapolar(mostra, nominal, tolerance[0])
        norm = None
        if pval_e is not None and pval_e > 0.05:
            norm = True
        elif pval_e is not None and pval_e <= 0.05:
            norm = False
        print(f"\nFinal sample n={len(final_values)}, {norm}.")
        
        if A_2 is None or pval_e is None:
            print(f"[{element}] No es pot extrapolar per aconseguir normalitat (A² o p-valor no disponible).")
            plt_extrapolated_sample(mostra, nominal, tolerance, mu, std, element, pp, ppk, pval_ad, is_normal, save, display)
            plot_pval(element, a2_stat, save, display)
            continue

        print(f"[{element}] Anderson-Darling A² = {A_2:.4f}, p-valor ≈ {pval_e:.4f}")

        if extrap:
            # Extrapolated sample achieved normality
            plt_extrapolated_sample(final_values, nominal, tolerance, mu, std, element, pp, ppk, pval_e, norm, save, display)
            plot_pval(element, A_2, save, display)
            continue          

        # Save to CSV
        out_csv = os.path.join(output_dir, f"{element}_extrapolated.csv")
        pd.DataFrame({'Extrapolated_Value': final_values}).to_csv(out_csv, index=False)


if __name__ == "__main__":
    # You can change n_vals here (e.g., 30, 50, 100, 500)
    main()
