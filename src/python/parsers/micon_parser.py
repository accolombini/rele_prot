"""
MICON Parser
Parses PDF files from MICON relays (GE models: P143, P241)
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from ..extractors.pdf_extractor import PdfExtractor
from ..utils.filename_parser import FilenameParser


class MiconParser:
    """Parser for MICON relay PDF files"""
    
    def __init__(self):
        self.extractor = PdfExtractor()
        self.filename_parser = FilenameParser()
        self.manufacturer = 'GENERAL ELECTRIC'
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a MICON PDF file"""
        path = Path(file_path)
        
        # Extract all data
        extracted = self.extractor.extract_all(file_path)
        
        # Verify manufacturer
        detected_manufacturer = extracted.get('manufacturer')
        if detected_manufacturer != self.manufacturer:
            raise ValueError(
                f"Expected {self.manufacturer} but detected {detected_manufacturer}"
            )
        
        # Parse filename for metadata
        filename_metadata = self._parse_filename(path.name)
        
        # Combine all data
        parsed_data = {
            'source_file': str(path.absolute()),
            'file_name': path.name,
            'file_type': 'PDF',
            'manufacturer': self.manufacturer,
            'relay_data': self._build_relay_data(extracted, filename_metadata),
            'ct_data': extracted['ct_vt_data']['current_transformers'],
            'vt_data': extracted['ct_vt_data']['voltage_transformers'],
            'protection_functions': self._parse_protection_functions(extracted['protection_functions']),
            'raw_extracted': extracted
        }
        
        return parsed_data
    
    def _parse_filename(self, filename: str) -> Dict[str, Any]:
        """Parse metadata from filename using FilenameParser"""
        result = self.filename_parser.parse_pdf_filename(filename)
        
        if not result.get('valid'):
            # Return empty metadata if parsing fails
            return {
                'modelo_rele': None,
                'barras_identificador': None,
                'data_configuracao': None,
                'tipo_painel_codigo': None,
                'ansi_codigo': None
            }
        
        return result
    
    def _build_relay_data(self, extracted: Dict[str, Any], filename_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build relay data combining extracted and filename data"""
        model_info = extracted.get('model_info', {})
        
        relay_data = {
            'modelo_numero': model_info.get('model_number'),
            'referencia_planta': model_info.get('plant_reference'),
            'modelo_rele': filename_metadata.get('modelo_rele') or model_info.get('model_type'),
            'versao_software': model_info.get('software_version'),
            'barras_identificador': filename_metadata.get('barras_identificador'),
            'identificador_elemento': filename_metadata.get('element'),
            'data_configuracao': filename_metadata.get('data_configuracao'),
            'frequencia_hz': model_info.get('frequency', 60.0),
            'tipo_painel_codigo': filename_metadata.get('tipo_painel_codigo'),
            'ansi_codigo': filename_metadata.get('ansi_codigo'),
            'fabricante': filename_metadata.get('fabricante', self.manufacturer)
        }
        
        # Extract voltage level from VT data
        vt_data = extracted.get('ct_vt_data', {}).get('voltage_transformers', [])
        if vt_data:
            # Get primary voltage from first VT
            primary_v = vt_data[0].get('primary_rating_v')
            if primary_v:
                relay_data['voltage_level_kv'] = primary_v / 1000.0
        
        return relay_data
    
    def _parse_protection_functions(self, raw_functions: list) -> list:
        """Parse and categorize protection functions"""
        parsed_functions = []
        
        # Map function names to ANSI codes
        ansi_mapping = {
            'Overcurrent': '50/51',
            'Short Circuit': '50/51',
            'Earth Fault': '50N/51N',
            'Sensitive E/F': '50N/51N',
            'Derived E/F': '50N/51N',
            'Neg Seq O/C': '46',
            'Thermal Overload': '49',
            'Volt Protection': '27/59',
            '3Ph Volt.Check': '27',
            'Freq Protection': '81',
            'Under Frequency': '81',
            'CB Fail': '50BF',
            'Stall Detection': '14',
            'Neg Seq O/V': '47',
            'Residual O/V NVD': '59N',
            'Loss of Load': '40',
            'Out of Step': '78',
            'Reverse power': '32',
            'Field Failure': '40',
            'RTD Inputs': 'RTD'
        }
        
        for func in raw_functions:
            function_name = func.get('function_name', '')
            
            # Determine ANSI code
            ansi_code = None
            for key, code in ansi_mapping.items():
                if key.lower() in function_name.lower():
                    ansi_code = code
                    break
            
            parsed_func = {
                'code': func.get('code'),
                'function_name': function_name,
                'ansi_code': ansi_code,
                'is_enabled': func.get('is_enabled', False),
                'setpoint': func.get('setpoint'),
                'raw_value': func.get('raw_value')
            }
            
            parsed_functions.append(parsed_func)
        
        return parsed_functions
    
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
