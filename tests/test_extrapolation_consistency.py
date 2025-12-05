#!/usr/bin/env python3
"""
Test de Consistència d'Extrapolació
Verifica que els càlculs són consistents quan s'utilitza extrapolació
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from scipy import stats

def test_extrapolation_consistency():
    """Test que verifica la consistència de càlculs amb extrapolació"""
    
    print('='*60)
    print('TEST: Verificació de càlculs amb extrapolació')
    print('='*60)
    
    # Configuració
    np.random.seed(123)
    nominal = 25.5
    tol_minus = 0.3
    tol_plus = 0.3
    USL = nominal + tol_plus
    LSL = nominal - tol_minus
    tolerance = USL - LSL
    
    # 1. Valors originals (5 valors)
    original_values = np.random.normal(nominal, 0.08, 5).tolist()
    
    print(f'\n1. VALORS ORIGINALS (n=5)')
    print(f'   Valors: {[f"{v:.4f}" for v in original_values]}')
    mean_orig = np.mean(original_values)
    std_orig = np.std(original_values, ddof=1)
    print(f'   Mitjana: {mean_orig:.4f}')
    print(f'   Sigma: {std_orig:.4f}')
    
    # Calcular Cpk amb 5 valors
    if std_orig > 0:
        cpk_orig = min((USL - mean_orig), (mean_orig - LSL)) / (3 * std_orig)
        ppk_orig = cpk_orig
    else:
        cpk_orig = ppk_orig = 0
    print(f'   Cpk: {cpk_orig:.3f}')
    print(f'   Ppk: {ppk_orig:.3f}')
    
    # 2. Extrapolar a 100 valors
    print(f'\n2. EXTRAPOLACIÓ A 100 VALORS')
    n_extra = 95
    extrapolated = np.random.normal(mean_orig, std_orig, n_extra)
    all_values = np.concatenate([original_values, extrapolated])
    
    mean_all = np.mean(all_values)
    std_all = np.std(all_values, ddof=1)
    
    # Moving range per sigma short
    mr = [abs(all_values[i] - all_values[i-1]) for i in range(1, len(all_values))]
    mr_bar = np.mean(mr)
    sigma_short = mr_bar / 1.128
    
    print(f'   Mitjana (100 valors): {mean_all:.4f}')
    print(f'   Sigma long: {std_all:.4f}')
    print(f'   Sigma short (MR): {sigma_short:.4f}')
    
    # Calcular capacitat
    if sigma_short > 0:
        cp = tolerance / (6 * sigma_short)
        cpk = min((USL - mean_all) / (3 * sigma_short), (mean_all - LSL) / (3 * sigma_short))
    else:
        cp = cpk = 0
        
    if std_all > 0:
        pp = tolerance / (6 * std_all)
        ppk = min((USL - mean_all) / (3 * std_all), (mean_all - LSL) / (3 * std_all))
    else:
        pp = ppk = 0
    
    print(f'   Cp: {cp:.3f}')
    print(f'   Cpk: {cpk:.3f}')
    print(f'   Pp: {pp:.3f}')
    print(f'   Ppk: {ppk:.3f}')
    
    # 3. Simular mètriques custom (problema de l'usuari)
    print(f'\n3. SIMULACIÓ: USUARI EDITA MÈTRIQUES')
    custom_mean = mean_orig  # Usa la mitjana original
    custom_sigma = std_orig  # Usa la sigma original
    print(f'   Mètriques editades:')
    print(f'   - Mitjana custom: {custom_mean:.4f}')
    print(f'   - Sigma custom: {custom_sigma:.4f}')
    
    if custom_sigma > 0:
        cpk_custom = min((USL - custom_mean) / (3 * custom_sigma), 
                        (custom_mean - LSL) / (3 * custom_sigma))
    else:
        cpk_custom = 0
    print(f'   Cpk (amb mètriques custom): {cpk_custom:.3f}')
    
    # 4. Verificar diferència
    print(f'\n4. COMPARACIÓ RESULTATS')
    print(f'   Cpk (5 valors originals):      {cpk_orig:.3f}')
    print(f'   Cpk (100 valors extrapolats):  {cpk:.3f}')
    print(f'   Cpk (mètriques custom):        {cpk_custom:.3f}')
    print()
    
    diff = abs(cpk_orig - cpk)
    print(f'   Diferència Cpk (orig vs extrap): {diff:.3f}')
    
    # Les diferències haurien de ser petites si l'extrapolació és consistent
    # Tolerem fins a 0.5 de diferència perquè l'extrapolació afegeix variabilitat
    assert diff < 0.5, f"Diferència massa gran: {diff:.3f}"
    
    print('\n   ✓ Test passat: diferències dins del rang acceptable')
    print('\n' + '='*60)


def test_metric_calculation_consistency():
    """Verifica que els càlculs de mètriques són consistents"""
    
    print('\n' + '='*60)
    print('TEST: Consistència de càlculs de mètriques')
    print('='*60)
    
    from src.services.capability_calculator_service import CapabilityCalculatorService
    
    np.random.seed(456)
    
    # Cas 1: Valors normals
    values = np.random.normal(10.0, 0.1, 100).tolist()
    nominal = 10.0
    tol_minus = 0.5
    tol_plus = 0.5
    
    calc = CapabilityCalculatorService()
    metrics = calc.calculate_metrics(values, nominal, tol_minus, tol_plus)
    
    # Verificar que tots els camps existeixen
    required_fields = ['mean', 'sigma_short', 'sigma_long', 'cp', 'cpk', 'pp', 'ppk', 'ppm']
    for field in required_fields:
        assert field in metrics, f"Camp {field} no trobat"
        assert metrics[field] is not None, f"Camp {field} és None"
    
    print('\n   ✓ Tots els camps de mètriques calculats correctament')
    
    # Verificar relacions
    assert metrics['cpk'] <= metrics['cp'] + 0.01, "Cpk no pot ser major que Cp"
    assert metrics['ppk'] <= metrics['pp'] + 0.01, "Ppk no pot ser major que Pp"
    
    print('   ✓ Relacions Cpk <= Cp i Ppk <= Pp verificades')
    
    # Verificar valors raonables
    assert 0 < metrics['cp'] < 10, f"Cp fora de rang: {metrics['cp']}"
    assert 0 < metrics['cpk'] < 10, f"Cpk fora de rang: {metrics['cpk']}"
    
    print('   ✓ Valors dins de rangs raonables')
    print('\n' + '='*60)


def test_sigma_calculation():
    """Verifica els càlculs de sigma short i sigma long"""
    
    print('\n' + '='*60)
    print('TEST: Càlculs de Sigma')
    print('='*60)
    
    # Valors amb sigma conegut
    np.random.seed(789)
    true_sigma = 0.1
    values = np.random.normal(10.0, true_sigma, 1000).tolist()
    
    # Calcular sigma long (desviació estàndard mostral)
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    sigma_long = variance ** 0.5
    
    # Calcular sigma short (moving range / 1.128)
    mr = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
    mr_bar = sum(mr) / len(mr)
    sigma_short = mr_bar / 1.128
    
    print(f'\n   Sigma real: {true_sigma:.4f}')
    print(f'   Sigma long calculat: {sigma_long:.4f}')
    print(f'   Sigma short calculat: {sigma_short:.4f}')
    
    # Amb 1000 valors, els sigmes haurien d'estar prop del real
    assert abs(sigma_long - true_sigma) < 0.02, f"Sigma long massa diferent: {sigma_long}"
    assert abs(sigma_short - true_sigma) < 0.02, f"Sigma short massa diferent: {sigma_short}"
    
    print('\n   ✓ Sigmes calculats correctament (diferència < 0.02)')
    print('='*60)


if __name__ == "__main__":
    test_extrapolation_consistency()
    test_metric_calculation_consistency()
    test_sigma_calculation()
    print("\n✅ TOTS ELS TESTS PASSATS")
