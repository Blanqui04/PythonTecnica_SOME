#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Cleaner Utility
Funcions per netejar i convertir valors problemàtics en CSV

Utilitzat per NetworkScanner i ProjectScanner per gestionar:
- Valors null/buits/¿¿¿???
- Problemes de format decimal (coma vs punt)
- Valors fora de rang

Autor: Sistema Automàtic
Data: Juliol 2025
"""

import logging
import pandas as pd
from typing import Any, Union, Optional

logger = logging.getLogger(__name__)

class ValueCleaner:
    """
    Utilitat per netejar i convertir valors problemàtics
    """
    
    # Patrons de valors invàlids
    INVALID_PATTERNS = ['nan', 'none', '', 'null', '#N/A', '#ERROR', 'error', 'unknown']
    TEMPLATE_PATTERNS = ['¿¿¿???', '¿¿¿', '???']
    
    @staticmethod
    def clean_element_value(element: Any) -> str:
        """
        Neteja un valor d'element/nom de mesura
        
        Args:
            element: Valor d'element a netejar
            
        Returns:
            str: Element net o "NULL" si és invàlid
        """
        if not element or pd.isna(element):
            return "NULL"
            
        element_str = str(element).strip()
        
        # Verificar si és invàlid
        if element_str.lower() in ValueCleaner.INVALID_PATTERNS:
            return "NULL"
            
        # Verificar si té patrons de plantilla
        if any(pattern in element_str for pattern in ValueCleaner.TEMPLATE_PATTERNS):
            # Netejar patrons problemàtics però mantenir el nom si queda alguna cosa
            cleaned = element_str
            for pattern in ValueCleaner.TEMPLATE_PATTERNS:
                cleaned = cleaned.replace(pattern, '')
            cleaned = cleaned.strip()
            
            return cleaned if cleaned else "NULL"
            
        return element_str
    
    @staticmethod
    def clean_numeric_value(value: Any, default_value: float = 0.000) -> float:
        """
        Neteja i converteix un valor numèric
        
        Args:
            value: Valor a convertir
            default_value: Valor per defecte si no es pot convertir
            
        Returns:
            float: Valor numèric net
        """
        if not value or pd.isna(value):
            return default_value
            
        value_str = str(value).strip()
        
        # Verificar si és invàlid
        if value_str.lower() in ValueCleaner.INVALID_PATTERNS:
            return default_value
            
        # Verificar si té patrons de plantilla
        if any(pattern in value_str for pattern in ValueCleaner.TEMPLATE_PATTERNS):
            return default_value
            
        # Intentar convertir valor real
        try:
            # Eliminar espais en blanc
            value_str = value_str.replace(' ', '')
            
            # Gestió de format numèric europeu
            if ',' in value_str and '.' not in value_str:
                # Format: "123,45" -> "123.45"
                value_str = value_str.replace(',', '.')
            elif ',' in value_str and '.' in value_str:
                # Format: "1.234,56" -> "1234.56"
                parts = value_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 3:  # Decimal part <= 3 digits
                    integer_part = parts[0].replace('.', '')
                    decimal_part = parts[1]
                    value_str = f"{integer_part}.{decimal_part}"
                else:
                    # Si no és format estàndard, intentar només eliminar comes
                    value_str = value_str.replace(',', '')
            
            numeric_value = float(value_str)
            
            # Verificar que el valor és raonable (no infinit o NaN)
            if not (float('-inf') < numeric_value < float('inf')) or pd.isna(numeric_value):
                return default_value
                
            return numeric_value
            
        except (ValueError, OverflowError, TypeError):
            # Si no es pot convertir, usar valor per defecte
            logger.debug(f"Valor '{value_str}' convertit a {default_value}")
            return default_value
    
    @staticmethod
    def clean_dataframe_columns(df: pd.DataFrame, 
                               element_col: str = None, 
                               actual_col: str = None,
                               nominal_col: str = None,
                               tolerance_col: str = None) -> pd.DataFrame:
        """
        Neteja les columnes d'un DataFrame
        
        Args:
            df: DataFrame a netejar
            element_col: Nom de la columna d'element
            actual_col: Nom de la columna de valor actual
            nominal_col: Nom de la columna de valor nominal
            tolerance_col: Nom de la columna de tolerància
            
        Returns:
            pd.DataFrame: DataFrame net
        """
        df_clean = df.copy()
        
        # Netejar columna d'element
        if element_col and element_col in df_clean.columns:
            df_clean[element_col] = df_clean[element_col].apply(ValueCleaner.clean_element_value)
        
        # Netejar columnes numèriques
        numeric_columns = []
        if actual_col and actual_col in df_clean.columns:
            numeric_columns.append(actual_col)
        if nominal_col and nominal_col in df_clean.columns:
            numeric_columns.append(nominal_col)
        if tolerance_col and tolerance_col in df_clean.columns:
            numeric_columns.append(tolerance_col)
            
        for col in numeric_columns:
            df_clean[col] = df_clean[col].apply(ValueCleaner.clean_numeric_value)
        
        return df_clean
    
    @staticmethod
    def detect_problematic_values(df: pd.DataFrame) -> dict:
        """
        Detecta valors problemàtics en un DataFrame
        
        Args:
            df: DataFrame a analitzar
            
        Returns:
            dict: Resum de valors problemàtics trobats
        """
        problems = {
            'template_patterns': 0,
            'invalid_patterns': 0,
            'decimal_issues': 0,
            'total_rows': len(df)
        }
        
        # Comptar patrons problemàtics en totes les columnes de text
        for col in df.select_dtypes(include=['object']).columns:
            for _, value in df[col].items():
                if not value or pd.isna(value):
                    continue
                    
                value_str = str(value)
                
                if any(pattern in value_str for pattern in ValueCleaner.TEMPLATE_PATTERNS):
                    problems['template_patterns'] += 1
                elif value_str.lower() in ValueCleaner.INVALID_PATTERNS:
                    problems['invalid_patterns'] += 1
                elif ',' in value_str or ('.' in value_str and value_str.count('.') > 1):
                    problems['decimal_issues'] += 1
        
        return problems
