import os
import logging
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
import numpy as np

# Configure comprehensive logging
def setup_logging(log_level=logging.INFO, log_file="capability_chart.log"):
    """
    Set up comprehensive logging configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("CAPABILITY CHART LOGGING SESSION STARTED")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info("="*50)
    
    return logger

# Initialize logger
logger = setup_logging(log_level=logging.DEBUG, log_file="logs/capability_chart.log")

# Define your colors (vermell = red, blau = blue, negre = black)
vermell = "#D62728"
blau = "#1F77B4"
negre = "#000000"

def validate_inputs(element, mean, std_short, std_long, usl, lsl, pp, ppk, ppm_long, cp, cpk, ppm_short):
    """
    Validate all input parameters for the capability chart
    """
    logger.info("Starting input validation...")
    
    validation_errors = []
    
    # Check element name
    if not element or not isinstance(element, str):
        validation_errors.append("Element name must be a non-empty string")
    else:
        logger.debug(f"Element name valid: '{element}'")
    
    # Check numeric parameters
    numeric_params = {
        'mean': mean,
        'std_short': std_short,
        'std_long': std_long,
        'usl': usl,
        'lsl': lsl,
        'pp': pp,
        'ppk': ppk,
        'ppm_long': ppm_long,
        'cp': cp,
        'cpk': cpk,
        'ppm_short': ppm_short
    }
    
    for param_name, param_value in numeric_params.items():
        if not isinstance(param_value, (int, float)):
            validation_errors.append(f"{param_name} must be a number")
        elif np.isnan(param_value) or np.isinf(param_value):
            validation_errors.append(f"{param_name} cannot be NaN or infinite")
        else:
            logger.debug(f"{param_name} = {param_value}")
    
    # Check logical relationships
    if isinstance(usl, (int, float)) and isinstance(lsl, (int, float)):
        if usl <= lsl:
            validation_errors.append("USL must be greater than LSL")
        else:
            logger.debug(f"Specification limits valid: LSL={lsl}, USL={usl}")
    
    # Check standard deviations are positive
    if isinstance(std_short, (int, float)) and std_short <= 0:
        validation_errors.append("Short-term standard deviation must be positive")
    if isinstance(std_long, (int, float)) and std_long <= 0:
        validation_errors.append("Long-term standard deviation must be positive")
    
    # Check PPM values are non-negative
    if isinstance(ppm_short, (int, float)) and ppm_short < 0:
        validation_errors.append("Short-term PPM cannot be negative")
    if isinstance(ppm_long, (int, float)) and ppm_long < 0:
        validation_errors.append("Long-term PPM cannot be negative")
    
    if validation_errors:
        logger.error("Input validation failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        raise ValueError("Input validation failed: " + "; ".join(validation_errors))
    
    logger.info("All input parameters validated successfully")
    return True

def capability_chart(
    element,
    mean,
    std_short,
    std_long,
    usl,
    lsl,
    pp,
    ppk,
    ppm_long,
    cp,
    cpk,
    ppm_short,
    save=False,
    display=False,
    language='ca',
    translations=None,
    output_dir="./output"
):
    """
    Create a capability chart with comprehensive logging
    """
    logger.info(f"Starting capability chart generation for element: {element}")
    logger.info(f"Parameters: mean={mean}, std_short={std_short}, std_long={std_long}")
    logger.info(f"Limits: LSL={lsl}, USL={usl}")
    logger.info(f"Capability indices: Cp={cp}, Cpk={cpk}, Pp={pp}, Ppk={ppk}")
    logger.info(f"PPM values: short={ppm_short}, long={ppm_long}")
    logger.info(f"Settings: save={save}, display={display}, language={language}")
    
    try:
        # Validate inputs
        validate_inputs(element, mean, std_short, std_long, usl, lsl, pp, ppk, ppm_long, cp, cpk, ppm_short)
        
        # Set up translations
        if translations is None:
            logger.debug("Using default translations")
            translations = {
                'ca': {
                    'short_term': "Curt Termini",
                    'long_term': "Llarg Termini",
                    'specifications': "Especificacions",
                    'Std_capchart': "Desv.Est.",
                    'Cp': "Cp",
                    'Cpk': "Cpk",
                    'PPM': "PPM",
                    'Pp': "Pp",
                    'Ppk': "Ppk",
                    'usl_label': "USL = {usl}",
                    'lsl_label': "LSL = {lsl}",
                    'value_measured': "Valor mesurat",
                    'process_capability_plot': "Diagrama de capacitat: {element}",
                    'mean': "Mitjana"
                }
            }
        
        tr = translations.get(language, translations['ca'])
        logger.debug(f"Using translations for language: {language}")
        
        curt_text = tr.get('short_term', "Short Term")
        llarg_text = tr.get('long_term', "Long Term")
        
        labels = {
            "Desv.Est.": tr.get('Std_capchart', "Std. Dev."),
            "Cp": tr.get('Cp', "Cp"),
            "Cpk": tr.get('Cpk', "Cpk"),
            "PPM": tr.get('PPM', "PPM"),
            "Pp": tr.get('Pp', "Pp"),
            "Ppk": tr.get('Ppk', "Ppk"),
        }
        
        # Create figure and grid
        logger.info("Creating matplotlib figure and grid layout")
        fig = plt.figure(figsize=(9, 6))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2.2, 1])
        ax = fig.add_subplot(gs[0])
        plt.rcParams["font.family"] = "Times New Roman"
        logger.debug("Figure and axes created successfully")
        
        # Calculate scale parameters
        logger.info("Calculating chart scale parameters")
        x_points = [lsl, usl, mean - 3 * std_short, mean + 3 * std_short, mean - 3 * std_long, mean + 3 * std_long, mean]
        x_min = min(x_points)
        x_max = max(x_points)
        x_margin = 0.02 * (x_max - x_min) if x_max > x_min else 1
        scale_min = x_min - x_margin
        scale_max = x_max + x_margin
        
        logger.debug(f"Scale parameters: min={scale_min:.4f}, max={scale_max:.4f}")
        logger.debug(f"Chart range: {scale_max - scale_min:.4f}")
        
        # Add row labels
        logger.info("Adding row labels for specifications and capability ranges")
        for y_pos, label in zip([2, 1, 0], [tr['long_term'], tr['short_term'], tr['specifications']]):
            ax.text(scale_min - 0.01 * abs(scale_max - scale_min), y_pos, label,
                    verticalalignment='center', fontsize=10, fontname="Times New Roman",
                    fontweight='normal', rotation=90, ha='right')
        
        # Draw horizontal lines for specs and capability ranges
        logger.info("Drawing horizontal lines for specifications and capability ranges")
        ax.hlines(y=0, xmin=lsl, xmax=usl, color=vermell, linestyle='-', linewidth=1)
        ax.hlines(y=1, xmin=mean - 3 * std_short, xmax=mean + 3 * std_short, color=blau, linestyle='-', linewidth=1)
        ax.hlines(y=2, xmin=mean - 3 * std_long, xmax=mean + 3 * std_long, color=blau, linestyle='-', linewidth=1)
        
        # Add markers
        logger.info("Adding markers for limits and mean")
        ax.plot([lsl, usl], [0, 0], 's', color=vermell, markersize=5, zorder=6)
        ax.plot([mean - 3 * std_short, mean + 3 * std_short], [1, 1], '+', color=blau, markersize=7, zorder=6)
        ax.plot([mean - 3 * std_long, mean + 3 * std_long], [2, 2], '+', color=blau, markersize=7, zorder=6)
        ax.plot(mean, 1, 'x', color=negre, markersize=6, zorder=7)
        ax.plot(mean, 2, 'x', color=negre, markersize=6, zorder=7)
        
        # Add vertical lines
        logger.info("Drawing vertical reference lines")
        ax.vlines(mean, -0.3, 2.7, color=negre, linestyle='-.', linewidth=0.75, zorder=5)
        ax.vlines(usl, -0.5, 2.7, color=vermell, linestyle='--', linewidth=0.75)
        ax.vlines(lsl, -0.5, 2.7, color=vermell, linestyle='--', linewidth=0.75)
        
        # Add limit labels
        logger.info("Adding USL and LSL labels")
        ax.text(usl, 2.5, tr['usl_label'].format(usl=usl), color=vermell,
                fontsize=9, fontname="Times New Roman", ha='center', va='bottom',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
        ax.text(lsl, 2.5, tr['lsl_label'].format(lsl=lsl), color=vermell,
                fontsize=9, fontname="Times New Roman", ha='center', va='bottom',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.1'))
        
        # Set axis properties
        logger.info("Setting axis properties and labels")
        ax.set_ylim(-0.3, 2.7)
        ax.set_xlim(scale_min, scale_max)
        ax.set_yticks([])
        ax.set_xlabel(tr.get('value_measured', "Measured Value"), fontsize=10, fontname="Times New Roman")
        
        for label in ax.get_xticklabels():
            label.set_fontsize(9)
            label.set_fontname("Times New Roman")
        
        # Add title and subtitle
        title = tr.get('process_capability_plot', "Process Capability Plot").format(element=element)
        subtitle = f"{tr.get('mean', 'Mean')}: {mean:.4f}"
        ax.set_title(title, fontsize=15, fontname="Times New Roman", pad=28)
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha='center',
                fontsize=11, fontname="Times New Roman", color="#444444", va='bottom')
        
        plt.grid(True, axis='both', linestyle='--', alpha=0.4)
        logger.debug("Main chart completed successfully")
        
        # Create info tables
        logger.info("Creating capability information tables")
        axbox = fig.add_subplot(gs[1])
        axbox.axis('off')
        wd = 0.5
        
        # Short term table
        logger.debug("Creating short-term capability table")
        short_table = Table(axbox, bbox=[0, 0.55, 1, 0.35])
        short_table.add_cell(0, 0, width=0.5, height=0.25, text=curt_text, loc='center', facecolor="#e6e6f2")
        short_table.add_cell(1, 0, width=wd, height=0.2, text=labels["Cp"], loc='left', facecolor="#f9f9f9")
        short_table.add_cell(1, 1, width=wd, height=0.2, text=f"{cp:.2f}", loc='left')
        short_table.add_cell(2, 0, width=wd, height=0.2, text=labels["Cpk"], loc='left', facecolor="#f9f9f9")
        short_table.add_cell(2, 1, width=wd, height=0.2, text=f"{cpk:.2f}", loc='left')
        short_table.add_cell(3, 0, width=wd, height=0.2, text=labels["PPM"], loc='left', facecolor="#f9f9f9")
        short_table.add_cell(3, 1, width=wd, height=0.2, text=f"{ppm_short:.2f}", loc='left')
        short_table.add_cell(4, 0, width=wd, height=0.2, text=labels["Desv.Est."], loc='left', facecolor="#f9f9f9")
        short_table.add_cell(4, 1, width=wd, height=0.2, text=f"{std_short:.4f}", loc='left')
        
        # Style short term table
        logger.debug("Styling short-term table")
        header_cell = short_table[(0, 0)]
        header_cell.get_text().set_fontname("Times New Roman")
        header_cell.get_text().set_fontsize(14)
        header_cell.get_text().set_weight('normal')
        header_cell.get_text().set_ha('center')
        header_cell.visible_edges = 'open'
        
        for i in range(1, 5):
            for j in range(2):
                cell = short_table[(i, j)]
                cell.get_text().set_fontname("Times New Roman")
                cell.get_text().set_fontsize(10)
                if j == 0:
                    cell.set_facecolor("#f9f9f9")
                    cell.get_text().set_weight("normal")
                else:
                    cell.get_text().set_weight("bold")
        
        axbox.add_table(short_table)
        
        # Long term table
        logger.debug("Creating long-term capability table")
        long_table = Table(axbox, bbox=[0, 0.05, 1, 0.45])
        long_table.add_cell(0, 0, width=0.5, height=0.25, text=llarg_text, loc='center', facecolor="#d9f2d9")
        long_table.add_cell(1, 0, width=wd, height=0.2, text=labels["Pp"], loc='left', facecolor="#f9fff9")
        long_table.add_cell(1, 1, width=wd, height=0.2, text=f"{pp:.2f}", loc='left')
        long_table.add_cell(2, 0, width=wd, height=0.2, text=labels["Ppk"], loc='left', facecolor="#f9fff9")
        long_table.add_cell(2, 1, width=wd, height=0.2, text=f"{ppk:.2f}", loc='left')
        long_table.add_cell(3, 0, width=wd, height=0.2, text=labels["PPM"], loc='left', facecolor="#f9fff9")
        long_table.add_cell(3, 1, width=wd, height=0.2, text=f"{ppm_long:.2f}", loc='left')
        long_table.add_cell(4, 0, width=wd, height=0.2, text=labels["Desv.Est."], loc='left', facecolor="#f9fff9")
        long_table.add_cell(4, 1, width=wd, height=0.2, text=f"{std_long:.4f}", loc='left')
        
        # Style long term table
        logger.debug("Styling long-term table")
        header_cell_long = long_table[(0, 0)]
        header_cell_long.get_text().set_fontname("Times New Roman")
        header_cell_long.get_text().set_fontsize(14)
        header_cell_long.get_text().set_weight('normal')
        header_cell_long.get_text().set_ha('center')
        header_cell_long.visible_edges = 'open'
        
        for i in range(1, 5):
            for j in range(2):
                cell = long_table[(i, j)]
                cell.get_text().set_fontname("Times New Roman")
                cell.get_text().set_fontsize(10)
                if j == 0:
                    cell.set_facecolor("#f9fff9")
                    cell.get_text().set_weight("normal")
                else:
                    cell.get_text().set_weight("bold")
        
        axbox.add_table(long_table)
        logger.debug("Both tables created and styled successfully")
        
        plt.tight_layout()
        logger.info("Chart layout finalized")
        
        # Save chart if requested
        if save:
            logger.info(f"Saving chart to directory: {output_dir}")
            try:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.debug(f"Created output directory: {output_dir}")
                
                save_path = os.path.join(output_dir, f"capability_chart_{element}.png")
                plt.savefig(save_path, dpi=300, bbox_inches="tight")
                logger.info(f"Chart saved successfully to: {save_path}")
                
                # Log file size
                file_size = os.path.getsize(save_path)
                logger.debug(f"Saved file size: {file_size} bytes ({file_size/1024:.1f} KB)")
                
            except Exception as e:
                logger.error(f"Failed to save chart: {e}", exc_info=True)
                raise
        
        # Display chart if requested
        if display:
            logger.info("Displaying chart")
            plt.show()
        
        logger.info("Chart generation completed successfully")
        plt.close(fig)
        
    except Exception as e:
        logger.error(f"Error in capability chart generation: {e}", exc_info=True)
        raise

def calculate_capability_indices(data, usl, lsl):
    """
    Calculate capability indices from data
    """
    logger.info("Calculating capability indices from data")
    
    mean = np.mean(data)
    std_short = np.std(data, ddof=1)  # Sample standard deviation
    std_long = std_short * 1.5  # Simulate long-term variation
    
    # Calculate capability indices
    cp = (usl - lsl) / (6 * std_short)
    cpu = (usl - mean) / (3 * std_short)
    cpl = (mean - lsl) / (3 * std_short)
    cpk = min(cpu, cpl)
    
    pp = (usl - lsl) / (6 * std_long)
    ppu = (usl - mean) / (3 * std_long)
    ppl = (mean - lsl) / (3 * std_long)
    ppk = min(ppu, ppl)
    
    # Calculate PPM (parts per million defective)
    from scipy import stats
    ppm_short = (stats.norm.cdf(lsl, mean, std_short) + 
                 (1 - stats.norm.cdf(usl, mean, std_short))) * 1e6
    ppm_long = (stats.norm.cdf(lsl, mean, std_long) + 
                (1 - stats.norm.cdf(usl, mean, std_long))) * 1e6
    
    logger.debug(f"Calculated indices: Cp={cp:.3f}, Cpk={cpk:.3f}, Pp={pp:.3f}, Ppk={ppk:.3f}")
    logger.debug(f"PPM values: short={ppm_short:.1f}, long={ppm_long:.1f}")
    
    return {
        'mean': mean,
        'std_short': std_short,
        'std_long': std_long,
        'cp': cp,
        'cpk': cpk,
        'pp': pp,
        'ppk': ppk,
        'ppm_short': ppm_short,
        'ppm_long': ppm_long
    }

def create_sample_chart():
    """
    Create a sample capability chart with realistic data
    """
    logger.info("="*50)
    logger.info("CREATING SAMPLE CAPABILITY CHART")
    logger.info("="*50)
    
    try:
        # Generate sample data
        logger.info("Generating sample process data")
        np.random.seed(42)  # For reproducible results
        
        # Simulate a process with target = 100, some variation
        target = 100.0
        process_std = 2.0
        n_samples = 1000
        
        # Generate data with slight process shift
        data = np.random.normal(target + 0.5, process_std, n_samples)
        
        logger.info(f"Generated {n_samples} data points")
        logger.debug(f"Data statistics: mean={np.mean(data):.3f}, std={np.std(data, ddof=1):.3f}")
        logger.debug(f"Data range: {np.min(data):.3f} to {np.max(data):.3f}")
        
        # Define specification limits
        usl = 108.0
        lsl = 92.0
        
        logger.info(f"Specification limits: LSL={lsl}, USL={usl}")
        
        # Calculate capability indices
        capability_data = calculate_capability_indices(data, usl, lsl)
        
        # Create the chart
        logger.info("Generating capability chart")
        capability_chart(
            element="SAMPLE_PROCESS",
            mean=capability_data['mean'],
            std_short=capability_data['std_short'],
            std_long=capability_data['std_long'],
            usl=usl,
            lsl=lsl,
            pp=capability_data['pp'],
            ppk=capability_data['ppk'],
            ppm_long=capability_data['ppm_long'],
            cp=capability_data['cp'],
            cpk=capability_data['cpk'],
            ppm_short=capability_data['ppm_short'],
            save=True,
            display=True,
            language='ca',
            output_dir="./output"
        )
        
        logger.info("Sample capability chart created successfully")
        
        # Log summary statistics
        logger.info("CAPABILITY ANALYSIS SUMMARY:")
        logger.info(f"  Process Mean: {capability_data['mean']:.4f}")
        logger.info(f"  Short-term Std: {capability_data['std_short']:.4f}")
        logger.info(f"  Long-term Std: {capability_data['std_long']:.4f}")
        logger.info(f"  Cp: {capability_data['cp']:.3f}")
        logger.info(f"  Cpk: {capability_data['cpk']:.3f}")
        logger.info(f"  Pp: {capability_data['pp']:.3f}")
        logger.info(f"  Ppk: {capability_data['ppk']:.3f}")
        logger.info(f"  PPM Short-term: {capability_data['ppm_short']:.1f}")
        logger.info(f"  PPM Long-term: {capability_data['ppm_long']:.1f}")
        
        # Provide interpretation
        cpk_interpretation = "Excellent" if capability_data['cpk'] >= 1.67 else \
                           "Good" if capability_data['cpk'] >= 1.33 else \
                           "Acceptable" if capability_data['cpk'] >= 1.0 else \
                           "Poor"
        
        logger.info(f"  Process Capability: {cpk_interpretation} (Cpk = {capability_data['cpk']:.3f})")
        
    except Exception as e:
        logger.error(f"Failed to create sample chart: {e}", exc_info=True)
        raise

def run_comprehensive_test():
    """
    Run comprehensive tests of the capability chart function
    """
    logger.info("="*50)
    logger.info("RUNNING COMPREHENSIVE TESTS")
    logger.info("="*50)
    
    test_cases = [
        {
            'name': 'Good Process',
            'element': 'GOOD_PROCESS',
            'mean': 100.0,
            'std_short': 1.0,
            'std_long': 1.5,
            'usl': 106.0,
            'lsl': 94.0,
            'cp': 2.0,
            'cpk': 1.67,
            'pp': 1.33,
            'ppk': 1.11,
            'ppm_short': 0.1,
            'ppm_long': 10.0
        },
        {
            'name': 'Marginal Process',
            'element': 'MARGINAL_PROCESS',
            'mean': 99.5,
            'std_short': 1.8,
            'std_long': 2.7,
            'usl': 105.0,
            'lsl': 95.0,
            'cp': 0.93,
            'cpk': 0.85,
            'pp': 0.62,
            'ppk': 0.57,
            'ppm_short': 8500.0,
            'ppm_long': 45000.0
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"Running test case {i}: {test_case['name']}")
        try:
            capability_chart(
                element=test_case['element'],
                mean=test_case['mean'],
                std_short=test_case['std_short'],
                std_long=test_case['std_long'],
                usl=test_case['usl'],
                lsl=test_case['lsl'],
                pp=test_case['pp'],
                ppk=test_case['ppk'],
                ppm_long=test_case['ppm_long'],
                cp=test_case['cp'],
                cpk=test_case['cpk'],
                ppm_short=test_case['ppm_short'],
                save=True,
                display=False,
                output_dir="./output/tests"
            )
            logger.info(f"Test case {i} completed successfully")
        except Exception as e:
            logger.error(f"Test case {i} failed: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting capability chart script execution")
    
    try:
        # Create sample chart
        create_sample_chart()
        
        # Run comprehensive tests
        run_comprehensive_test()
        
        logger.info("="*50)
        logger.info("ALL OPERATIONS COMPLETED SUCCESSFULLY")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        logger.error("="*50)
        logger.error("SCRIPT EXECUTION FAILED")
        logger.error("="*50)
        raise
    finally:
        # Close any remaining figures
        plt.close('all')
        logger.info("Script execution finished")