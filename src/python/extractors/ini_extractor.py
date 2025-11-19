"""
INI Extractor for SEPAM Relay Files (.S40)
Extracts structured data from INI-formatted SEPAM configuration files
"""

import configparser
from pathlib import Path
from typing import Dict, Any, List, Optional


class IniExtractor:
    """Extracts structured data from SEPAM .S40 configuration files"""
    
    def __init__(self):
        self.manufacturer = 'SCHNEIDER ELECTRIC'
        self.model_series = 'SEPAM'
    
    def extract_all(self, ini_path: str) -> Dict[str, Any]:
        """Extract all relevant data from SEPAM INI file"""
        config = configparser.ConfigParser()
        # Try UTF-8 first, fallback to Latin-1 for legacy SEPAM files
        try:
            config.read(ini_path, encoding='utf-8')
        except UnicodeDecodeError:
            config.read(ini_path, encoding='latin-1')
        
        return {
            'manufacturer': self.manufacturer,
            'model_info': self._extract_model_info(config),
            'ct_vt_data': self._extract_ct_vt_data(config),
            'protection_functions': self._extract_protection_functions(config),
            'raw_sections': {section: dict(config[section]) for section in config.sections()}
        }
    
    def _extract_model_info(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """Extract model and configuration information"""
        model_info = {
            'model_number': None,
            'plant_reference': None,
            'software_version': None,
            'frequency': 60.0,  # Default for Brazil
            'model_type': 'SEPAM S40',
            'serial_number': None,
            'application': None
        }
        
        if 'Sepam_Caracteristiques' in config:
            carac = config['Sepam_Caracteristiques']
            
            # Application type
            if 'application' in carac:
                model_info['application'] = carac['application']
                model_info['model_type'] = f"SEPAM {carac['application']}"
            
            # Frequency
            if 'frequence_reseau' in carac:
                freq_code = carac['frequence_reseau']
                model_info['frequency'] = 60.0 if freq_code == '1' else 50.0
        
        if 'Sepam_ConfigMaterielle' in config:
            config_mat = config['Sepam_ConfigMaterielle']
            
            # Repere contains: substation-bay serial_number
            # Example: "00-MF-12 NS08170043"
            if 'repere' in config_mat:
                repere = config_mat['repere'].strip()
                model_info['plant_reference'] = repere
                
                # Extract serial number (part after space)
                parts = repere.split()
                if len(parts) > 1:
                    model_info['serial_number'] = parts[-1]
            
            # Model code
            if 'modele' in config_mat:
                model_info['model_number'] = config_mat['modele']
        
        return model_info
    
    def _extract_ct_vt_data(self, config: configparser.ConfigParser) -> Dict[str, List[Dict[str, Any]]]:
        """Extract CT and VT data"""
        ct_vt_data = {
            'current_transformers': [],
            'voltage_transformers': []
        }
        
        if 'Sepam_Caracteristiques' in config:
            carac = config['Sepam_Caracteristiques']
            
            # Current Transformers
            if 'i_nominal' in carac:
                primary_a = float(carac['i_nominal'])
                
                # SEPAM uses 1A or 5A secondary (typically 1A for European models)
                secondary_a = 1.0  # Default
                if 'calibre_TC' in carac:
                    # calibre_TC: 0=1A, 1=5A
                    secondary_a = 5.0 if carac['calibre_TC'] == '1' else 1.0
                
                ct_vt_data['current_transformers'].append({
                    'tc_type': 'Phase',
                    'primary_rating_a': primary_a,
                    'secondary_rating_a': secondary_a,
                    'ratio': f"{int(primary_a)}:{int(secondary_a)}"
                })
            
            # Residual current (ground)
            if 'courant_nominal_residuel' in carac:
                residual_a = float(carac['courant_nominal_residuel'])
                secondary_a = 1.0
                
                ct_vt_data['current_transformers'].append({
                    'tc_type': 'Residual',
                    'primary_rating_a': residual_a,
                    'secondary_rating_a': secondary_a,
                    'ratio': f"{int(residual_a)}:{int(secondary_a)}"
                })
            
            # Voltage Transformers
            if 'tension_primaire_nominale' in carac:
                primary_v = float(carac['tension_primaire_nominale'])
                
                # tension_secondaire_nominale is coded:
                # 0=115V, 1=100V, 2=110V, etc.
                secondary_v = 115.0  # Default
                if 'tension_secondaire_nominale' in carac:
                    sec_code = carac['tension_secondaire_nominale']
                    secondary_map = {
                        '0': 115.0,
                        '1': 100.0,
                        '2': 110.0,
                        '3': 120.0
                    }
                    secondary_v = secondary_map.get(sec_code, 115.0)
                
                ct_vt_data['voltage_transformers'].append({
                    'vt_type': 'Main',
                    'primary_rating_v': primary_v,
                    'secondary_rating_v': secondary_v,
                    'ratio': f"{int(primary_v)}:{int(secondary_v)}"
                })
        
        return ct_vt_data
    
    def _extract_protection_functions(self, config: configparser.ConfigParser) -> List[Dict[str, Any]]:
        """Extract protection functions from all Protection sections"""
        functions = []
        
        # ANSI code mapping for SEPAM sections
        ansi_map = {
            'Protection50_51': '50/51',
            'Protection50_51N': '50N/51N',
            'Protection46': '46',
            'Protection47': '47',
            'Protection49': '49',
            'Protection50BF': '50BF',
            'Protection59': '59',
            'Protection59N': '59N',
            'Protection2727S': '27',
            'Protection81': '81',
            'Protection32': '32',
            'Protection67': '67',
            'Protection67N': '67N'
        }
        
        for section in config.sections():
            if section.startswith('Protection'):
                ansi_code = ansi_map.get(section, section.replace('Protection', ''))
                section_data = dict(config[section])
                
                # SEPAM uses "activite_X" fields where X is threshold number
                # activite_X = 1 means enabled, 0 means disabled
                active_thresholds = []
                
                for key, value in section_data.items():
                    if key.startswith('activite_') and value == '1':
                        threshold = key.replace('activite_', '')
                        active_thresholds.append(threshold)
                
                # If any threshold is active, the function is enabled
                is_enabled = len(active_thresholds) > 0
                
                # Extract setpoints for active thresholds
                setpoints = {}
                for threshold in active_thresholds:
                    # Look for setpoint parameters
                    for param_key in section_data:
                        if threshold in param_key and not param_key.startswith('activite'):
                            setpoints[param_key] = section_data[param_key]
                
                functions.append({
                    'section': section,
                    'ansi_code': ansi_code,
                    'is_enabled': is_enabled,
                    'active_thresholds': active_thresholds,
                    'setpoints': setpoints,
                    'all_parameters': section_data
                })
        
        return functions
    
    def get_voltage_level_kv(self, ini_path: str) -> Optional[float]:
        """Get voltage level from .S40 file"""
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')
        
        if 'Sepam_Caracteristiques' in config:
            carac = config['Sepam_Caracteristiques']
            if 'tension_primaire_nominale' in carac:
                voltage_v = float(carac['tension_primaire_nominale'])
                return voltage_v / 1000.0  # Convert to kV
        
        return None
    
    def get_barras_identifier(self, ini_path: str) -> Optional[str]:
        """Extract barras identifier from repere field"""
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')
        
        if 'Sepam_ConfigMaterielle' in config:
            config_mat = config['Sepam_ConfigMaterielle']
            if 'repere' in config_mat:
                repere = config_mat['repere'].strip()
                # Extract first part before space: "00-MF-12 NS08170043" -> "00-MF-12"
                return repere.split()[0] if repere else None
        
        return None
