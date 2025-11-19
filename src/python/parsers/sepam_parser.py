"""
SEPAM Parser
Parses .S40 files from SEPAM relays (Schneider Electric)
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from ..extractors.ini_extractor import IniExtractor


class SepamParser:
    """Parser for SEPAM .S40 configuration files"""
    
    def __init__(self):
        self.extractor = IniExtractor()
        self.manufacturer = 'SCHNEIDER ELECTRIC'
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a SEPAM .S40 file"""
        path = Path(file_path)
        
        # Extract all data
        extracted = self.extractor.extract_all(file_path)
        
        # Parse filename for metadata
        filename_metadata = self._parse_filename(path.name)
        
        # Combine all data
        parsed_data = {
            'source_file': str(path.absolute()),
            'file_name': path.name,
            'file_type': 'S40',
            'manufacturer': self.manufacturer,
            'relay_data': self._build_relay_data(extracted, filename_metadata),
            'ct_data': extracted['ct_vt_data']['current_transformers'],
            'vt_data': extracted['ct_vt_data']['voltage_transformers'],
            'protection_functions': extracted['protection_functions'],
            'raw_extracted': extracted
        }
        
        return parsed_data
    
    def _parse_filename(self, filename: str) -> Dict[str, Any]:
        """Parse metadata from filename
        Format: 00-MF-12_2016-03-31.S40
        - 00: Código da subestação
        - MF: Tipo de painel (Main Feeder - Alimentador Principal)
        - 12: Identificador das barras
        - 2016-03-31: Data de configuração
        """
        metadata = {
            'subestacao_codigo': None,
            'tipo_painel': None,
            'barras_identificador': None,
            'data_configuracao': None
        }
        
        # Remove extension
        name = filename.replace('.S40', '').replace('.s40', '')
        
        # Split by underscore
        parts = name.split('_')
        
        if len(parts) >= 1:
            # Parse location-type-bay (00-MF-12)
            location_part = parts[0]
            location_parts = location_part.split('-')
            
            if len(location_parts) >= 1:
                metadata['subestacao_codigo'] = location_parts[0]
            if len(location_parts) >= 2:
                metadata['tipo_painel'] = location_parts[1]
            if len(location_parts) >= 3:
                metadata['barras_identificador'] = location_parts[2]
        
        if len(parts) >= 2:
            # Date (2016-03-31)
            try:
                date_str = parts[1]
                metadata['data_configuracao'] = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                pass
        
        return metadata
    
    def _build_relay_data(self, extracted: Dict[str, Any], filename_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build relay data combining extracted and filename data"""
        model_info = extracted.get('model_info', {})
        
        relay_data = {
            'modelo_numero': model_info.get('model_number'),
            'referencia_planta': model_info.get('plant_reference'),
            'serial_number': model_info.get('serial_number'),
            'modelo_rele': model_info.get('model_type', 'SEPAM S40'),
            'versao_software': model_info.get('application'),
            'barras_identificador': filename_metadata.get('barras_identificador'),
            'subestacao_codigo': filename_metadata.get('subestacao_codigo'),
            'tipo_painel': filename_metadata.get('tipo_painel'),
            'data_configuracao': filename_metadata.get('data_configuracao'),
            'frequencia_hz': model_info.get('frequency', 60.0),
            'fabricante': self.manufacturer
        }
        
        # Extract voltage level from VT data
        vt_data = extracted.get('ct_vt_data', {}).get('voltage_transformers', [])
        if vt_data:
            # Get primary voltage from first VT
            primary_v = vt_data[0].get('primary_rating_v')
            if primary_v:
                relay_data['voltage_level_kv'] = primary_v / 1000.0
        
        return relay_data
    
    def validate_data(self, parsed_data: Dict[str, Any]) -> tuple[bool, list]:
        """Validate parsed data"""
        errors = []
        
        relay_data = parsed_data.get('relay_data', {})
        
        # Check required fields
        if not relay_data.get('modelo_rele'):
            errors.append("Missing model name")
        
        if not relay_data.get('barras_identificador'):
            errors.append("Missing barras identifier")
        
        # Check if at least one protection function is enabled
        prot_funcs = parsed_data.get('protection_functions', [])
        enabled_funcs = [f for f in prot_funcs if f.get('is_enabled')]
        if not enabled_funcs:
            errors.append("No protection functions enabled")
        
        # Check CT/VT data
        if not parsed_data.get('ct_data') and not parsed_data.get('vt_data'):
            errors.append("Missing both CT and VT data")
        
        return (len(errors) == 0, errors)
