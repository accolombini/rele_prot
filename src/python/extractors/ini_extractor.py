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
            'application': None,
            'substation_code': None  # NOVO
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
            
            # Substation Code (SUBSTATION_CODE)
            if 'SUBSTATION_CODE' in carac:
                model_info['substation_code'] = carac['SUBSTATION_CODE']
        
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
                
                # Mapeamento SEPAM VT secundário (SFT2841 documentation)
                # 1=110V, 2=115V, 3=120V, 4=200V, 5=230V, 6=user-defined
                secondary_v = 115.0  # Default
                vt_enabled = True  # Default
                
                if 'tension_secondaire_nominale' in carac:
                    sec_code = carac['tension_secondaire_nominale']
                    
                    # Mapeamento oficial Schneider SFT2841
                    secondary_map = {
                        '1': 110.0,
                        '2': 115.0,
                        '3': 120.0,
                        '4': 200.0,
                        '5': 230.0
                    }
                    
                    if sec_code == '6':
                        # User-defined: ler tension_secondaire_nominale_val
                        if 'tension_secondaire_nominale_val' in carac:
                            secondary_v = float(carac['tension_secondaire_nominale_val'])
                        else:
                            secondary_v = 115.0  # Fallback
                    else:
                        secondary_v = secondary_map.get(sec_code, 115.0)
                
                # Verificar se VT está habilitado (EnServiceTP)
                if 'EnServiceTP' in carac:
                    vt_enabled = (carac['EnServiceTP'] == '1')
                
                ct_vt_data['voltage_transformers'].append({
                    'vt_type': 'Main',
                    'primary_rating_v': primary_v,
                    'secondary_rating_v': secondary_v,
                    'ratio': f"{int(primary_v)}:{int(secondary_v)}",
                    'vt_enabled': vt_enabled  # NOVO
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
    
    def extract_all_parameters(self, ini_path: str) -> List[Dict[str, Any]]:
        """
        Extract ALL parameters from INI file including multi-line blocks
        Returns list of parameter dicts with section, key, value, and continuation lines
        """
        parameters = []
        
        # Read raw file to preserve multi-line values
        with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()
        
        # Also parse with ConfigParser for structured access
        config = configparser.ConfigParser()
        try:
            config.read(ini_path, encoding='utf-8')
        except UnicodeDecodeError:
            config.read(ini_path, encoding='latin-1')
        
        current_section = None
        line_num = 0
        
        for line in raw_content.split('\n'):
            line_num += 1
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith(';') or stripped.startswith('#'):
                continue
            
            # Section header
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1]
                continue
            
            # Key-value pairs
            if current_section and '=' in stripped:
                key, _, value = stripped.partition('=')
                key = key.strip()
                value = value.strip()
                
                # Special handling for [Matrice] section - multi-line blocks
                if current_section == 'Matrice':
                    # Matrice entries are like: Trip RL2 = {multi-line list}
                    # or: LED1 = {multi-line list}
                    parameters.append({
                        'section': current_section,
                        'key': key,
                        'value': value,
                        'line_number': line_num,
                        'is_multiline_block': True if 'Trip RL' in key or 'LED' in key else False
                    })
                else:
                    parameters.append({
                        'section': current_section,
                        'key': key,
                        'value': value,
                        'line_number': line_num,
                        'is_multiline_block': False
                    })
        
        return parameters
    
    def validate_extraction(self, ini_path: str, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate extraction completeness
        Returns validation metrics including completeness score and warnings
        """
        # Count lines in original file
        with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_lines = len(f.readlines())
        
        # Count non-empty, non-comment lines
        with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
            useful_lines = sum(1 for line in f if line.strip() 
                             and not line.strip().startswith(';') 
                             and not line.strip().startswith('#')
                             and not line.strip().startswith('['))
        
        extracted_count = len(parameters)
        
        # Calculate completeness score
        completeness_score = (extracted_count / useful_lines * 100) if useful_lines > 0 else 0
        
        # Generate warnings
        warnings = []
        if completeness_score < 95:
            warnings.append(f"Baixa cobertura: {completeness_score:.1f}% ({extracted_count}/{useful_lines} parâmetros)")
        
        # Check for missing critical sections
        sections_found = set(p['section'] for p in parameters)
        critical_sections = ['Sepam_Caracteristiques', 'Sepam_ConfigMaterielle', 'Matrice']
        missing_sections = [s for s in critical_sections if s not in sections_found]
        if missing_sections:
            warnings.append(f"Seções críticas ausentes: {', '.join(missing_sections)}")
        
        return {
            'total_lines': total_lines,
            'useful_lines': useful_lines,
            'extracted_parameters': extracted_count,
            'completeness_score': completeness_score,
            'warnings': warnings,
            'sections_found': list(sections_found)
        }
