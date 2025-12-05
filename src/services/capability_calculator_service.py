# src/services/capability_calculator_service.py
import numpy as np
from typing import Dict, List, Union, Optional
import math
from scipy import stats

__all__ = ['CapabilityCalculatorService']  # Explicitly declare what to export

class CapabilityCalculatorService:
    """Service for real-time capability calculations"""
    
    @staticmethod
    def calculate_metrics(values: List[float],
                         nominal: float,
                         tol_minus: float,
                         tol_plus: float) -> Dict[str, float]:
        """Calculate capability metrics for a set of values"""
        if not values:
            return {}
            
        n = len(values)
        mean = sum(values) / n
        
        # Calculate standard deviations
        if n > 1:
            variance = sum((x - mean) ** 2 for x in values) / (n - 1)
            sigma_long = math.sqrt(variance)
            
            # Calculate sigma short using moving range method
            moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, n)]
            mr_bar = sum(moving_ranges) / len(moving_ranges) if moving_ranges else 0
            sigma_short = mr_bar / 1.128  # d2 constant for n=2
        else:
            sigma_long = sigma_short = 0
            
        # Calculate capability indices
        USL = nominal + tol_plus
        LSL = nominal - tol_minus
        tolerance = USL - LSL
        
        if sigma_short > 0:
            cp = tolerance / (6 * sigma_short)
            cpu = (USL - mean) / (3 * sigma_short)
            cpl = (mean - LSL) / (3 * sigma_short)
            cpk = min(cpu, cpl)
        else:
            cp = cpk = 0
            
        if sigma_long > 0:
            pp = tolerance / (6 * sigma_long)
            ppu = (USL - mean) / (3 * sigma_long)
            ppl = (mean - LSL) / (3 * sigma_long)
            ppk = min(ppu, ppl)
        else:
            pp = ppk = 0
            
        # Calculate PPM (uses sigma_long - overall process variation)
        try:
            if sigma_long > 0:
                z_usl = (USL - mean) / sigma_long
                z_lsl = (mean - LSL) / sigma_long
                # PPM = probability above USL + probability below LSL
                ppm = ((1 - stats.norm.cdf(z_usl)) + stats.norm.cdf(-z_lsl)) * 1e6
            else:
                ppm = 0
        except:
            ppm = 0
            
        return {
            "mean": mean,
            "sigma_short": sigma_short,
            "sigma_long": sigma_long,
            "cp": cp,
            "cpk": cpk,
            "pp": pp,
            "ppk": ppk,
            "ppm": ppm
        }
    
    @staticmethod
    def calculate_normality_metrics(values: List[float]) -> Dict[str, Union[float, bool]]:
        """Calculate normality test metrics"""
        try:
            if len(values) >= 3:
                statistic, p_value = stats.normaltest(values)
                return {
                    "is_normal": p_value > 0.05,
                    "p_value": p_value,
                    "statistic": statistic
                }
        except ImportError:
            pass
            
        return {
            "is_normal": True,
            "p_value": 1.0,
            "statistic": 0.0
        }
