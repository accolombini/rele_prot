"""
Full Parameters CSV Exporter
Exporta TODOS os parâmetros extraídos do PDF para CSV completo
Atende aos requisitos de auditoria com 100% de cobertura
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class FullParametersExporter:
    """
    Exporta todos os parâmetros do relé para CSV detalhado
    
    Formato CSV:
    - Código | Parâmetro | Valor | Linhas Continuação | Timestamp
    - Delimitador: ponto-e-vírgula (;) para evitar conflitos
    """
    
    def __init__(self, output_dir: str = "outputs/csv", logger=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def export_full_parameters(self, 
                              parsed_data: Dict[str, Any], 
                              base_filename: str) -> str:
        """
        Export ALL parameters to detailed CSV
        
        Args:
            parsed_data: Complete parsed data including all_parameters
            base_filename: Base name for output file
        
        Returns:
            Path to created CSV file
        """
        filename = f"{base_filename}.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        try:
            with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
                # Use semicolon delimiter to avoid conflicts with values
                writer = csv.writer(f, delimiter=';')
                
                # Write header with metadata
                writer.writerow(['FULL PARAMETER EXTRACTION REPORT'])
                writer.writerow([''])
                writer.writerow(['Manufacturer', parsed_data.get('manufacturer', '')])
                writer.writerow(['Model', parsed_data.get('relay_data', {}).get('modelo_rele', '')])
                writer.writerow(['Barras', parsed_data.get('relay_data', {}).get('barras_identificador', '')])
                writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                
                # Validation metrics - try both locations for compatibility
                validation = parsed_data.get('validation', {})
                if not validation:
                    validation = parsed_data.get('raw_extracted', {}).get('validation', {})
                if validation:
                    writer.writerow([''])
                    writer.writerow(['EXTRACTION VALIDATION'])
                    writer.writerow(['Total Parameters', validation.get('total_parameters', 0)])
                    writer.writerow(['CT Count', validation.get('ct_count', 0)])
                    writer.writerow(['VT Count', validation.get('vt_count', 0)])
                    writer.writerow(['Protection Functions', validation.get('protection_functions', 0)])
                    writer.writerow(['Enabled Functions', validation.get('enabled_functions', 0)])
                    writer.writerow(['Completeness Score', f"{validation.get('completeness_score', 0):.1f}%"])
                    
                    if validation.get('warnings'):
                        writer.writerow([''])
                        writer.writerow(['WARNINGS'])
                        for warning in validation['warnings']:
                            writer.writerow(['', warning])
                
                # Main parameters table
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['ALL RELAY PARAMETERS'])
                writer.writerow([''])
                
                # Table headers
                writer.writerow([
                    'Code',
                    'Parameter',
                    'Value',
                    'Continuation Lines',
                    'Export Timestamp'
                ])
                
                # Get all parameters - try both locations for compatibility
                all_params = parsed_data.get('all_parameters', [])
                if not all_params:
                    all_params = parsed_data.get('raw_extracted', {}).get('all_parameters', [])
                
                if not all_params:
                    writer.writerow(['', 'No parameters extracted', '', '', ''])
                else:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    for param in all_params:
                        # Handle different parameter formats
                        # PDF format: code, parameter, value
                        # INI format: section, key, value
                        
                        if 'section' in param:
                            # SEPAM INI format
                            code = param.get('section', '')
                            parameter = param.get('key', '')
                            value = param.get('value', '')
                            continuation_str = 'Multiline' if param.get('is_multiline_block') else ''
                        else:
                            # PDF format
                            code = param.get('code', '')
                            parameter = param.get('parameter', '')
                            value = param.get('value', '')
                            continuation = param.get('continuation_lines', [])
                            continuation_str = ' | '.join(continuation) if continuation else ''
                        
                        writer.writerow([
                            code,
                            parameter,
                            value,
                            continuation_str,
                            timestamp
                        ])
                
                # Summary statistics
                writer.writerow([''])
                writer.writerow([''])
                writer.writerow(['EXTRACTION SUMMARY'])
                writer.writerow(['Total Parameters Extracted', len(all_params)])
                writer.writerow(['Parameters with Continuation', 
                               sum(1 for p in all_params if p.get('continuation_lines'))])
                writer.writerow(['Coverage Estimate', 
                               f"{min(100, (len(all_params) / 450) * 100):.1f}%"])
            
            # Atomic rename
            temp_filepath.rename(filepath)
            
            if self.logger:
                self.logger.info(f"  ✓ Full parameters CSV: {filename}")
                self.logger.info(f"    - Total parameters: {len(all_params)}")
                self.logger.info(f"    - With continuation: {sum(1 for p in all_params if p.get('continuation_lines'))}")
            
            return str(filepath)
            
        except Exception as e:
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise Exception(f"Failed to export full parameters: {str(e)}")
    
    def export_comparison_report(self, 
                                 original_params: List[Dict[str, Any]], 
                                 extracted_params: List[Dict[str, Any]], 
                                 base_filename: str) -> str:
        """
        Generate comparison report between original and extracted parameters
        
        Useful for audit validation
        """
        filename = f"{base_filename}_COMPARISON.csv"
        filepath = self.output_dir / filename
        temp_filepath = filepath.with_suffix('.csv.tmp')
        
        try:
            # Create code-based lookup
            extracted_by_code = {p['code']: p for p in extracted_params}
            
            with open(temp_filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                writer.writerow(['PARAMETER COMPARISON REPORT'])
                writer.writerow([''])
                writer.writerow(['Code', 'Parameter', 'Original Value', 
                               'Extracted Value', 'Status', 'Notes'])
                
                matched = 0
                missing = 0
                different = 0
                
                for orig in original_params:
                    code = orig.get('code')
                    param_name = orig.get('parameter')
                    orig_value = orig.get('value')
                    
                    if code in extracted_by_code:
                        extracted = extracted_by_code[code]
                        extr_value = extracted.get('value')
                        
                        if orig_value == extr_value:
                            status = '✓ Match'
                            matched += 1
                        else:
                            status = '⚠ Different'
                            different += 1
                        
                        writer.writerow([
                            code, param_name, orig_value, extr_value, status, ''
                        ])
                    else:
                        status = '✗ Missing'
                        missing += 1
                        writer.writerow([
                            code, param_name, orig_value, '', status, 
                            'Not found in extraction'
                        ])
                
                # Summary
                writer.writerow([''])
                writer.writerow(['COMPARISON SUMMARY'])
                writer.writerow(['Total Parameters (Original)', len(original_params)])
                writer.writerow(['Matched', matched])
                writer.writerow(['Different', different])
                writer.writerow(['Missing', missing])
                writer.writerow(['Match Rate', f"{(matched / len(original_params) * 100):.1f}%"])
            
            temp_filepath.rename(filepath)
            
            return str(filepath)
            
        except Exception as e:
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise Exception(f"Failed to export comparison report: {str(e)}")
