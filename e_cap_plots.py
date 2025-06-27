import os
import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.table import Table
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
# ------------- Traduccions
from translation_dict import translations
# ------------------------------------------ Sample Data Retrieval ------------------------------------------ #
from e_cap import get_sample_data, analisi_mostra, pvalor_approx, extrapolar, index_proces, ppm_calc

output_dir = r'C:\Github\PythonTecnica_SOME\estudi de capacitat'
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------ Constants and Style Setup ------------------------------------------ #
font_name = 'Times new roman'
taronja = "#B96900"
vermell = "#830B0B"
vermell_clar = "#fab3b3"
verd = "#135E13"
blau = "#1e72ad"
negre = "#000000"
gris = "#A0A0A0"
gold_r = (1 + np.sqrt(5)) / 2 
save = True  # Save plots?
display = True  # Show plots?
lan = 'en'

# ------------------------------------------ Plot Histogram & Q-Q Plot (mostra real)------------------------------------------ #
def plt_sample_analysis(mostra, nominal, tol, element, std_short, pval_ad=None, ad=None, ad_res=None, save=False, display=False, language='en'):
    tr = translations[language]
    kde_kwargs = {"fill": True, "linewidth": 1}
    mean = np.mean(mostra)
    std = np.std(mostra, ddof=1)
    lsl = nominal + tol[0]
    usl = nominal + tol[1]
    
    fig, axs = plt.subplots(1, 2, figsize=(10, 10/gold_r))
    fig.subplots_adjust(top=0.70)  # Leave space for main title and subtitle
    # ----------- Main Title and Subtitle -----------
    fig.suptitle(
        tr['normality_analysis'].format(element=element),
        fontsize=16,
        fontname=font_name,
        y=0.94
    )
    subtitle = ""
    if pval_ad is not None and ad_res is not None:
        subtitle = (
            f"{tr['mean']}: {mean:.4f}   "
            f"AD: {ad:.4f}   "
            f"{tr['p_value']}: {pval_ad:.4f}   "
            f"{tr['normality']}: {tr['yes'] if ad_res else tr['no']}"
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

    # Troba la línia de la KDE de seaborn de manera robusta
    kde_line = None
    max_points = 0
    for line in sns_hist.lines:
        ydata = line.get_ydata()
        if len(ydata) > max_points:
            kde_line = line
            max_points = len(ydata)
    if kde_line is not None:
        kde_ymax = np.max(kde_line.get_ydata())
    else:
        kde_ymax = 1  # Fallback

    x_lg = np.linspace(mean-3*std, mean+3*std, 100)
    pdf_long = stats.norm.pdf(x_lg, loc=mean, scale=std)
    pdf_long_sc = pdf_long * kde_ymax / np.max(pdf_long)
    ax.plot(x_lg, pdf_long_sc, color=negre, linewidth=0.8, label=f'{tr['long_term_norm']}')
    
    x_sh = np.linspace(mean-3*std_short, mean+3*std_short, 100)
    pdf_short = stats.norm.pdf(x_sh, loc=mean, scale=std_short)
    pdf_short_sc = pdf_short * kde_ymax / np.max(pdf_short)
    ax.plot(x_sh, pdf_short_sc, color=taronja, linestyle='--', linewidth=0.8, label=f'{tr['short_term_norm']}')

    # Plot LSL, USL, Nominal, Mean
    ax.axvline(lsl, color=vermell, linestyle='-', linewidth=0.8)  # No label
    ax.axvline(usl, color=vermell, linestyle='-', linewidth=0.8)  # No label
    ax.axvline(nominal, color=verd, linestyle='-', linewidth=0.8)
    ax.axvline(mean, color=negre, linestyle='--', linewidth=0.8)
    
    # Add LSL/USL as text above the lines
    ymax = ax.get_ylim()[1]
    ax.text(lsl, ymax * 0.94, f'LSL ({lsl:.2f})', color=vermell, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.text(usl, ymax * 0.94, f'USL ({usl:.2f})', color=vermell, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.text(nominal, ymax * 0.94, f'$x_{{0}}$ ({nominal:.3f})', color=verd, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))

    # Calculate x_min and x_max to always include lsl and usl
    x_min = min(min(mostra), mean - 3*std, lsl)
    x_max = max(max(mostra), mean + 3*std, usl)
    x_margin = 0.02 * (x_max - x_min)
    ax.set_xlim(x_min - x_margin, x_max + x_margin)

    ax.set_title(tr['histogram_kde'], fontsize=13, fontname=font_name)
    ax.set_xlabel(tr['value'], fontsize=11, fontname=font_name)
    ax.set_ylabel(tr['frequency'], fontsize=11, fontname=font_name)
    
    ax.legend(fontsize=8, prop={'family': font_name}, markerscale=1, handlelength=0.7,
              borderpad=0.3, labelspacing=0.2, handletextpad=0.3, loc='right', frameon=True, framealpha=0.95)

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
        sample = np.random.choice(mostra, size=len(mostra), replace=True)   # Resample with replacement from mostra
        osm_b, osr_b = stats.probplot(sample, dist="norm", fit=False)       # Get theoretical and sample quantiles for the bootstrap sample
        reg_b = stats.linregress(osm_b, osr_b)                              # Fit a line to the bootstrap sample's Q-Q plot
        boot_lines.append(reg_b.slope * np.array(osm) + reg_b.intercept)    # Calculate the fitted line at the original osm points
    boot_lines = np.array(boot_lines)
    # Calculate the 2.5th and 97.5th percentiles for each point (95% confidence interval)
    lower_bound = np.percentile(boot_lines, 2.5, axis=0)
    upper_bound = np.percentile(boot_lines, 97.5, axis=0)

    # Plot the 95% confidence band as a shaded area
    ax.fill_between(osm, lower_bound, upper_bound, color=gris, alpha=0.25, label=tr['confidence_qq'])
    
    ax.plot(osm, slope * np.array(osm) + intercept, color=vermell, linewidth=2, zorder=2, label=tr['normal_fit'])   # Plot the Q-Q line (fit to your data)
    ax.scatter(osm, osr, color=blau, edgecolor=negre, linewidths=0.5, s=50, zorder=3, label=tr['sample_quantiles']) # Plot the sample quantiles as points

    ax.set_title(tr['qq_plot'], fontsize=13, fontname=font_name)
    ax.set_xlabel(tr['theoretical_quantiles'], fontsize=11, fontname=font_name)
    ax.set_ylabel(tr['sample_quantiles'], fontsize=11, fontname=font_name)

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
def plt_extrapolated_sample(mostra, nominal, tol, mu, std, element_name, pp=None, ppk=None, pval=None, is_normal=None, save=True, display=False, language='ca'):
    tr = translations[language]
    x = np.linspace(mu - 3*std, mu + 3*std, 200)
    p = stats.norm.pdf(x, mu, std)
    hist_range = max(max(mostra), mu + 3*std) - min(min(mostra), mu - 3*std)
    lsl = nominal + tol[0]
    usl = nominal + tol[1]

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
    
    # Histogram and KDE
    sns.histplot(
        mostra, bins=30, kde=True, stat="count", alpha=0.6, color=blau, edgecolor='k',
        label=tr['histogram_kde'] if 'histogram_kde' in tr else "Histogram and KDE"
    )
    # Normal fit line
    plt.plot(
        x, p * len(mostra) * hist_range / 30, negre, linewidth=1,
        label=f"$\\bar{{x}}$ = {mu:.4f}, $\\sigma$ = {std:.4f}"
    )
    # LSL, USL, Nominal
    plt.axvline(nominal + tol[0], color=vermell, linestyle='-', linewidth=0.75)
    plt.axvline(nominal + tol[1], color=vermell, linestyle='-', linewidth=0.75)
    plt.axvline(nominal, color=verd, linestyle='-', linewidth=0.75)
    plt.axvline(mu, color=negre, linestyle='--', linewidth=0.75)
    plt.fill_between(
        x, 0, p * len(mostra) * hist_range / 30,
        where=(x < nominal + tol[0]) | (x > nominal + tol[1]),
        color=vermell_clar, alpha=0.4
    )
    ymax = ax.get_ylim()[1]
    ax.text(lsl, ymax * 0.95, f'LSL ({lsl:.2f})', color=vermell, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.text(usl, ymax * 0.95, f'USL ({usl:.2f})', color=vermell, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.text(nominal, ymax * 0.95, f'$x_{{0}}$ ({nominal:.2f})', color=verd, fontsize=9, fontname=font_name,
            ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))

    plt.xlabel(tr['distribution_xlabel'] if 'distribution_xlabel' in tr else 'Measured Values', fontsize=14, fontname=font_name)
    plt.ylabel(tr['distribution_ylabel'] if 'distribution_ylabel' in tr else 'Frequency', fontsize=14, fontname=font_name)
    # Title
    ax.set_title(
        tr['distribution_title'].format(element=element_name) if 'distribution_title' in tr else f'Measurement Distribution - {element_name}',
        fontsize=16, fontname=font_name, pad=22
    )

    # Subtitle (as a second text, not superposed)
    subtitle = ""
    if pp is not None and ppk is not None:
        subtitle += (tr['subtitle_pp_ppk'].format(pp=pp, ppk=ppk) + "   ") if 'subtitle_pp_ppk' in tr else f"Pp = {pp:.3f}, Ppk = {ppk:.3f}   "
    if pval is not None:
        subtitle += (tr['subtitle_pval'].format(pval=pval) + "   ") if 'subtitle_pval' in tr else f"p-value = {pval:.4f}   "
    if is_normal is not None:
        subtitle += (tr['subtitle_normal'].format(normal=tr['yes'] if is_normal else tr['no']) if 'subtitle_normal' in tr and 'yes' in tr and 'no' in tr
                     else f"Normal: {'Yes' if is_normal else 'No'}")

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
        
# ------------------------------------------ Gràfic I ------------------------------------------ #
def i_chart(mostra, nominal, tol, mu, mr, element, pp=None, ppk=None, save=True, display=False, language='en'):
    """
    Professional I-Chart for automotive capability studies.
    """
    tr = translations[language]
    indices = np.arange(1, len(mostra) + 1)
    LSL = nominal + tol[0]
    USL = nominal + tol[1]
    CL = mu
    D4 = 2.659816
    UCL = mu + D4 * mr
    LCL = mu - D4 * mr

    # Determine point colors: blue if in spec, red if out of spec
    point_colors = [blau if (LSL <= v <= USL) else vermell for v in mostra]

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
        zorder=4
    )

    # Control limits
    plt.axhline(UCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=tr['ucl_label'].format(ucl=UCL))
    plt.axhline(LCL, color=vermell, linestyle="-", linewidth=1, zorder=2, label=tr['lcl_label'].format(lcl=LCL))

    # Specification limits (red solid)
    #plt.axhline(USL, color=gris, linestyle="--", alpha=0.5, linewidth=0.5, zorder=5, label=tr['usl_label'].format(usl=USL))
    #plt.axhline(LSL, color=gris, linestyle="--", alpha=0.5, linewidth=0.5, zorder=5, label=tr['lsl_label'].format(lsl=LSL))

    # Mean (black solid)
    plt.axhline(CL, color=verd, linestyle="-", linewidth=0.8, zorder=2, label=tr['mean_legend'].format(mean=mu))

    # Nominal (green dash-dot)
    #plt.axhline(nominal, color="#156315", linestyle="-", linewidth=0.8, zorder=2, label=tr['nominal_label'].format(nominal=nominal))
    
    # Title and subtitle with blank space between them and the chart
    ax = plt.gca()
    # Title
    ax.set_title(
        tr['individual_chart'].format(element=element),
        fontsize=15,
        fontname="Times New Roman",
        pad=30  # More space below title
    )
    # Subtitle (as a second text, not superposed)
    subtitle = f"{tr['process performance']}: Pp = {pp:.2f}, Ppk = {ppk:.2f}" if pp is not None and ppk is not None else ""
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

    plt.xlabel(tr['index_piece'], fontsize=12, fontname="Times New Roman")
    plt.ylabel(tr['value_measured'], fontsize=12, fontname="Times New Roman")
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
        filename = os.path.join(output_dir, f"{element}_IChart.png")
        plt.savefig(filename, format="png")
        plt.close()
    if display:
        plt.show()
        plt.close()

# ------------------------------------------ Gràfic R_m ------------------------------------------ #
def rm_chart(mostra, element_name, save=True, display=False, language='en'):
    """
    Moving Range (MR) chart for capability studies, with translation support.
    """
    tr = translations[language]
    mostra = np.asarray(mostra)
    # Calculate moving ranges
    mr = np.abs(np.diff(mostra))
    indices = np.arange(2, len(mostra) + 1)  # MR is defined from the second observation

    # Control line, CL.
    MR_bar = np.mean(mr)
    d2 = 1.128
    sigma_est = MR_bar / d2
    # D4 and D3 for n=2
    D4 = 3.267
    D3 = 0
    UCL = D4 * MR_bar
    LCL = D3 * MR_bar  # Always 0 by definition

    plt.figure(figsize=(10, 6))
    plt.grid(True, linestyle=":", alpha=0.4, zorder=0)

    # Plot moving ranges
    plt.plot(indices, mr, marker='o', color=blau, linewidth=1, zorder=3)
    plt.scatter(indices, mr, color=blau, edgecolor=negre, s=60, zorder=4)

    # Control lines
    plt.axhline(UCL, color=vermell, linestyle="-", linewidth=0.75, zorder=2, label=tr['ucl_label'].format(ucl=UCL))
    plt.axhline(MR_bar, color=negre, linestyle="-", linewidth=0.75, zorder=2, label=f'$\\bar{{MR}}$ = {MR_bar:.3f}')
    plt.axhline(LCL, color=vermell, linestyle="-", linewidth=0.75, zorder=2, label=tr['lcl_label'].format(lcl=LCL))

    # Titles and labels
    ax = plt.gca()
    ax.set_title(
        tr['moving_range_chart'].format(element=element_name),
        fontsize=15,
        fontname="Times New Roman",
        pad=30
    )
    # Subtitle
    subtitle = tr['estimated_sigma'].format(sigma=sigma_est)
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

    plt.xlabel(tr['index_piece'], fontsize=12, fontname="Times New Roman")
    plt.ylabel(tr['mobile_range'], fontsize=12, fontname="Times New Roman")
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

# ------------------------------------------------- Gràfica de 'capacitat' ------------------------------------------------- #
def capability_chart(element, mean, std_short, std_long, usl, lsl, pp, ppk, ppm_long, cp, cpk, ppm_short, save=False, display=False, language='ca'):
    tr = translations[language]

    # Prepare labels and values
    curt_text = tr['short_term'] if 'short_term' in tr else "Short Term"
    llarg_text = tr['long_term'] if 'long_term' in tr else "Long Term"
    labels = {
        "Desv.Est.": tr['Std_capchart'] if 'Std_capchart' in tr else "Std. Dev.",
        "Cp": tr['Cp'] if 'Cp' in tr else "Cp",
        "Cpk": tr['Cpk'] if 'Cpk' in tr else "Cpk",
        "PPM": tr['PPM'] if 'PPM' in tr else "PPM",
        "Pp": tr['Pp'] if 'Pp' in tr else "Pp",
        "Ppk": tr['Ppk'] if 'Ppk' in tr else "Ppk"
    }

    fig = plt.figure(figsize=(9, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2.2, 1])
    ax = fig.add_subplot(gs[0])
    plt.rcParams["font.family"] = "Times New Roman"

    x_points = [
        lsl,
        usl,
        mean - 3 * std_short,
        mean + 3 * std_short,
        mean - 3 * std_long,
        mean + 3 * std_long,
        mean
    ]

    x_min = min(x_points)
    x_max = max(x_points)
    x_margin = 0.02 * (x_max - x_min) if x_max > x_min else 1  # Avoid zero margin if all points are equal

    # Add margin
    scale_min = x_min - x_margin
    scale_max = x_max + x_margin
        
    for y_pos, label in zip([2, 1, 0], [tr['long_term'], tr['short_term'], tr['specifications']]):
        ax.text(scale_min - 0.01 * abs(scale_max - scale_min), y_pos, label,
                verticalalignment='center', fontsize=10, fontname="Times New Roman", fontweight='normal', rotation=90, ha='right')
    ax.hlines(y=0, xmin=lsl, xmax=usl, color=vermell, linestyle='-', linewidth=1)
    ax.hlines(y=1, xmin=mean - 3 * std_short, xmax=mean + 3 * std_short, color=blau, linestyle='-', linewidth=1)
    ax.hlines(y=2, xmin=mean - 3 * std_long, xmax=mean + 3 * std_long, color=blau, linestyle='-', linewidth=1)
    ax.plot([lsl, usl], [0, 0], 's', color=vermell, markersize=5, zorder=6) # Specs (red)
    ax.plot([mean - 3 * std_short, mean + 3 * std_short], [1, 1], '+', color="#0B034E", markersize=7, zorder=6) # Short term (blue)
    ax.plot([mean - 3 * std_long, mean + 3 * std_long], [2, 2], '+', color="#0B034E", markersize=7, zorder=6)   # Long term (blue)
    # Points at the mean for the two blue lines
    ax.plot(mean, 1, 'x', color=negre, markersize=6, zorder=7)
    ax.plot(mean, 2, 'x', color=negre, markersize=6, zorder=7)
    ax.vlines(mean, -0.3, 2.7, color=negre, linestyle='-.', linewidth=0.75, zorder=5)
    ax.vlines(usl, -0.5, 2.7, color=vermell, linestyle='--', linewidth=0.75)
    ax.vlines(lsl, -0.5, 2.7, color=vermell, linestyle='--', linewidth=0.75)
    ax.text(usl, 2.5, tr['usl_label'].format(usl=usl), color=vermell, fontsize=9, fontname="Times New Roman", ha='center', va='bottom',
        bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.text(lsl, 2.5, tr['lsl_label'].format(lsl=lsl), color=vermell, fontsize=9, fontname="Times New Roman", ha='center', va='bottom',
        bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
    ax.set_ylim(-0.3, 2.7)
    # Collect all relevant X points

    ax.set_xlim(scale_min, scale_max)
    ax.set_yticks([])
    ax.set_xlabel(tr['value_measured'] if 'value_measured' in tr else "Measured Value", fontsize=10, fontname="Times New Roman")
    # Make X axis tick labels smaller and Times New Roman
    for label in ax.get_xticklabels():
        label.set_fontsize(9)
        label.set_fontname("Times New Roman")
    title = tr['process_capability_plot'] if 'process_capability_plot' in tr else "Process Capability Plot"
    subtitle = f"{tr['mean']}: {mean:.5f}"
    ax.set_title(title, fontsize=15, fontname="Times New Roman", pad=28)
    ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha='center', fontsize=11, fontname="Times New Roman", color=gris, va='bottom')
    plt.grid(True, axis='both', linestyle='--', alpha=0.4)

    # Info box on the right using Table for full control
    axbox = fig.add_subplot(gs[1])
    axbox.axis('off')
    wd = 0.5

    # Short term table
    short_table = Table(axbox, bbox=[0, 0.55, 1, 0.35])
    # Header: one cell spanning both columns
    short_table.add_cell(0, 0, width=0.5, height=0.18, text=curt_text, loc='center', facecolor="#e6e6f2")
    # Data rows
    short_table.add_cell(1, 0, width=wd, height=0.13, text=labels["Cp"], loc='left', facecolor="#f9f9f9")
    short_table.add_cell(1, 1, width=wd, height=0.13, text=f"{cp:.4f}", loc='left')
    short_table.add_cell(2, 0, width=wd, height=0.13, text=labels["Cpk"], loc='left', facecolor="#f9f9f9")
    short_table.add_cell(2, 1, width=wd, height=0.13, text=f"{cpk:.4f}", loc='left')
    short_table.add_cell(3, 0, width=wd, height=0.13, text=labels["PPM"], loc='left', facecolor="#f9f9f9")
    short_table.add_cell(3, 1, width=wd, height=0.13, text=f"{ppm_short:.2f}", loc='left')
    short_table.add_cell(4, 0, width=wd, height=0.13, text=labels["Desv.Est."], loc='left', facecolor="#f9f9f9")
    short_table.add_cell(4, 1, width=wd, height=0.13, text=f"{std_short:.5f}", loc='left')

    # Style header
    header_cell = short_table[(0, 0)]
    header_cell.get_text().set_fontname("Times New Roman")
    header_cell.get_text().set_fontsize(14)
    header_cell.get_text().set_weight('normal')
    header_cell.get_text().set_ha('center')
    header_cell.visible_edges = 'open'

    # Style data cells
    for i in range(1, 5):
        for j in range(2):
            cell = short_table[(i, j)]
            cell.get_text().set_fontname("Times New Roman")
            cell.get_text().set_fontsize(10)
            cell.get_text().set_weight('normal')
            if j == 0:
                cell.set_facecolor("#f9f9f9")

    # Table borders and alternating row colors
    for key, cell in short_table.get_celld().items():
        cell.set_linewidth(0.5)
        cell.set_edgecolor("#CCCCCC")
        if key[0] == 0:
            cell.set_facecolor("#e6e6f2")
        elif key[0] % 2 == 1:
            cell.set_facecolor("#f7f7fa")
        else:
            cell.set_facecolor("#ffffff")

    axbox.add_table(short_table)

    # White space between tables
    axbox.text(0.5, 0.48, "", ha='center', va='center', fontsize=2, color='white')

    # Long term table
    long_table = Table(axbox, bbox=[0, 0.05, 1, 0.35])
    # Header: one cell spanning both columns
    long_table.add_cell(0, 0, width=0.5, height=0.18, text=llarg_text, loc='center', facecolor="#e6e6f2")
    # Data rows
    long_table.add_cell(1, 0, width=wd, height=0.13, text=labels["Pp"], loc='left', facecolor="#f9f9f9")
    long_table.add_cell(1, 1, width=wd, height=0.13, text=f"{pp:.4f}", loc='left')
    long_table.add_cell(2, 0, width=wd, height=0.13, text=labels["Ppk"], loc='left', facecolor="#f9f9f9")
    long_table.add_cell(2, 1, width=wd, height=0.13, text=f"{ppk:.4f}", loc='left')
    long_table.add_cell(3, 0, width=wd, height=0.13, text=labels["PPM"], loc='left', facecolor="#f9f9f9")
    long_table.add_cell(3, 1, width=wd, height=0.13, text=f"{ppm_long:.2f}", loc='left')
    long_table.add_cell(4, 0, width=wd, height=0.13, text=labels["Desv.Est."], loc='left', facecolor="#f9f9f9")
    long_table.add_cell(4, 1, width=wd, height=0.13, text=f"{std_long:.5f}", loc='left')

    # Style header
    header_cell = long_table[(0, 0)]
    header_cell.get_text().set_fontname("Times New Roman")
    header_cell.get_text().set_fontsize(14)
    header_cell.get_text().set_weight('normal')
    header_cell.get_text().set_ha('center')
    header_cell.visible_edges = 'open'

    # Style data cells
    for i in range(1, 5):
        for j in range(2):
            cell = long_table[(i, j)]
            cell.get_text().set_fontname("Times New Roman")
            cell.get_text().set_fontsize(10)
            cell.get_text().set_weight('normal')
            if j == 0:
                cell.set_facecolor("#f9f9f9")

    # Table borders and alternating row colors
    for key, cell in long_table.get_celld().items():
        cell.set_linewidth(0.5)
        cell.set_edgecolor("#CCCCCC")
        if key[0] == 0:
            cell.set_facecolor("#e6e6f2")
        elif key[0] % 2 == 1:
            cell.set_facecolor("#f7f7fa")
        else:
            cell.set_facecolor("#ffffff")

    axbox.add_table(long_table)

    plt.tight_layout()
    if save:
        filename = os.path.join(output_dir, f"{element}_Capability_chart.png")
        plt.savefig(filename, format="png")
        plt.close()
    if display:
        plt.show()
        plt.close()

# ------------------------------------------ Main ------------------------------------------ #
def main():
    os.makedirs(output_dir, exist_ok=True)  # Crear carpeta si no existeix
    df = get_sample_data()                  # For now, use hardcoded sample data

    for i, row in df.iterrows():
        element = str(row['Element']).replace(' ', '_')
        print(f"\nProcessing element: {element} (Row {i+1}/{len(df)})\n")
        nominal = row['Nominal']
        tolerance = [row['Tol-'], row['Tol+']]
        mostra = np.array(row['Values'], dtype=float)
# --------------------------------------------- Càlcul dels paràmetres i indicadors estadístics --------------------------------------------- #
        lsl = nominal + tolerance[0]
        usl = nominal + tolerance[1]
        mu, std_long, std_short, is_normal, ad_stat = analisi_mostra(mostra)
        pval_ad = pvalor_approx(ad_stat) # Approximate p-value for A² statistic
        mu, std_long, std_short, pval_ad = [round(x, 6) for x in (mu, std_long, std_short, pval_ad)]
    # ------------------- Procés a llarg termini (PPK i PP) ------------------- #
        cp, cpk = index_proces(element, nominal, mu, std_short, tolerance)
        ppm_short = ppm_calc(nominal, tolerance, mu, std_short)
        pp, ppk = index_proces(element, nominal, mu, std_long, tolerance)
        ppm_long = ppm_calc(nominal, tolerance, mu, std_long)
# ----------------------------------------------------- Gràfics ----------------------------------------------------- #
        plt_sample_analysis(mostra, nominal, tolerance, element, std_short, pval_ad, ad_stat, is_normal, save, display, lan) # Gràfics d’anàlisi
        MR_bar = rm_chart(mostra, element, save, display, lan)  
        i_chart(mostra, nominal, tolerance, mu, MR_bar, element, pp, ppk, save, display, lan)  # I-Chart
        capability_chart(element, mu, std_short, std_long, usl, lsl, pp, ppk, ppm_long, cp, cpk, ppm_short, save, display, lan)

        final_values, A_2, pval_e, extrap = extrapolar(mostra, nominal, tolerance[0])
        norm = None
        if pval_e is not None and pval_e > 0.05:
            norm = True
        elif pval_e is not None and pval_e <= 0.05:
            norm = False
        print(f"\nFinal sample n={len(final_values)}, {norm}.")

        if A_2 is None or pval_e is None:
            plt_extrapolated_sample(mostra, nominal, tolerance, mu, std_long, element, pp, ppk, pval_ad, is_normal, save, display, lan)
            continue

        print(f"[{element}] Anderson-Darling A² = {A_2:.4f}, p-valor ≈ {pval_e:.4f}")

        if extrap:
            plt_extrapolated_sample(final_values, nominal, tolerance, mu, std_long, element, pp, ppk, pval_e, norm, save, display, lan)
            continue          

        # Save to CSV
        out_csv = os.path.join(output_dir, f"{element}_extrapolated.csv")
        pd.DataFrame({'Extrapolated_Value': final_values}).to_csv(out_csv, index=False)


if __name__ == "__main__":
    # You can change n_vals here (e.g., 30, 50, 100, 500)
    main()
