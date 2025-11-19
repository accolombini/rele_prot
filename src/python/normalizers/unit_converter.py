"""
Unit Converter
Converte e padroniza unidades de medida
"""

import re
from typing import Dict, Any, Optional, Tuple


class UnitConverter:
    """Conversor e padronizador de unidades"""
    
    # Mapeamento de unidades
    CURRENT_UNITS = {
        'A': 'ampere',
        'In': 'nominal_current',
        'Ien': 'nominal_earth_current',
        'Ib': 'base_current'
    }
    
    VOLTAGE_UNITS = {
        'V': 'volt',
        'kV': 'kilovolt',
        'Vn': 'nominal_voltage'
    }
    
    TIME_UNITS = {
        's': 'second',
        'ms': 'millisecond',
        'min': 'minute',
        'h': 'hour'
    }
    
    @staticmethod
    def parse_ct_ratio(ratio_str: str) -> Dict[str, Any]:
        """
        Parse CT ratio string
        
        Examples:
            "1500:5" -> {primary: 1500, secondary: 5, ratio: 300.0}
            "1500/5" -> {primary: 1500, secondary: 5, ratio: 300.0}
        """
        if not ratio_str:
            return {'primary_a': None, 'secondary_a': None, 'ratio': None}
        
        # Padrão: número:número ou número/número
        match = re.match(r'(\d+\.?\d*)\s*[:/]\s*(\d+\.?\d*)', str(ratio_str))
        if match:
            primary = float(match.group(1))
            secondary = float(match.group(2))
            ratio = primary / secondary if secondary > 0 else None
            
            return {
                'primary_a': primary,
                'secondary_a': secondary,
                'ratio': round(ratio, 2) if ratio else None
            }
        
        return {'primary_a': None, 'secondary_a': None, 'ratio': None}
    
    @staticmethod
    def parse_vt_ratio(ratio_str: str) -> Dict[str, Any]:
        """
        Parse VT ratio string
        
        Examples:
            "13800:120" -> {primary: 13800, secondary: 120, ratio: 115.0}
            "13800V/120V" -> {primary: 13800, secondary: 120, ratio: 115.0}
        """
        if not ratio_str:
            return {'primary_v': None, 'secondary_v': None, 'ratio': None}
        
        # Remove 'V' se existir
        clean_str = str(ratio_str).replace('V', '').strip()
        
        # Padrão: número:número ou número/número
        match = re.match(r'(\d+\.?\d*)\s*[:/]\s*(\d+\.?\d*)', clean_str)
        if match:
            primary = float(match.group(1))
            secondary = float(match.group(2))
            ratio = primary / secondary if secondary > 0 else None
            
            return {
                'primary_v': primary,
                'secondary_v': secondary,
                'ratio': round(ratio, 2) if ratio else None
            }
        
        return {'primary_v': None, 'secondary_v': None, 'ratio': None}
    
    @staticmethod
    def parse_current_value(value_str: str, base_current: float = None) -> Dict[str, Any]:
        """
        Parse current value with unit
        
        Examples:
            "0.63 In" -> {value: 0.63, unit: 'In', absolute: 315.0 (if base=500)}
            "1500 A" -> {value: 1500, unit: 'A', absolute: 1500}
            "2.00 Ien" -> {value: 2.0, unit: 'Ien', absolute: depends on base}
        """
        if not value_str:
            return {'value': None, 'unit': None, 'absolute_a': None}
        
        # Padrão: número + unidade
        match = re.match(r'([\d.]+)\s*([A-Za-z]+)', str(value_str).strip())
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            # Calcular valor absoluto se possível
            absolute = None
            if unit == 'A':
                absolute = value
            elif unit == 'In' and base_current:
                absolute = value * base_current
            elif unit == 'Ien' and base_current:
                absolute = value * base_current
            
            return {
                'value': value,
                'unit': unit,
                'absolute_a': round(absolute, 2) if absolute else None
            }
        
        # Apenas número (assumir Amperes)
        try:
            value = float(str(value_str).strip())
            return {
                'value': value,
                'unit': 'A',
                'absolute_a': value
            }
        except ValueError:
            pass
        
        return {'value': None, 'unit': None, 'absolute_a': None}
    
    @staticmethod
    def parse_voltage_value(value_str: str) -> Dict[str, Any]:
        """
        Parse voltage value with unit
        
        Examples:
            "13800V" -> {value: 13800, unit: 'V', kv: 13.8}
            "13.8 kV" -> {value: 13.8, unit: 'kV', kv: 13.8}
        """
        if not value_str:
            return {'value': None, 'unit': None, 'kv': None}
        
        # Padrão: número + unidade
        match = re.match(r'([\d.]+)\s*([kK]?[Vv])', str(value_str).strip())
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()
            
            # Converter para kV
            if unit == 'V':
                kv = value / 1000.0
            else:  # kV
                kv = value
            
            return {
                'value': value,
                'unit': unit,
                'kv': round(kv, 2)
            }
        
        return {'value': None, 'unit': None, 'kv': None}
    
    @staticmethod
    def parse_time_value(value_str: str) -> Dict[str, Any]:
        """
        Parse time value with unit
        
        Examples:
            "0.5 s" -> {value: 0.5, unit: 's', seconds: 0.5}
            "100 ms" -> {value: 100, unit: 'ms', seconds: 0.1}
        """
        if not value_str:
            return {'value': None, 'unit': None, 'seconds': None}
        
        # Padrão: número + unidade
        match = re.match(r'([\d.]+)\s*([a-zA-Z]+)', str(value_str).strip())
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            # Converter para segundos
            seconds = value
            if unit == 'ms':
                seconds = value / 1000.0
            elif unit == 'min':
                seconds = value * 60.0
            elif unit == 'h':
                seconds = value * 3600.0
            
            return {
                'value': value,
                'unit': unit,
                'seconds': round(seconds, 4)
            }
        
        # Apenas número (assumir segundos)
        try:
            value = float(str(value_str).strip())
            return {
                'value': value,
                'unit': 's',
                'seconds': value
            }
        except ValueError:
            pass
        
        return {'value': None, 'unit': None, 'seconds': None}
    
    @staticmethod
    def normalize_boolean(value: Any) -> Optional[bool]:
        """
        Normaliza valores booleanos
        
        Examples:
            "Yes" -> True
            "No" -> False
            "ON" -> True
            "1" -> True
        """
        if value is None:
            return None
        
        str_value = str(value).strip().upper()
        
        if str_value in ['YES', 'Y', 'TRUE', 'T', 'ON', '1', 'ENABLED', 'ACTIVE']:
            return True
        elif str_value in ['NO', 'N', 'FALSE', 'F', 'OFF', '0', 'DISABLED', 'INACTIVE']:
            return False
        
        return None
    
    @staticmethod
    def parse_frequency(value: Any) -> Optional[float]:
        """
        Parse frequency value
        
        Examples:
            "60Hz" -> 60.0
            "60 Hz" -> 60.0
            "50" -> 50.0
        """
        if not value:
            return None
        
        # Remover "Hz" se existir
        clean_str = str(value).replace('Hz', '').replace('hz', '').strip()
        
        try:
            return float(clean_str)
        except ValueError:
            return None
