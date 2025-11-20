"""
Relay Normalizer
Normaliza dados completos do relé para formato 3FN
"""

import csv
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_normalizer import BaseNormalizer
from .unit_converter import UnitConverter
from ..utils.glossary_loader import GlossaryLoader


class RelayNormalizer(BaseNormalizer):
    """Normaliza dados de relés para 3FN"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.converter = UnitConverter()
        self.relay_counter = 0
        # Load glossary for relay type mapping
        # Path: src/python/normalizers/ -> src/python/ -> src/ -> root/
        glossary_path = Path(__file__).parent.parent.parent.parent / 'inputs' / 'glossario'
        self.glossary = GlossaryLoader(str(glossary_path))
    
    def normalize_from_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        Lê CSV da FASE 1 e normaliza
        
        Args:
            csv_path: Path to CSV file from FASE 1
        
        Returns:
            Normalized data dictionary with relay_info, cts, vts, protections, parameters
        """
        path = Path(csv_path)
        
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")
        
        self.log_info(f"Normalizing: {path.name}")
        
        # Parse CSV
        sections = self._parse_csv_sections(csv_path)
        
        # Generate relay ID
        self.relay_counter += 1
        relay_id = f"R{self.relay_counter:03d}"
        
        # Normalize each section
        normalized = {
            'relay_info': self._normalize_relay_info(sections, relay_id, path.name),
            'cts': self._normalize_cts(sections, relay_id),
            'vts': self._normalize_vts(sections, relay_id),
            'protections': self._normalize_protections(sections, relay_id),
            'parameters': self._normalize_parameters(sections, relay_id)
        }
        
        self.log_info(f"  → Relay: {relay_id}, CTs: {len(normalized['cts'])}, "
                     f"VTs: {len(normalized['vts'])}, "
                     f"Protections: {len(normalized['protections'])}, "
                     f"Parameters: {len(normalized['parameters'])}")
        
        return normalized
    
    def _parse_csv_sections(self, csv_path: str) -> Dict[str, Any]:
        """Parse CSV sections (header + parameters)"""
        sections = {
            'metadata': {},
            'validation': {},
            'parameters': []
        }
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            
            current_section = 'header'
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                # Header metadata
                if row[0] in ['Manufacturer', 'Model', 'Barras', 'Export Date']:
                    sections['metadata'][row[0].lower().replace(' ', '_')] = row[1] if len(row) > 1 else ''
                
                # Validation section
                elif row[0] in ['Total Parameters', 'CT Count', 'VT Count', 'Completeness Score']:
                    key = row[0].lower().replace(' ', '_')
                    sections['validation'][key] = row[1] if len(row) > 1 else ''
                
                # Parameters table header
                elif row[0] == 'Code' or row[0] == 'Section':
                    current_section = 'parameters'
                    continue
                
                # Parameter rows
                elif current_section == 'parameters' and row[0]:
                    # CSV format: Code;Parameter;Value;Continuation;Timestamp
                    # or: Section;Key;Value;LineNumber;Timestamp
                    if len(row) >= 3:
                        sections['parameters'].append({
                            'code_or_section': row[0],
                            'parameter_or_key': row[1] if len(row) > 1 else '',
                            'value': row[2] if len(row) > 2 else '',
                            'extra': row[3] if len(row) > 3 else '',
                            'timestamp': row[4] if len(row) > 4 else ''
                        })
        
        return sections
    
    def _normalize_relay_info(self, sections: Dict, relay_id: str, filename: str) -> Dict[str, Any]:
        """Normalize relay information with enhanced metadata"""
        metadata = sections.get('metadata', {})
        parameters = sections.get('parameters', [])
        
        # Extract base info
        manufacturer = metadata.get('manufacturer', '')
        model = metadata.get('model', '')
        barras = metadata.get('barras', '')
        
        # Parse filename for additional metadata
        filename_meta = self._parse_filename(filename)
        
        # Extract metadata from parameters
        param_meta = self._extract_metadata_from_parameters(parameters)
        
        # Get relay type from glossary
        relay_type = self.glossary.get_relay_type(model)
        if relay_type == 'Tipo Desconhecido':
            self.log_warning(f"Modelo não mapeado: {model} - Adicione em relay_models_config.json")
        
        # Determine subestacao_codigo (priority: param > filename > None)
        subestacao_codigo = (param_meta.get('substation_code') or 
                            filename_meta.get('subestacao') or 
                            None)
        
        # Determine voltage_class_kv from VT primary
        voltage_class_kv = None
        vt_defined = False
        vt_enabled = None
        
        vt_primary = param_meta.get('vt_primary_v')
        if vt_primary:
            vt_defined = True
            voltage_class_kv = round(vt_primary / 1000.0, 2)  # V → kV
            vt_enabled = param_meta.get('vt_enabled')
        
        return {
            'relay_id': relay_id,
            'source_file': filename,
            'manufacturer': manufacturer,
            'model': model,
            'barras_identificador': barras or filename_meta.get('barras'),
            'subestacao_codigo': subestacao_codigo,
            'voltage_class_kv': voltage_class_kv,
            'relay_type': relay_type,
            'config_date': filename_meta.get('config_date'),
            'frequency_hz': param_meta.get('frequency_hz'),
            'software_version': param_meta.get('software_version'),
            'vt_defined': vt_defined,
            'vt_enabled': vt_enabled,
            'voltage_source': 'doc' if vt_defined else None,
            'voltage_confidence': 1.0 if vt_defined else None,
            'processed_at': self.get_timestamp()
        }
    
    def _parse_filename(self, filename: str) -> Dict[str, Optional[str]]:
        """
        Parse filename for metadata
        Supports formats:
        - P122_52-MF-03B1_2021-03-17.csv (PDF Schneider)
        - P_122 52-MF-03B1_2021-03-17.csv (com espaço)
        - 00-MF-12_2016-03-31.csv (SEPAM)
        """
        metadata = {
            'modelo': None,
            'elemento': None,
            'subestacao': None,
            'barras': None,
            'config_date': None
        }
        
        # Remove extension
        name = Path(filename).stem
        
        # Regex robusta para PDFs Schneider/GE
        pattern_pdf = re.compile(
            r'^(?P<modelo>P_?\d{3})'           # P122 ou P_122
            r'[ _]+'                            # Espaço ou underscore
            r'(?P<elemento>\d{2})'              # 52 (ANSI)
            r'-'
            r'(?P<subestacao>[A-Z]{2})'        # MF, MK
            r'-'
            r'(?P<barras>[0-9A-Z]{3,4})'       # 03B1, 01BC
            r'(?:_(?P<data>\d{4}-\d{2}-\d{2}))?' # Data opcional
        , re.IGNORECASE)
        
        # Regex para SEPAM
        pattern_sepam = re.compile(
            r'^(?P<elemento>\d{2})'             # 00
            r'-'
            r'(?P<subestacao>[A-Z]{2})'        # MF
            r'-'
            r'(?P<barras>\d{2})'                # 12
            r'(?:_(?P<data>\d{4}-\d{2}-\d{2}))?' # Data opcional
        , re.IGNORECASE)
        
        # Try PDF pattern
        match = pattern_pdf.match(name)
        if match:
            metadata['modelo'] = match.group('modelo').replace('_', '')  # P_122 → P122
            metadata['elemento'] = match.group('elemento')
            metadata['subestacao'] = match.group('subestacao')
            metadata['barras'] = match.group('barras')
            if match.group('data'):
                metadata['config_date'] = match.group('data')
            return metadata
        
        # Try SEPAM pattern
        match = pattern_sepam.match(name)
        if match:
            metadata['elemento'] = match.group('elemento')
            metadata['subestacao'] = match.group('subestacao')
            metadata['barras'] = match.group('barras')
            if match.group('data'):
                metadata['config_date'] = match.group('data')
            return metadata
        
        # No match - log warning
        self.log_warning(f"Filename não corresponde a padrões conhecidos: {filename}")
        return metadata
    
    def _extract_metadata_from_parameters(self, parameters: List[Dict]) -> Dict[str, Any]:
        """Extract metadata from parameter list"""
        meta = {
            'substation_code': None,
            'vt_primary_v': None,
            'vt_enabled': None,
            'frequency_hz': None,
            'software_version': None
        }
        
        for param in parameters:
            param_name = param.get('parameter_or_key', '').lower()
            value = param.get('value', '')
            
            # SUBSTATION_CODE (SEPAM)
            if 'substation_code' in param_name and value:
                meta['substation_code'] = value
            
            # VT Primary (SEPAM: tension_primaire_nominale)
            if 'tension_primaire' in param_name or 'vt primary' in param_name:
                try:
                    # Extract numeric value
                    numeric = re.findall(r'\d+(?:\.\d+)?', value)
                    if numeric:
                        meta['vt_primary_v'] = float(numeric[0])
                except:
                    pass
            
            # VT Enabled (SEPAM: EnServiceTP)
            if 'enservicetp' in param_name or 'vt.*enabled' in param_name:
                if value in ['1', 'Yes', 'True', 'Enabled']:
                    meta['vt_enabled'] = True
                elif value in ['0', 'No', 'False', 'Disabled']:
                    meta['vt_enabled'] = False
            
            # Frequency (SEPAM: frequence_reseau)
            if 'frequence' in param_name or 'frequency' in param_name:
                try:
                    freq_str = re.findall(r'\d+', value)
                    if freq_str:
                        freq = int(freq_str[0])
                        if freq in [50, 60]:
                            meta['frequency_hz'] = float(freq)
                except:
                    pass
            
            # Software Version (SEPAM: application)
            if 'application' in param_name or 'software' in param_name or 'firmware' in param_name:
                if value and value not in ['0', '1']:
                    meta['software_version'] = value
        
        return meta
    
    def _normalize_cts(self, sections: Dict, relay_id: str) -> List[Dict[str, Any]]:
        """Normalize CT data"""
        cts = []
        ct_counter = 0
        
        # Search for CT parameters in data
        for param in sections.get('parameters', []):
            code = param.get('code_or_section', '')
            parameter = param.get('parameter_or_key', '')
            value = param.get('value', '')
            
            # CT RATIO codes (PDFs Schneider: 0120-0123, SEPAM: i_nominal)
            if code in ['0120', '0122'] or 'CT primary' in parameter:
                ct_counter += 1
                ct_type = 'Phase' if '0120' in code or 'Line CT' in parameter else 'Ground'
                
                # Try to find secondary value
                # This is simplified - real implementation needs pairing logic
                parsed = self.converter.parse_ct_ratio(f"{value}:5")  # Default secondary
                
                cts.append({
                    'ct_id': f"{relay_id}_CT{ct_counter:02d}",
                    'relay_id': relay_id,
                    'ct_type': ct_type,
                    'primary_a': parsed['primary_a'],
                    'secondary_a': parsed['secondary_a'],
                    'ratio': parsed['ratio'],
                    'usage': 'Line' if ct_type == 'Phase' else 'Residual'
                })
        
        return cts
    
    def _normalize_vts(self, sections: Dict, relay_id: str) -> List[Dict[str, Any]]:
        """Normalize VT data"""
        vts = []
        vt_counter = 0
        
        # Search for VT parameters
        for param in sections.get('parameters', []):
            code = param.get('code_or_section', '')
            parameter = param.get('parameter_or_key', '')
            value = param.get('value', '')
            
            # VT parameters (tension_primaire_nominale, Main VT Primary, etc.)
            if 'tension_primaire' in parameter.lower() or 'vt primary' in parameter.lower():
                vt_counter += 1
                vt_type = 'Main' if 'main' in parameter.lower() or 'primaire' in parameter.lower() else 'Residual'
                
                parsed = self.converter.parse_vt_ratio(f"{value}:120")  # Default secondary
                
                vts.append({
                    'vt_id': f"{relay_id}_VT{vt_counter:02d}",
                    'relay_id': relay_id,
                    'vt_type': vt_type,
                    'primary_v': parsed['primary_v'],
                    'secondary_v': parsed['secondary_v'],
                    'ratio': parsed['ratio']
                })
        
        return vts
    
    def _normalize_protections(self, sections: Dict, relay_id: str) -> List[Dict[str, Any]]:
        """Normalize protection functions"""
        protections = []
        prot_counter = 0
        
        # This is a simplified version - real implementation needs:
        # - ANSI code detection
        # - Setpoint parsing
        # - Enable/disable status
        
        # Look for protection codes (0200-0299 range typically)
        for param in sections.get('parameters', []):
            code = param.get('code_or_section', '')
            parameter = param.get('parameter_or_key', '')
            value = param.get('value', '')
            
            # Protection parameters (simplified detection)
            if code.startswith('02') or 'Protection' in parameter:
                prot_counter += 1
                
                # Try to extract ANSI code from parameter name
                ansi_code = self._extract_ansi_code(parameter)
                
                protections.append({
                    'prot_id': f"{relay_id}_P{prot_counter:03d}",
                    'relay_id': relay_id,
                    'ansi_code': ansi_code,
                    'function_name': parameter[:50],  # Truncate
                    'is_enabled': self.converter.normalize_boolean(value),
                    'setpoint_1': value if not self.converter.normalize_boolean(value) else None,
                    'unit_1': None,  # TODO: Extract unit
                    'time_dial': None,
                    'curve_type': None
                })
        
        return protections
    
    def _normalize_parameters(self, sections: Dict, relay_id: str) -> List[Dict[str, Any]]:
        """Normalize all parameters"""
        parameters = []
        param_counter = 0
        
        for param in sections.get('parameters', []):
            param_counter += 1
            
            parameters.append({
                'param_id': f"{relay_id}_PARAM{param_counter:04d}",
                'relay_id': relay_id,
                'section_or_code': param.get('code_or_section', ''),
                'parameter_name': param.get('parameter_or_key', ''),
                'value': param.get('value', ''),
                'continuation_lines': param.get('extra', ''),
                'timestamp': param.get('timestamp', '')
            })
        
        return parameters
    
    def _extract_ansi_code(self, parameter_name: str) -> str:
        """Extract ANSI code from parameter name"""
        # Common ANSI codes
        ansi_codes = ['50', '51', '50N', '51N', '46', '49', '37', '59', '27', '81', '67', '67N', '32']
        
        param_upper = parameter_name.upper()
        for code in ansi_codes:
            if code in param_upper:
                return code
        
        return 'Unknown'
    
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data from parsed format"""
        # This method is for future use if we normalize directly from parsed data
        # Currently we use normalize_from_csv
        raise NotImplementedError("Use normalize_from_csv instead")
