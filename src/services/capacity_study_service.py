# src/services/capacity_study_service.py - CALCULATES AD & P-VALUE
import os
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from scipy import stats

from .spc_chart_service import SPCChartService

logger = logging.getLogger(__name__)


def calculate_anderson_darling(sample: List[float]) -> tuple:
    """
    Calculate Anderson-Darling statistic and approximate p-value for original sample
    
    Returns:
        tuple: (ad_statistic, p_value)
    """
    try:
        sample_array = np.array(sample)
        n = len(sample_array)
        
        if n < 5:
            return 0.0, 0.0
        
        mean = np.mean(sample_array)
        std = np.std(sample_array, ddof=1)
        
        if std == 0:
            return 0.0, 0.0
        
        # Calculate Anderson-Darling statistic manually
        sorted_sample = np.sort(sample_array)
        cdf_vals = stats.norm.cdf(sorted_sample, loc=mean, scale=std)
        cdf_vals = np.clip(cdf_vals, 1e-10, 1 - 1e-10)
        
        i = np.arange(1, n + 1)
        one_minus_cdf_reverse = 1 - cdf_vals[::-1]
        
        s = (2 * i - 1) * (np.log(cdf_vals) + np.log(one_minus_cdf_reverse))
        A_2 = -n - np.sum(s) / n
        A2_corrected = A_2 * (1 + 0.75 / n + 2.25 / (n**2))
        
        # Calculate approximate p-value
        ad_stat = A2_corrected
        if ad_stat >= 0.6:
            p_value = np.exp(1.2937 - 5.709 * ad_stat + 0.0186 * ad_stat**2)
        elif 0.34 < ad_stat < 0.6:
            p_value = np.exp(0.9177 - 4.279 * ad_stat - 1.38 * ad_stat**2)
        elif 0.2 < ad_stat <= 0.34:
            p_value = 1 - np.exp(-8.318 + 42.796 * ad_stat - 59.938 * ad_stat**2)
        else:
            p_value = 1 - np.exp(-13.436 + 101.14 * ad_stat - 223.73 * ad_stat**2)
        
        return A2_corrected, p_value
        
    except Exception as e:
        logger.error(f"Error calculating Anderson-Darling: {e}")
        return 0.0, 0.0


def perform_capability_study(
    client: str,
    ref_project: str,
    elements: List[Dict[str, Any]],
    chart_config: Dict[str, Any] = None,
    batch_number: str = None
) -> Dict[str, Any]:
    """
    Perform capability study with Anderson-Darling calculation
    """
    try:
        logger.info("=" * 80)
        logger.info(f"CAPABILITY STUDY STARTING")
        logger.info(f"Client: {client}, Project: {ref_project}, Batch: {batch_number}")
        logger.info(f"Processing {len(elements)} elements")
        logger.info("=" * 80)
        
        if not elements:
            return {"success": False, "error": "No elements provided"}
        
        # Setup paths
        base_path = Path("./data/spc")
        base_path.mkdir(parents=True, exist_ok=True)
        
        folder_name = f"{client}_{ref_project}_{batch_number}"
        study_folder = base_path / folder_name
        study_folder.mkdir(exist_ok=True)
        
        logger.info(f"Study folder: {study_folder}")
        
        # Process elements
        processed_elements = []
        element_results = {}
        extrapolation_results = []
        
        for idx, element in enumerate(elements):
            try:
                element_id = element['element_id']
                cavity = element.get('cavity', '')
                instrument = element.get('instrument', '3D Scanner')
                sigma = element.get('sigma', '6σ')
                element_class = element.get('class', 'CC')
                
                # Get values
                all_values = element['values']
                original_values = element.get('original_values', all_values)
                has_extrapolation = element.get('has_extrapolation', False)
                extrapolated_values = element.get('extrapolated_values', [])
                
                logger.info(f"\n{'='*60}")
                logger.info(f"PROCESSING ELEMENT {idx+1}/{len(elements)}: {element_id}")
                logger.info(f"  All values count: {len(all_values)}")
                logger.info(f"  Original values: {len(original_values)}")
                logger.info(f"  Has extrapolation: {has_extrapolation}")
                logger.info(f"  Extrapolated count: {len(extrapolated_values)}")
                logger.info(f"  Class: {element_class}, Instrument: {instrument}, Sigma: {sigma}")
                
                # CRITICAL: Calculate Anderson-Darling for ORIGINAL sample
                ad_statistic, p_value = calculate_anderson_darling(original_values)
                logger.info(f"  Anderson-Darling: A²={ad_statistic:.4f}, p={p_value:.4f}")
                
                # Get metrics (custom or calculate from ALL values)
                custom_metrics = element.get('metrics')
                
                if custom_metrics:
                    mean = custom_metrics.get('average')
                    sigma_short = custom_metrics.get('sigma_short')
                    sigma_long = custom_metrics.get('sigma_long')
                    logger.info(f"  Using CUSTOM metrics")
                else:
                    # Calculate from ALL values
                    mean = sum(all_values) / len(all_values)
                    if len(all_values) > 1:
                        variance = sum((x - mean) ** 2 for x in all_values) / (len(all_values) - 1)
                        sigma_long = variance ** 0.5
                        moving_ranges = [abs(all_values[i] - all_values[i-1]) for i in range(1, len(all_values))]
                        mr_bar = sum(moving_ranges) / len(moving_ranges) if moving_ranges else 0
                        sigma_short = mr_bar / 1.128
                    else:
                        sigma_long = sigma_short = 0
                    logger.info(f"  Calculated metrics from ALL values")
                
                # Calculate capability
                nominal = element['nominal']
                tol_minus = abs(element['tol_minus'])
                tol_plus = abs(element['tol_plus'])
                USL = nominal + tol_plus
                LSL = nominal - tol_minus
                tolerance = USL - LSL
                
                if sigma_short > 0:
                    cp = tolerance / (6 * sigma_short)
                    cpu = (USL - mean) / (3 * sigma_short)
                    cpl = (mean - LSL) / (3 * sigma_short)
                    cpk = min(cpu, cpl)
                    
                    from scipy import stats as scipy_stats
                    z_usl = (USL - mean) / sigma_short
                    z_lsl = (mean - LSL) / sigma_short
                    ppm_short = (scipy_stats.norm.cdf(-z_lsl) + (1 - scipy_stats.norm.cdf(z_usl))) * 1e6
                else:
                    cp = cpk = ppm_short = 0

                if sigma_long > 0:
                    pp = tolerance / (6 * sigma_long)
                    ppu = (USL - mean) / (3 * sigma_long)
                    ppl = (mean - LSL) / (3 * sigma_long)
                    ppk = min(ppu, ppl)
                    
                    z_usl_long = (USL - mean) / sigma_long
                    z_lsl_long = (mean - LSL) / sigma_long
                    ppm_long = (scipy_stats.norm.cdf(-z_lsl_long) + (1 - scipy_stats.norm.cdf(z_usl_long))) * 1e6
                else:
                    pp = ppk = ppm_long = 0

                logger.info(f"  Capability: Cp={cp:.3f}, Cpk={cpk:.3f}, Pp={pp:.3f}, Ppk={ppk:.3f}")
                logger.info(f"  PPM: Short={ppm_short:.0f}, Long={ppm_long:.0f}")
                
                # Build result with ALL data including AD and p-value
                element_result = {
                    "element_name": element_id,
                    "cavity": cavity,
                    "instrument": instrument,
                    "class": element_class,
                    "sigma": sigma,
                    "nominal": nominal,
                    "tolerance": [element['tol_minus'], element['tol_plus']],
                    "original_values": all_values,  # ALL values for charts
                    "statistics": {
                        "mean": mean,
                        "std_short": sigma_short,
                        "std_long": sigma_long,
                        "sample_size": len(all_values),
                        "ad_value": ad_statistic,  # ADDED
                        "p_value": p_value          # ADDED
                    },
                    "capability": {
                        "cp": cp,
                        "cpk": cpk,
                        "pp": pp,
                        "ppk": ppk,
                        "ppm_short": ppm_short,
                        "ppm_long": ppm_long
                    }
                }
                
                # Store extrapolation info
                if has_extrapolation and len(extrapolated_values) > 0:
                    extrap_result = {
                        "element_name": element_id,
                        "cavity": cavity,
                        "extrapolated_values": extrapolated_values,
                        "was_extrapolated": True
                    }
                    extrapolation_results.append(extrap_result)
                
                element_key = f"{element_id} Cavity {cavity}" if cavity else element_id
                processed_elements.append(element_result)
                element_results[element_key] = element_result
                
            except Exception as e:
                logger.error(f"Error processing element {element.get('element_id', 'unknown')}: {e}", exc_info=True)
                continue
        
        if not processed_elements:
            return {"success": False, "error": "No elements were processed successfully"}
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SAVING STUDY RESULTS")
        logger.info(f"{'='*80}")
        
        # Save complete report
        complete_report = {
            "client": client,
            "ref_project": ref_project,
            "batch_number": batch_number,
            "timestamp": datetime.now().isoformat(),
            "study_id": f"{ref_project}_{batch_number}",
            "detailed_results": processed_elements,
            "extrapolation_results": extrapolation_results
        }
        
        report_filename = f"{ref_project}_{batch_number}_complete_report.json"
        results_file = study_folder / report_filename
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(complete_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Study results saved: {results_file}")
        logger.info(f"   Elements: {len(processed_elements)}")
        logger.info(f"   Extrapolations: {len(extrapolation_results)}")
        
        # Initialize chart service
        logger.info(f"\n{'='*80}")
        logger.info(f"INITIALIZING CHART SERVICE")
        logger.info(f"{'='*80}")
        
        chart_service = SPCChartService(client, ref_project, batch_number)
        
        if not chart_service.initialize_chart_manager():
            error_msg = "Failed to initialize chart manager"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        
        logger.info("✅ Chart manager initialized")

        # Generate charts with configuration
        logger.info(f"\n{'='*80}")
        logger.info(f"GENERATING CHARTS")
        logger.info(f"Chart configuration: {chart_config}")
        logger.info(f"{'='*80}")
        
        chart_results = chart_service.generate_all_charts(
            show=False, save=True, chart_config=chart_config
        )

        successful_charts = sum(sum(elem_results.values()) for elem_results in chart_results.values())
        total_charts = sum(len(elem_results) for elem_results in chart_results.values())
        
        logger.info(f"✅ Charts generated: {successful_charts}/{total_charts}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STUDY COMPLETED SUCCESSFULLY")
        logger.info(f"{'='*80}\n")
        
        return {
            "success": True,
            "study_results": complete_report,
            "chart_service": chart_service,
            "chart_results": chart_results,
            "elements_summary": element_results,
            "statistics": {
                "total_elements": len(processed_elements),
                "charts_generated": successful_charts,
                "charts_total": total_charts,
                "elements_with_extrapolation": len(extrapolation_results)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ FATAL ERROR in capability study: {e}", exc_info=True)
        return {"success": False, "error": str(e)}