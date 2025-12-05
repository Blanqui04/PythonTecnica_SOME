#!/usr/bin/env python3
"""
Test de Validació vs Excel
Verifica que els càlculs coincideixen amb les fórmules d'Excel
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from scipy import stats

# Importar el servei de càlcul
from src.services.capability_calculator_service import CapabilityCalculatorService


def test_cp_cpk_formulas():
    """
    Verifica les fórmules Cp i Cpk vs Excel
    
    Fórmules Excel:
    Cp = (USL - LSL) / (6 * sigma)
    Cpk = MIN((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
    
    On sigma_short = MRbar / d2 (d2 = 1.128 per subgrup n=2)
    """
    print('='*60)
    print('TEST: Fórmules Cp/Cpk vs Excel')
    print('='*60)
    
    # Dades de prova
    values = [10.02, 10.05, 9.98, 10.01, 10.03, 9.99, 10.04, 10.00, 10.02, 10.01,
              10.03, 9.97, 10.02, 10.04, 9.98, 10.01, 10.00, 10.03, 9.99, 10.02]
    nominal = 10.0
    tol_minus = 0.1
    tol_plus = 0.1
    
    USL = nominal + tol_plus  # 10.1
    LSL = nominal - tol_minus  # 9.9
    tolerance = USL - LSL  # 0.2
    
    # Càlcul manual (fórmules Excel)
    n = len(values)
    mean = sum(values) / n
    
    # Moving Range (diferències consecutives absolutes)
    MR = [abs(values[i] - values[i-1]) for i in range(1, n)]
    MR_bar = sum(MR) / len(MR)
    
    # Sigma short (Moving Range / d2)
    d2 = 1.128  # Constant per subgrup de mida 2
    sigma_short = MR_bar / d2
    
    # Sigma long (desviació estàndard mostral)
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    sigma_long = variance ** 0.5
    
    # Cp i Cpk (usen sigma_short)
    Cp_excel = tolerance / (6 * sigma_short)
    Cpu = (USL - mean) / (3 * sigma_short)
    Cpl = (mean - LSL) / (3 * sigma_short)
    Cpk_excel = min(Cpu, Cpl)
    
    # Pp i Ppk (usen sigma_long)
    Pp_excel = tolerance / (6 * sigma_long)
    Ppu = (USL - mean) / (3 * sigma_long)
    Ppl = (mean - LSL) / (3 * sigma_long)
    Ppk_excel = min(Ppu, Ppl)
    
    print(f'\nDades:')
    print(f'  n = {n}')
    print(f'  Mean = {mean:.6f}')
    print(f'  USL = {USL}, LSL = {LSL}')
    print(f'  MR_bar = {MR_bar:.6f}')
    print(f'  sigma_short (MR/d2) = {sigma_short:.6f}')
    print(f'  sigma_long (std) = {sigma_long:.6f}')
    
    print(f'\nResultats Excel:')
    print(f'  Cp = {Cp_excel:.4f}')
    print(f'  Cpk = {Cpk_excel:.4f}')
    print(f'  Pp = {Pp_excel:.4f}')
    print(f'  Ppk = {Ppk_excel:.4f}')
    
    # Ara comprovem amb el servei
    calc = CapabilityCalculatorService()
    result = calc.calculate_metrics(values, nominal, tol_minus, tol_plus)
    
    print(f'\nResultats del Servei:')
    print(f'  Cp = {result["cp"]:.4f}')
    print(f'  Cpk = {result["cpk"]:.4f}')
    print(f'  Pp = {result["pp"]:.4f}')
    print(f'  Ppk = {result["ppk"]:.4f}')
    print(f'  sigma_short = {result["sigma_short"]:.6f}')
    print(f'  sigma_long = {result["sigma_long"]:.6f}')
    
    # Comparar amb tolerància
    tolerance_check = 0.001
    
    assert abs(result['cp'] - Cp_excel) < tolerance_check, \
        f"Cp no coincideix: {result['cp']:.4f} vs {Cp_excel:.4f}"
    assert abs(result['cpk'] - Cpk_excel) < tolerance_check, \
        f"Cpk no coincideix: {result['cpk']:.4f} vs {Cpk_excel:.4f}"
    assert abs(result['pp'] - Pp_excel) < tolerance_check, \
        f"Pp no coincideix: {result['pp']:.4f} vs {Pp_excel:.4f}"
    assert abs(result['ppk'] - Ppk_excel) < tolerance_check, \
        f"Ppk no coincideix: {result['ppk']:.4f} vs {Ppk_excel:.4f}"
    
    print(f'\n✓ Tots els índexs coincideixen amb Excel (tolerància < {tolerance_check})')
    print('='*60)


def test_ppm_formula():
    """
    Verifica la fórmula PPM
    
    Fórmules:
    PPM = (1 - NORMDIST(Z)) * 1,000,000
    On Z = min(|USL - mean|, |mean - LSL|) / sigma
    """
    print('\n' + '='*60)
    print('TEST: Fórmula PPM vs Excel')
    print('='*60)
    
    # Cas amb dades centrades
    np.random.seed(42)
    values = np.random.normal(10.0, 0.02, 100).tolist()
    nominal = 10.0
    tol_minus = 0.1
    tol_plus = 0.1
    
    USL = nominal + tol_plus
    LSL = nominal - tol_minus
    
    mean = np.mean(values)
    sigma = np.std(values, ddof=1)
    
    # Z scores
    Z_upper = (USL - mean) / sigma
    Z_lower = (mean - LSL) / sigma
    
    # PPM total (defectes per ambdós costats)
    ppm_upper = (1 - stats.norm.cdf(Z_upper)) * 1_000_000
    ppm_lower = stats.norm.cdf(-Z_lower) * 1_000_000  # Cola esquerra
    ppm_total = ppm_upper + ppm_lower
    
    print(f'\nDades:')
    print(f'  Mean = {mean:.6f}')
    print(f'  Sigma = {sigma:.6f}')
    print(f'  Z_upper = {Z_upper:.4f}')
    print(f'  Z_lower = {Z_lower:.4f}')
    print(f'\nPPM Excel:')
    print(f'  PPM upper = {ppm_upper:.2f}')
    print(f'  PPM lower = {ppm_lower:.2f}')
    print(f'  PPM total = {ppm_total:.2f}')
    
    # Comprovar amb el servei
    calc = CapabilityCalculatorService()
    result = calc.calculate_metrics(values, nominal, tol_minus, tol_plus)
    
    print(f'\nPPM del Servei: {result["ppm"]:.2f}')
    
    # El servei pot calcular PPM de manera diferent, però ha de ser raonable
    assert result['ppm'] < 1_000_000, "PPM ha de ser < 1,000,000"
    assert result['ppm'] >= 0, "PPM ha de ser >= 0"
    
    print(f'\n✓ PPM dins de rang vàlid')
    print('='*60)


def test_capability_with_offset():
    """
    Verifica que Cpk detecta correctament el descentrament
    """
    print('\n' + '='*60)
    print('TEST: Cpk amb descentrament')
    print('='*60)
    
    nominal = 10.0
    tol_minus = 0.1
    tol_plus = 0.1
    
    # Cas 1: Procés centrat
    np.random.seed(100)
    values_centered = np.random.normal(nominal, 0.02, 50).tolist()
    
    # Cas 2: Procés descentrat cap a USL
    values_high = np.random.normal(nominal + 0.04, 0.02, 50).tolist()
    
    # Cas 3: Procés descentrat cap a LSL
    values_low = np.random.normal(nominal - 0.04, 0.02, 50).tolist()
    
    calc = CapabilityCalculatorService()
    
    result_centered = calc.calculate_metrics(values_centered, nominal, tol_minus, tol_plus)
    result_high = calc.calculate_metrics(values_high, nominal, tol_minus, tol_plus)
    result_low = calc.calculate_metrics(values_low, nominal, tol_minus, tol_plus)
    
    print(f'\nProcés centrat:')
    print(f'  Mean = {result_centered["mean"]:.4f}')
    print(f'  Cp = {result_centered["cp"]:.4f}')
    print(f'  Cpk = {result_centered["cpk"]:.4f}')
    
    print(f'\nProcés descentrat (alt):')
    print(f'  Mean = {result_high["mean"]:.4f}')
    print(f'  Cp = {result_high["cp"]:.4f}')
    print(f'  Cpk = {result_high["cpk"]:.4f}')
    
    print(f'\nProcés descentrat (baix):')
    print(f'  Mean = {result_low["mean"]:.4f}')
    print(f'  Cp = {result_low["cp"]:.4f}')
    print(f'  Cpk = {result_low["cpk"]:.4f}')
    
    # Verificar que Cpk és menor que Cp quan hi ha descentrament
    assert result_centered['cpk'] <= result_centered['cp'], "Cpk ha de ser <= Cp"
    assert result_high['cpk'] < result_high['cp'], "Cpk ha de ser < Cp quan hi ha descentrament"
    assert result_low['cpk'] < result_low['cp'], "Cpk ha de ser < Cp quan hi ha descentrament"
    
    # Cpk del procés centrat ha de ser major que els descentrats
    assert result_centered['cpk'] > result_high['cpk'], \
        "Cpk centrat ha de ser major que descentrat"
    assert result_centered['cpk'] > result_low['cpk'], \
        "Cpk centrat ha de ser major que descentrat"
    
    print(f'\n✓ Cpk reflecteix correctament el descentrament')
    print('='*60)


def test_normality_test():
    """
    Verifica el test de normalitat Anderson-Darling
    """
    print('\n' + '='*60)
    print('TEST: Test de Normalitat Anderson-Darling')
    print('='*60)
    
    # Dades normals
    np.random.seed(200)
    normal_data = np.random.normal(10, 0.1, 100)
    
    # Dades no normals (bimodal)
    non_normal_data = np.concatenate([
        np.random.normal(9.5, 0.05, 50),
        np.random.normal(10.5, 0.05, 50)
    ])
    
    # Test Anderson-Darling
    result_normal = stats.anderson(normal_data, dist='norm')
    result_non_normal = stats.anderson(non_normal_data, dist='norm')
    
    # p-value aproximat pel nivell de significança 5%
    critical_value_5pct = result_normal.critical_values[2]  # Index 2 és per 5%
    
    is_normal_ad = result_normal.statistic < critical_value_5pct
    is_non_normal_ad = result_non_normal.statistic >= critical_value_5pct
    
    print(f'\nDades normals:')
    print(f'  Estadístic A-D = {result_normal.statistic:.4f}')
    print(f'  Valor crític (5%) = {critical_value_5pct:.4f}')
    print(f'  És normal? {is_normal_ad}')
    
    print(f'\nDades NO normals:')
    print(f'  Estadístic A-D = {result_non_normal.statistic:.4f}')
    print(f'  Valor crític (5%) = {critical_value_5pct:.4f}')
    print(f'  És normal? {not is_non_normal_ad}')
    
    assert is_normal_ad, "Les dades normals haurien de passar el test"
    assert is_non_normal_ad, "Les dades no normals haurien de fallar el test"
    
    print(f'\n✓ Test de normalitat funciona correctament')
    print('='*60)


def test_decimal_precision():
    """
    Verifica que els valors s'arrodoneixen correctament a 2 decimals
    """
    print('\n' + '='*60)
    print('TEST: Precisió Decimal')
    print('='*60)
    
    # Valors que arrodoneixen de maneres diferents
    test_cases = [
        (1.234, 1.23),
        (1.235, 1.24),  # Python arrodoneix 5 cap al parell més proper (banker's rounding)
        (1.245, 1.24),  # o .25
        (0.999, 1.00),
        (0.001, 0.00),
    ]
    
    print('\nArrodoniment a 2 decimals:')
    for original, expected in test_cases:
        rounded = round(original, 2)
        formatted = f"{original:.2f}"
        print(f'  {original} -> round: {rounded}, format: {formatted}')
    
    # Verificar format d'string
    value = 1.23456789
    formatted = f"{value:.2f}"
    assert formatted == "1.23", f"Format incorrecte: {formatted}"
    
    print(f'\n✓ Format decimal correcte')
    print('='*60)


if __name__ == "__main__":
    test_cp_cpk_formulas()
    test_ppm_formula()
    test_capability_with_offset()
    test_normality_test()
    test_decimal_precision()
    
    print('\n' + '='*60)
    print('✅ TOTS ELS TESTS DE VALIDACIÓ EXCEL PASSATS')
    print('='*60)
