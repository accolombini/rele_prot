"""
CSV Exporter - High Reliability Data Export
Exports relay data to CSV format with strict validation and error handling
CRITICAL SYSTEM: Data integrity and precision are paramount
"""

import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation


class CsvExporter:
    """
    Robust CSV exporter for relay protection data
    
    Features:
    - Strict data validation
    - Type checking and conversion
    - UTF-8 encoding (BOM for Excel compatibility)
    - Detailed error reporting
    - Atomic file operations (temp file + rename)
    - Comprehensive logging
    """
    
    def __init__(self, output_dir: str, logger=None):
        """
        Initialize CSV exporter
        
        Args:
            output_dir: Directory for CSV output files
            logger: Logger instance (optional)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        
        # Validation rules
        self.validation_rules = {
            'relay_data': {
                'required_fields': ['modelo_rele', 'barras_identificador'],
                'numeric_fields': ['frequencia_hz', 'voltage_level_kv'],
                'string_fields': ['modelo_numero', 'serial_number', 'referencia_planta']
            },
            'ct_data': {
                'required_fields': ['tc_type', 'primary_rating_a', 'secondary_rating_a'],
                'numeric_fields': ['primary_rating_a', 'secondary_rating_a'],
                'valid_types': ['Phase', 'Residual', 'Ground', 'Neutral']
            },
            'vt_data': {
                'required_fields': ['vt_type', 'primary_rating_v', 'secondary_rating_v'],
                'numeric_fields': ['primary_rating_v', 'secondary_rating_v'],
                'valid_types': ['Main', 'Residual', 'Auxiliary']
            }
        }
    
    def export_relay_data(self, parsed_data: Dict[str, Any], base_filename: str) -> str:
        """
        Export complete relay data to ONE consolidated CSV file
        
        Args:
            parsed_data: Complete parsed data from parser
            base_filename: Base name for output file (without extension)
        
        Returns:
            Path to created consolidated CSV file
        
        Raises:
            ValueError: If data validation fails
            IOError: If file operations fail
        """
        self._log_info(f"Starting consolidated CSV export for: {base_filename}")
        
        # Validate input data
        validation_result = self._validate_parsed_data(parsed_data)
        if not validation_result['valid']:
            error_msg = f"Data validation failed: {', '.join(validation_result['errors'])}"
            self._log_error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Generate single consolidated CSV file
            csv_file = self._export_consolidated_csv(
                parsed_data,
                base_filename
            )
            
            self._log_info(f"✓ Consolidated CSV export completed: {Path(csv_file).name}")
            return csv_file
            
        except Exception as e:
            self._log_error(f"CSV export failed: {str(e)}")
            raise
    
    def _export_consolidated_csv(self, parsed_data: Dict[str, Any], base_filename: str) -> str:
        """
        Export all relay data to a single consolidated CSV file
        Sections: Relay Summary, CTs, VTs, Protection Functions
        """
        filename = f"{base_filename}.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        relay_data = parsed_data['relay_data']
        manufacturer = parsed_data['manufacturer']
        barras_id = relay_data['barras_identificador']
        
        try:
            with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                
                # ============ SECTION 1: RELAY SUMMARY ============
                writer.writerow(['RELAY SUMMARY'])
                writer.writerow([])  # Blank line
                
                relay_headers = [
                    'Manufacturer', 'Model Name', 'Model Number', 'Serial Number',
                    'Plant Reference', 'Barras Identificador', 'Subestação Código',
                    'Tipo Painel', 'Voltage Level (kV)', 'Frequency (Hz)',
                    'Data Configuração', 'Software Version', 'Export Timestamp'
                ]
                writer.writerow(relay_headers)
                
                relay_row = [
                    str(manufacturer),
                    str(relay_data.get('modelo_rele', '')),
                    str(relay_data.get('modelo_numero', '')),
                    str(relay_data.get('serial_number', '')),
                    str(relay_data.get('referencia_planta', '')),
                    str(barras_id),
                    str(relay_data.get('subestacao_codigo', '')),
                    str(relay_data.get('tipo_painel', '')),
                    self._format_number(relay_data.get('voltage_level_kv'), decimals=3),
                    self._format_number(relay_data.get('frequencia_hz'), decimals=2),
                    self._format_date(relay_data.get('data_configuracao')),
                    str(relay_data.get('versao_software', '')),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                writer.writerow(relay_row)
                writer.writerow([])  # Blank line separator
                
                # ============ SECTION 2: CURRENT TRANSFORMERS ============
                ct_data = parsed_data.get('ct_data', [])
                if ct_data:
                    writer.writerow(['CURRENT TRANSFORMERS'])
                    writer.writerow([])
                    
                    ct_headers = [
                        'Barras Identificador', 'TC Type', 'Primary Rating (A)',
                        'Secondary Rating (A)', 'Ratio', 'Export Timestamp'
                    ]
                    writer.writerow(ct_headers)
                    
                    for ct in ct_data:
                        tc_type = ct.get('tc_type', 'Phase')
                        if tc_type not in self.validation_rules['ct_data']['valid_types']:
                            tc_type = 'Phase'
                        
                        primary_a = self._validate_positive_number(
                            ct.get('primary_rating_a'), 'CT primary'
                        )
                        secondary_a = self._validate_positive_number(
                            ct.get('secondary_rating_a'), 'CT secondary'
                        )
                        
                        ct_row = [
                            str(barras_id),
                            str(tc_type),
                            self._format_number(primary_a, decimals=2),
                            self._format_number(secondary_a, decimals=2),
                            str(ct.get('ratio', '')),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                        writer.writerow(ct_row)
                    
                    writer.writerow([])  # Blank line separator
                
                # ============ SECTION 3: VOLTAGE TRANSFORMERS ============
                vt_data = parsed_data.get('vt_data', [])
                if vt_data:
                    writer.writerow(['VOLTAGE TRANSFORMERS'])
                    writer.writerow([])
                    
                    vt_headers = [
                        'Barras Identificador', 'VT Type', 'Primary Rating (V)',
                        'Secondary Rating (V)', 'Ratio', 'Export Timestamp'
                    ]
                    writer.writerow(vt_headers)
                    
                    for vt in vt_data:
                        vt_type = vt.get('vt_type', 'Main')
                        if vt_type not in self.validation_rules['vt_data']['valid_types']:
                            vt_type = 'Main'
                        
                        primary_v = self._validate_positive_number(
                            vt.get('primary_rating_v'), 'VT primary'
                        )
                        secondary_v = self._validate_positive_number(
                            vt.get('secondary_rating_v'), 'VT secondary'
                        )
                        
                        vt_row = [
                            str(barras_id),
                            str(vt_type),
                            self._format_number(primary_v, decimals=2),
                            self._format_number(secondary_v, decimals=2),
                            str(vt.get('ratio', '')),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                        writer.writerow(vt_row)
                    
                    writer.writerow([])  # Blank line separator
                
                # ============ SECTION 4: PROTECTION FUNCTIONS ============
                prot_funcs = parsed_data.get('protection_functions', [])
                enabled_funcs = [f for f in prot_funcs if f.get('is_enabled')]
                
                if enabled_funcs:
                    writer.writerow(['PROTECTION FUNCTIONS'])
                    writer.writerow([])
                    
                    prot_headers = [
                        'Barras Identificador', 'ANSI Code', 'Section Name',
                        'Status', 'Active Thresholds', 'Setpoints (JSON)', 'Export Timestamp'
                    ]
                    writer.writerow(prot_headers)
                    
                    for func in enabled_funcs:
                        setpoints = func.get('setpoints', {})
                        setpoints_json = json.dumps(setpoints, ensure_ascii=False) if setpoints else '{}'
                        
                        prot_row = [
                            str(barras_id),
                            str(func.get('ansi_code', '')),
                            str(func.get('section', '')),
                            'ENABLED',
                            ', '.join(func.get('active_thresholds', [])),
                            setpoints_json,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                        writer.writerow(prot_row)
            
            # Atomic rename
            temp_filepath.rename(filepath)
            
            self._log_info(f"  ✓ Consolidated CSV: {filename}")
            self._log_info(f"    - Relay data: 1 row")
            self._log_info(f"    - CTs: {len(ct_data)} transformers")
            self._log_info(f"    - VTs: {len(vt_data)} transformers")
            self._log_info(f"    - Protection functions: {len(enabled_funcs)} enabled")
            
            return str(filepath)
            
        except Exception as e:
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise
    
    def _export_relay_summary(self, relay_data: Dict[str, Any], manufacturer: str, base_filename: str) -> str:
        """Export relay summary data"""
        filename = f"{base_filename}_relay_summary.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        headers = [
            'manufacturer',
            'modelo_rele',
            'modelo_numero',
            'serial_number',
            'referencia_planta',
            'barras_identificador',
            'subestacao_codigo',
            'tipo_painel',
            'voltage_level_kv',
            'frequencia_hz',
            'data_configuracao',
            'versao_software',
            'export_timestamp'
        ]
        
        # Prepare row data with type conversion
        row_data = {
            'manufacturer': str(manufacturer),
            'modelo_rele': str(relay_data.get('modelo_rele', '')),
            'modelo_numero': str(relay_data.get('modelo_numero', '')),
            'serial_number': str(relay_data.get('serial_number', '')),
            'referencia_planta': str(relay_data.get('referencia_planta', '')),
            'barras_identificador': str(relay_data.get('barras_identificador', '')),
            'subestacao_codigo': str(relay_data.get('subestacao_codigo', '')),
            'tipo_painel': str(relay_data.get('tipo_painel', '')),
            'voltage_level_kv': self._format_number(relay_data.get('voltage_level_kv'), decimals=3),
            'frequencia_hz': self._format_number(relay_data.get('frequencia_hz'), decimals=2),
            'data_configuracao': self._format_date(relay_data.get('data_configuracao')),
            'versao_software': str(relay_data.get('versao_software', '')),
            'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Write to temporary file first (atomic operation)
        with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerow(row_data)
        
        # Rename temp file to final (atomic on POSIX systems)
        temp_filepath.rename(filepath)
        
        self._log_info(f"  ✓ Relay summary exported: {filename}")
        return str(filepath)
    
    def _export_ct_data(self, ct_data: List[Dict[str, Any]], barras_id: str, base_filename: str) -> str:
        """Export CT (Current Transformer) data"""
        filename = f"{base_filename}_ct_data.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        headers = [
            'barras_identificador',
            'tc_type',
            'primary_rating_a',
            'secondary_rating_a',
            'ratio',
            'export_timestamp'
        ]
        
        rows = []
        for idx, ct in enumerate(ct_data):
            # Validate CT type
            tc_type = ct.get('tc_type', 'Phase')
            if tc_type not in self.validation_rules['ct_data']['valid_types']:
                self._log_warning(f"Invalid CT type '{tc_type}' at index {idx}, using 'Phase'")
                tc_type = 'Phase'
            
            # Validate and convert ratings
            primary_a = self._validate_positive_number(
                ct.get('primary_rating_a'),
                f"CT {idx} primary rating"
            )
            secondary_a = self._validate_positive_number(
                ct.get('secondary_rating_a'),
                f"CT {idx} secondary rating"
            )
            
            rows.append({
                'barras_identificador': str(barras_id),
                'tc_type': str(tc_type),
                'primary_rating_a': self._format_number(primary_a, decimals=2),
                'secondary_rating_a': self._format_number(secondary_a, decimals=2),
                'ratio': str(ct.get('ratio', f"{int(primary_a) if primary_a else 0}:{int(secondary_a) if secondary_a else 0}")),
                'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)
        
        temp_filepath.rename(filepath)
        
        self._log_info(f"  ✓ CT data exported: {filename} ({len(rows)} transformers)")
        return str(filepath)
    
    def _export_vt_data(self, vt_data: List[Dict[str, Any]], barras_id: str, base_filename: str) -> str:
        """Export VT (Voltage Transformer) data"""
        filename = f"{base_filename}_vt_data.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        headers = [
            'barras_identificador',
            'vt_type',
            'primary_rating_v',
            'secondary_rating_v',
            'ratio',
            'export_timestamp'
        ]
        
        rows = []
        for idx, vt in enumerate(vt_data):
            # Validate VT type
            vt_type = vt.get('vt_type', 'Main')
            if vt_type not in self.validation_rules['vt_data']['valid_types']:
                self._log_warning(f"Invalid VT type '{vt_type}' at index {idx}, using 'Main'")
                vt_type = 'Main'
            
            # Validate and convert ratings
            primary_v = self._validate_positive_number(
                vt.get('primary_rating_v'),
                f"VT {idx} primary rating"
            )
            secondary_v = self._validate_positive_number(
                vt.get('secondary_rating_v'),
                f"VT {idx} secondary rating"
            )
            
            rows.append({
                'barras_identificador': str(barras_id),
                'vt_type': str(vt_type),
                'primary_rating_v': self._format_number(primary_v, decimals=2),
                'secondary_rating_v': self._format_number(secondary_v, decimals=2),
                'ratio': str(vt.get('ratio', f"{int(primary_v) if primary_v else 0}:{int(secondary_v) if secondary_v else 0}")),
                'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)
        
        temp_filepath.rename(filepath)
        
        self._log_info(f"  ✓ VT data exported: {filename} ({len(rows)} transformers)")
        return str(filepath)
    
    def _export_protection_functions(self, prot_funcs: List[Dict[str, Any]], barras_id: str, base_filename: str) -> str:
        """Export protection functions data"""
        filename = f"{base_filename}_protection_functions.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        headers = [
            'barras_identificador',
            'ansi_code',
            'section_name',
            'is_enabled',
            'active_thresholds',
            'setpoints_json',
            'export_timestamp'
        ]
        
        rows = []
        for func in prot_funcs:
            # Only export enabled functions (optional: change to export all)
            if not func.get('is_enabled', False):
                continue
            
            # Serialize setpoints to JSON for storage
            setpoints = func.get('setpoints', {})
            setpoints_json = json.dumps(setpoints, ensure_ascii=False) if setpoints else '{}'
            
            rows.append({
                'barras_identificador': str(barras_id),
                'ansi_code': str(func.get('ansi_code', '')),
                'section_name': str(func.get('section', '')),
                'is_enabled': 'TRUE' if func.get('is_enabled') else 'FALSE',
                'active_thresholds': ', '.join(func.get('active_thresholds', [])),
                'setpoints_json': setpoints_json,
                'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)
        
        temp_filepath.rename(filepath)
        
        self._log_info(f"  ✓ Protection functions exported: {filename} ({len(rows)} enabled functions)")
        return str(filepath)
    
    def _validate_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive data validation
        
        Returns:
            Dict with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Check top-level structure
        if not isinstance(parsed_data, dict):
            return {'valid': False, 'errors': ['Parsed data must be a dictionary']}
        
        required_keys = ['manufacturer', 'relay_data']
        for key in required_keys:
            if key not in parsed_data:
                errors.append(f"Missing required key: {key}")
        
        # Validate relay_data
        relay_data = parsed_data.get('relay_data', {})
        if not isinstance(relay_data, dict):
            errors.append("relay_data must be a dictionary")
        else:
            for field in self.validation_rules['relay_data']['required_fields']:
                if not relay_data.get(field):
                    errors.append(f"relay_data missing required field: {field}")
        
        # Validate CT data if present
        ct_data = parsed_data.get('ct_data', [])
        if ct_data and not isinstance(ct_data, list):
            errors.append("ct_data must be a list")
        
        # Validate VT data if present
        vt_data = parsed_data.get('vt_data', [])
        if vt_data and not isinstance(vt_data, list):
            errors.append("vt_data must be a list")
        
        # At least one transformer type should be present
        if not ct_data and not vt_data:
            errors.append("At least one of ct_data or vt_data must be present")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_positive_number(self, value: Any, field_name: str) -> Optional[float]:
        """Validate and convert to positive number"""
        if value is None:
            self._log_warning(f"{field_name}: None value encountered")
            return None
        
        try:
            num = float(value)
            if num <= 0:
                self._log_warning(f"{field_name}: Non-positive value {num}, using absolute")
                return abs(num)
            return num
        except (ValueError, TypeError):
            self._log_error(f"{field_name}: Invalid numeric value '{value}'")
            return None
    
    def _format_number(self, value: Any, decimals: int = 2) -> str:
        """Format number with fixed decimals"""
        if value is None:
            return ''
        
        try:
            num = float(value)
            return f"{num:.{decimals}f}"
        except (ValueError, TypeError):
            return ''
    
    def _format_date(self, value: Any) -> str:
        """Format date to ISO string"""
        if value is None:
            return ''
        
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
        else:
            return str(value)
    
    def _cleanup_files(self, file_paths: List[str]) -> None:
        """Remove files on export failure"""
        for filepath in file_paths:
            try:
                Path(filepath).unlink(missing_ok=True)
                self._log_info(f"Cleaned up partial file: {filepath}")
            except Exception as e:
                self._log_error(f"Failed to cleanup {filepath}: {str(e)}")
    
    def _log_info(self, message: str) -> None:
        """Log info message"""
        if self.logger:
            self.logger.info(message)
    
    def _log_warning(self, message: str) -> None:
        """Log warning message"""
        if self.logger:
            self.logger.warning(message)
    
    def _log_error(self, message: str) -> None:
        """Log error message"""
        if self.logger:
            self.logger.error(message)
