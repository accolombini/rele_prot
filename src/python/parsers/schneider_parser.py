"""Parser de arquivos PDF de relés Schneider Electric.

Este módulo implementa parser especializado para arquivos PDF exportados pelo
software Easergy Studio (Schneider Electric). Suporta múltiplos modelos de relés
industriais incluindo P122, P220 e P922.

Modelos suportados:
    - P122/P123: Relés de sobrecorrente (apenas TC)
    - P220/P22x: Relés de proteção de motores (apenas TC)
    - P922/P92x: Relés de tensão e frequência (apenas TP)

Formato de arquivo:
    - Extensão: .pdf
    - Software: Easergy Studio
    - Fabricante: Schneider Electric
    - Código identificador: "0120:" no início do arquivo

Exemplo de uso:
    >>> parser = SchneiderParser()
    >>> dados = parser.parse_file('inputs/pdf/P122_SE01-12_20240101.pdf')
    >>> print(f"Tipo: {dados['relay_type']}")
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from ..extractors.pdf_extractor import PdfExtractor
from ..utils.filename_parser import FilenameParser


class SchneiderParser:
    """Parser especializado para PDFs de relés Schneider (Easergy Studio).
    
    Processa arquivos PDF exportados do Easergy Studio, extraindo configurações
    de relés Schneider das séries P122, P220 e P922.
    
    Attributes:
        extractor (PdfExtractor): Extrator de conteúdo PDF
        filename_parser (FilenameParser): Parser de metadados de nome de arquivo
        manufacturer (str): Fabricante dos relés ('SCHNEIDER ELECTRIC')
    """
    
    def __init__(self) -> None:
        """Inicializa o parser Schneider com extratores apropriados.
        
        Configura extrator de PDF, parser de nomes de arquivo e define
        fabricante padrão.
        """
        self.extractor = PdfExtractor()
        self.filename_parser = FilenameParser()
        self.manufacturer = 'SCHNEIDER ELECTRIC'
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Processa arquivo PDF Schneider e extrai todos os dados do relé.
        
        Orquestra o processo completo de parse incluindo extração, validação
        de fabricante, determinação de tipo de relé e interpretação de metadados.
        
        Args:
            file_path: Caminho completo do arquivo PDF a ser processado
            
        Returns:
            Dicionário com dados estruturados do relé:
                - source_file: Caminho absoluto do arquivo
                - file_name: Nome do arquivo
                - file_type: Tipo do arquivo ('PDF')
                - manufacturer: Fabricante validado
                - relay_type: Tipo de aplicação do relé
                - relay_data: Dados principais do relé
                - ct_data: Configurações de TCs
                - vt_data: Configurações de TPs
                - protection_functions: Funções de proteção com códigos ANSI
                - all_parameters: Lista completa de parâmetros
                - validation: Resultado da validação
                - raw_extracted: Dados brutos extraídos
                
        Raises:
            ValueError: Se fabricante detectado não for Schneider Electric
            FileNotFoundError: Se arquivo não for encontrado
        """
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
        
        # Determine relay type and application
        model_name = filename_metadata.get('model') or extracted['model_info'].get('model_type')
        relay_type = self._determine_relay_type(model_name)
        
        # Combine all data
        parsed_data = {
            'source_file': str(path.absolute()),
            'file_name': path.name,
            'file_type': 'PDF',
            'manufacturer': self.manufacturer,
            'relay_type': relay_type,
            'relay_data': self._build_relay_data(extracted, filename_metadata, relay_type),
            'ct_data': extracted['ct_vt_data']['current_transformers'],
            'vt_data': extracted['ct_vt_data']['voltage_transformers'],
            'protection_functions': self._parse_protection_functions(extracted['protection_functions'], relay_type),
            'all_parameters': extracted.get('all_parameters', []),
            'validation': extracted.get('validation', {}),
            'raw_extracted': extracted
        }
        
        return parsed_data
    
    def _determine_relay_type(self, model_name: Optional[str]) -> str:
        """Determine relay type and application"""
        if not model_name:
            return 'Unknown'
        
        model_upper = model_name.upper()
        
        if 'P122' in model_upper or 'P123' in model_upper:
            return 'Overcurrent'  # TC only
        elif 'P220' in model_upper or 'P22' in model_upper:
            return 'Motor'  # TC only
        elif 'P922' in model_upper or 'P92' in model_upper:
            return 'Voltage'  # TP only
        else:
            return 'Unknown'
    
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
    
    def _build_relay_data(
        self, 
        extracted: Dict[str, Any], 
        filename_metadata: Dict[str, Any],
        relay_type: str
    ) -> Dict[str, Any]:
        """Build relay data combining extracted and filename data"""
        model_info = extracted.get('model_info', {})
        
        relay_data = {
            'modelo_numero': model_info.get('model_number'),
            'referencia_planta': model_info.get('plant_reference') or filename_metadata.get('element'),
            'modelo_rele': filename_metadata.get('modelo_rele') or model_info.get('model_type'),
            'serie_modelo': relay_type,
            'versao_software': model_info.get('software_version'),
            'barras_identificador': filename_metadata.get('barras_identificador'),
            'identificador_elemento': filename_metadata.get('element'),
            'data_configuracao': filename_metadata.get('data_configuracao'),
            'frequencia_hz': model_info.get('frequency', 60.0),
            'tipo_rele': relay_type,
            'tipo_painel_codigo': filename_metadata.get('tipo_painel_codigo'),
            'ansi_codigo': filename_metadata.get('ansi_codigo'),
            'fabricante': filename_metadata.get('fabricante', self.manufacturer)
        }
        
        # Extract voltage level from VT data (only for P922)
        if relay_type == 'Voltage':
            vt_data = extracted.get('ct_vt_data', {}).get('voltage_transformers', [])
            if vt_data:
                primary_v = vt_data[0].get('primary_rating_v')
                if primary_v:
                    relay_data['voltage_level_kv'] = primary_v / 1000.0
        
        return relay_data
    
    def _parse_protection_functions(self, raw_functions: list, relay_type: str) -> list:
        """Parse and categorize protection functions"""
        parsed_functions = []
        
        # ANSI code mapping specific to Schneider relays
        ansi_mapping = {
            # P122 - Overcurrent relay
            'I>': '50',
            'I>>': '51',
            'I>>>': '50',
            'Ie>': '50N',
            'Ie>>': '51N',
            'Ie>>>': '50N',
            'I2>': '46',
            'I2>>': '46',
            # P220 - Motor relay
            'THERMAL OVERLOAD': '49',
            'I>> FUNCTION': '51',
            'I0>> FUNCTION': '51N',
            'I0> FUNCTION': '50N',
            'I2> FUNCTION': '46',
            'BLOCKED ROTOR': '14',
            'STALLED ROTOR': '14',
            'I< FUNCTION': '37',
            # P922 - Voltage/Frequency relay
            'U<': '27',
            'U<<': '27',
            'U<<<': '27',
            'U>': '59',
            'U>>': '59',
            'U>>>': '59',
            'Vo>': '59N',
            'Vo>>': '59N',
            'V2>': '47',
            'V1<': '27D',
            'f1': '81',
            'f2': '81',
            'f3': '81',
            'f4': '81',
            'f5': '81',
            'f6': '81'
        }
        
        for func in raw_functions:
            function_name = func.get('function_name', '')
            code = func.get('code', '')
            
            # Determine ANSI code
            ansi_code = None
            for key, ansi in ansi_mapping.items():
                if key in function_name or key in code:
                    ansi_code = ansi
                    break
            
            # Parse setpoint value
            setpoint = func.get('setpoint')
            if not setpoint and 'raw_value' in func:
                # Try to extract value from context
                setpoint = self._extract_setpoint_value(code, func.get('raw_value'))
            
            parsed_func = {
                'code': code,
                'function_name': function_name,
                'ansi_code': ansi_code,
                'is_enabled': func.get('is_enabled', False),
                'setpoint': setpoint,
                'raw_value': func.get('raw_value')
            }
            
            parsed_functions.append(parsed_func)
        
        return parsed_functions
    
    def _extract_setpoint_value(self, code: str, raw_text: str) -> Optional[str]:
        """Extract setpoint value from raw text"""
        if not code or not raw_text:
            return None
        
        # Look for next line after code with value
        # Example: "0201: U<:" followed by "30.0V"
        pattern = f'{code}:.*?([\\d.]+\\s*[A-Za-z]*)'
        match = re.search(pattern, raw_text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def validate_data(self, parsed_data: Dict[str, Any]) -> tuple[bool, list]:
        """Validate parsed data"""
        errors = []
        
        relay_data = parsed_data.get('relay_data', {})
        relay_type = relay_data.get('relay_type')
        
        # Check required fields
        if not relay_data.get('modelo_rele'):
            errors.append("Missing model name")
        
        if not relay_data.get('barras_identificador'):
            errors.append("Missing barras identifier")
        
        # Type-specific validation
        if relay_type == 'Overcurrent' or relay_type == 'Motor':
            # Must have CT data
            if not parsed_data.get('ct_data'):
                errors.append(f"{relay_type} relay must have CT data")
            # Should NOT have VT data
            if parsed_data.get('vt_data'):
                errors.append(f"{relay_type} relay should not have VT data")
        
        elif relay_type == 'Voltage':
            # Must have VT data
            if not parsed_data.get('vt_data'):
                errors.append("Voltage relay must have VT data")
            # Should NOT have CT data
            if parsed_data.get('ct_data'):
                errors.append("Voltage relay should not have CT data")
        
        # Check if at least one protection function is enabled
        prot_funcs = parsed_data.get('protection_functions', [])
        enabled_funcs = [f for f in prot_funcs if f.get('is_enabled')]
        if not enabled_funcs:
            errors.append("No protection functions enabled")
        
        return (len(errors) == 0, errors)
