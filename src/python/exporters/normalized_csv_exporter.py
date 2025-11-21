"""
Normalized CSV Exporter
Exporta dados normalizados para CSVs consolidados (3FN)
"""

import csv
from pathlib import Path
from typing import Dict, Any, List


class NormalizedCsvExporter:
    """Exporta dados normalizados para CSVs consolidados"""
    
    # Headers para cada tabela 3FN
    RELAY_INFO_HEADERS = [
        'relay_id', 'source_file', 'manufacturer', 'model',
        'barras_identificador', 'subestacao_codigo', 'voltage_class_kv',
        'relay_type', 'config_date', 'frequency_hz', 'software_version',
        'vt_defined', 'vt_enabled', 'voltage_source', 'voltage_confidence',
        'processed_at'
    ]
    
    CT_DATA_HEADERS = [
        'ct_id', 'relay_id', 'ct_type', 'primary_a',
        'secondary_a', 'ratio', 'usage'
    ]
    
    VT_DATA_HEADERS = [
        'vt_id', 'relay_id', 'vt_type', 'primary_v',
        'secondary_v', 'ratio'
    ]
    
    PROTECTIONS_HEADERS = [
        'prot_id', 'relay_id', 'ansi_code', 'function_name',
        'is_enabled', 'setpoint_1', 'unit_1', 'time_dial', 'curve_type'
    ]
    
    PARAMETERS_HEADERS = [
        'param_id', 'relay_id', 'section_or_code', 'parameter_name',
        'value', 'continuation_lines', 'timestamp'
    ]
    
    def __init__(self, output_dir: str = "outputs/norm_csv", logger=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        
        # Paths dos CSVs consolidados
        self.relay_info_csv = self.output_dir / 'all_relays_info.csv'
        self.ct_data_csv = self.output_dir / 'all_ct_data.csv'
        self.vt_data_csv = self.output_dir / 'all_vt_data.csv'
        self.protections_csv = self.output_dir / 'all_protections.csv'
        self.parameters_csv = self.output_dir / 'all_parameters.csv'
    
    def initialize_csvs(self):
        """Cria CSVs com headers (limpa se existirem)"""
        self._create_csv_with_header(self.relay_info_csv, self.RELAY_INFO_HEADERS)
        self._create_csv_with_header(self.ct_data_csv, self.CT_DATA_HEADERS)
        self._create_csv_with_header(self.vt_data_csv, self.VT_DATA_HEADERS)
        self._create_csv_with_header(self.protections_csv, self.PROTECTIONS_HEADERS)
        self._create_csv_with_header(self.parameters_csv, self.PARAMETERS_HEADERS)
        
        if self.logger:
            self.logger.info(f"Initialized consolidated CSVs in: {self.output_dir}")
    
    def _create_csv_with_header(self, filepath: Path, headers: List[str]):
        """Cria CSV com header"""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
            writer.writeheader()
    
    def append_normalized_data(self, normalized_data: Dict[str, Any]):
        """
        Append normalized data to consolidated CSVs
        
        Args:
            normalized_data: Dictionary with keys: relay_info, cts, vts, protections, parameters
        """
        # Append relay info
        self._append_to_csv(
            self.relay_info_csv,
            [normalized_data['relay_info']],
            self.RELAY_INFO_HEADERS
        )
        
        # Append CTs (only if not empty)
        cts = normalized_data.get('cts', [])
        if cts and len(cts) > 0:
            self._append_to_csv(
                self.ct_data_csv,
                cts,
                self.CT_DATA_HEADERS
            )
        
        # Append VTs (only if not empty)
        vts = normalized_data.get('vts', [])
        if vts and len(vts) > 0:
            self._append_to_csv(
                self.vt_data_csv,
                vts,
                self.VT_DATA_HEADERS
            )
        
        # Append Protections
        if normalized_data.get('protections'):
            self._append_to_csv(
                self.protections_csv,
                normalized_data['protections'],
                self.PROTECTIONS_HEADERS
            )
        
        # Append Parameters
        if normalized_data.get('parameters'):
            self._append_to_csv(
                self.parameters_csv,
                normalized_data['parameters'],
                self.PARAMETERS_HEADERS
            )
        
        if self.logger:
            relay_id = normalized_data['relay_info']['relay_id']
            self.logger.info(f"    ✓ Appended to consolidated CSVs: {relay_id}")
    
    def _append_to_csv(self, filepath: Path, rows: List[Dict], headers: List[str]):
        """Append rows to CSV"""
        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';', extrasaction='ignore')
            for row in rows:
                writer.writerow(row)
