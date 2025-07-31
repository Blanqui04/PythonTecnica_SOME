#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Cleaner Utility
Funcions per netejar i convertir valors problemàtics en CSV

Utilitzat per NetworkScanner i ProjectScanner per gestionar:
- Valors null/buits/¿¿¿???
- Problemes de format decimal (coma vs punt)
- Valors fora de rang
- Problemes d'encoding Unicode (caràcters grecs, etc.)
- Preservació de precisió decimal

Autor: Sistema Automàtic
Data: Juliol 2025
"""

import logging
import pandas as pd
import re
from typing import Any, Union, Optional
from decimal import Decimal, InvalidOperation
import unicodedata

logger = logging.getLogger(__name__)

class ValueCleaner:
    """
    Utilitat per netejar i convertir valors problemàtics amb suport Unicode complet
    """
    
    # Patrons de valors invàlids
    INVALID_PATTERNS = ['nan', 'none', '', 'null', '#N/A', '#ERROR', 'error', 'unknown']
    TEMPLATE_PATTERNS = ['¿¿¿???', '¿¿¿', '???']
    
    # Mapatge de caràcters Unicode problemàtics a ASCII
    UNICODE_REPLACEMENTS = {
        'Δ': 'Delta',  # Caràcter grec Delta
        'α': 'alpha',
        'β': 'beta', 
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'λ': 'lambda',
        'μ': 'mu',
        'π': 'pi',
        'σ': 'sigma',
        'φ': 'phi',
        'ω': 'omega',
        'Ω': 'Omega',
        '°': 'deg',  # Símbol de grau
        '±': '+/-',  # Més o menys
        '≤': '<=',   # Menor o igual
        '≥': '>=',   # Major o igual
        '≠': '!=',   # No igual
        '≈': '~',    # Aproximadament igual
        '×': 'x',    # Multiplicació
        '÷': '/',    # Divisió
        '–': '-',    # Guió en dash
        '—': '-',    # Guió em dash
        '"': '"',    # Cometes dobles curvades
        '"': '"',    # Cometes dobles curvades
        ''': "'",    # Cometes simples curvades
        ''': "'",    # Cometes simples curvades
    }
    
    @staticmethod
    def normalize_unicode_text(text: str) -> str:
        """
        Normalitza text Unicode per evitar problemes d'encoding
        
        Args:
            text: Text a normalitzar
            
        Returns:
            str: Text normalitzat sense caràcters problemàtics
        """
        if not text or pd.isna(text):
            return ""
            
        text_str = str(text)
        
        # Aplicar reemplaçaments específics
        for unicode_char, replacement in ValueCleaner.UNICODE_REPLACEMENTS.items():
            text_str = text_str.replace(unicode_char, replacement)
        
        # Normalitzar Unicode (NFD = Normalization Form Decomposed)
        # Això separa caràcters amb accents en lletra base + accent
        text_str = unicodedata.normalize('NFD', text_str)
        
        # Eliminar tots els caràcters que no són ASCII
        # Mantenim només caràcters del rang ASCII estàndard
        text_str = ''.join(char for char in text_str if ord(char) < 128)
        
        return text_str.strip()
    
    @staticmethod
    def clean_element_value(element: Any) -> str:
        """
        Neteja un valor d'element/nom de mesura amb suport Unicode
        
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
            
            if cleaned:
                # Normalitzar Unicode abans de retornar
                return ValueCleaner.normalize_unicode_text(cleaned)
            else:
                return "NULL"
        
        # Normalitzar Unicode
        return ValueCleaner.normalize_unicode_text(element_str)
    
    @staticmethod
    def clean_numeric_value(value: Any, default_value: float = 0.000) -> float:
        """
        Neteja i converteix un valor numèric amb màxima precisió
        
        Args:
            value: Valor a convertir
            default_value: Valor per defecte si no es pot convertir
            
        Returns:
            float: Valor numèric net amb precisió preservada
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
        
        # Normalitzar caràcters Unicode problemàtics abans del processament numèric
        value_str = ValueCleaner.normalize_unicode_text(value_str)
            
        # Intentar convertir valor real amb màxima precisió
        try:
            # Eliminar espais en blanc
            value_str = value_str.replace(' ', '')
            
            # Eliminar caràcters no numèrics excepte punto, coma i signe negatiu
            value_str = re.sub(r'[^\d.,+-]', '', value_str)
            
            if not value_str or value_str in ['+', '-', '.', ',']:
                return default_value
            
            # Gestió de format numèric europeu amb alta precisió
            if ',' in value_str and '.' not in value_str:
                # Format: "123,45678" -> "123.45678"
                value_str = value_str.replace(',', '.')
            elif ',' in value_str and '.' in value_str:
                # Format: "1.234,56789" -> "1234.56789"
                # O format: "1,234.56789" -> "1234.56789"
                if value_str.rfind(',') > value_str.rfind('.'):
                    # Última coma és el separador decimal
                    parts = value_str.rsplit(',', 1)
                    if len(parts) == 2:
                        integer_part = parts[0].replace('.', '').replace(',', '')
                        decimal_part = parts[1]
                        value_str = f"{integer_part}.{decimal_part}"
                else:
                    # Última punt és el separador decimal
                    parts = value_str.rsplit('.', 1)
                    if len(parts) == 2:
                        integer_part = parts[0].replace('.', '').replace(',', '')
                        decimal_part = parts[1]
                        value_str = f"{integer_part}.{decimal_part}"
            
            # Utilitzar Decimal per preservar precisió màxima
            try:
                decimal_value = Decimal(value_str)
                numeric_value = float(decimal_value)
            except InvalidOperation:
                # Si Decimal falla, intentar conversió directa
                numeric_value = float(value_str)
            
            # Verificar que el valor és raonable (no infinit o NaN)
            if not (float('-inf') < numeric_value < float('inf')) or pd.isna(numeric_value):
                logger.debug(f"Valor fora de rang: {value_str}")
                return default_value
                
            return numeric_value
            
        except (ValueError, OverflowError, TypeError, InvalidOperation) as e:
            # Si no es pot convertir, usar valor per defecte
            logger.debug(f"Valor '{value_str}' no convertible: {e}, usant {default_value}")
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
