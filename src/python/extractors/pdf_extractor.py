"""
PDF Extractor for MICON Relay Files
Extracts text content from PDF files exported from .set files
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pdfplumber


class PdfExtractor:
    """Extracts structured data from PDF relay configuration files"""
    
    def __init__(self):
        self.manufacturer_signatures = {
            'SCHNEIDER ELECTRIC': ['Easergy Studio'],
            'GENERAL ELECTRIC': ['MiCOM S1 Agile', 'MiCOM Agile']
        }
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    def extract_by_pages(self, pdf_path: str) -> List[str]:
        """Extract text page by page"""
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        return pages
    
    def detect_manufacturer(self, pdf_path: str) -> Optional[str]:
        """Detect manufacturer from PDF footer/metadata"""
        text = self.extract_text(pdf_path)
        
        for manufacturer, signatures in self.manufacturer_signatures.items():
            for signature in signatures:
                if signature in text:
                    return manufacturer
        
        return None
    
    def extract_model_info(self, text: str) -> Dict[str, Any]:
        """Extract relay model information"""
        model_info = {
            'model_number': None,
            'plant_reference': None,
            'software_version': None,
            'frequency': None,
            'model_type': None
        }
        
        # Model Number (15-digit format: P143312A2A0150C)
        model_match = re.search(r'Model Number:\s*([A-Z0-9]{15})', text)
        if model_match:
            model_info['model_number'] = model_match.group(1)
        
        # Plant Reference
        plant_ref_match = re.search(r'Plant Reference:\s*(.+)', text)
        if plant_ref_match:
            model_info['plant_reference'] = plant_ref_match.group(1).strip()
        
        # Software Version
        software_match = re.search(r'Software (?:Version|Ref\.?\s*1):\s*(.+)', text)
        if software_match:
            model_info['software_version'] = software_match.group(1).strip()
        
        # Frequency
        freq_match = re.search(r'Frequency:\s*(\d+)\s*Hz', text)
        if freq_match:
            model_info['frequency'] = float(freq_match.group(1))
        
        # Model Type (P122, P143, P220, P241, P922)
        type_match = re.search(r'TYPE\s*=:\s*(P\d+[-\d]*)', text)
        if type_match:
            model_info['model_type'] = type_match.group(1)
        else:
            # Try from filename or model number
            type_match = re.search(r'(P\d+)', text[:500])
            if type_match:
                model_info['model_type'] = type_match.group(1)
        
        return model_info
    
    def extract_ct_vt_data(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract CT and VT ratios"""
        ct_vt_data = {
            'current_transformers': [],
            'voltage_transformers': []
        }
        
        # Extract CT ratios (various formats - Schneider and GE)
        # Schneider formats: "PRIM PH =: 100", "Line CT primary: 1500"
        # GE formats: "Phase CT Primary: 400.0 A"
        ct_patterns = [
            # Schneider Easergy (P122) - "Line CT primary: 1500" + "Line CT sec: 5"
            (r'Line CT primary:\s*(\d+\.?\d*)', r'Line CT sec:\s*(\d+\.?\d*)', 'Phase'),
            (r'E/Gnd CT primary:\s*(\d+\.?\d*)', r'E/Gnd CT sec:\s*(\d+\.?\d*)', 'Ground'),
            # Schneider Easergy (P220) - "PRIM PH =: 100" + "SEC PH =: 5"
            (r'PRIM PH\s*=:\s*(\d+\.?\d*)', r'SEC PH\s*=:\s*(\d+\.?\d*)', 'Phase'),
            (r'PRIM E\s*=:\s*(\d+\.?\d*)', r'SEC E\s*=:\s*(\d+\.?\d*)', 'Ground'),
            # GE MiCOM (P143, P241) - "Phase CT Primary: 400.0 A"
            (r'Phase CT Primary:\s*(\d+\.?\d*)\s*A', r'Phase CT Sec\'y:\s*(\d+\.?\d*)\s*A', 'Phase'),
            (r'E/F CT Primary:\s*(\d+\.?\d*)\s*A', r'E/F CT Secondary:\s*(\d+\.?\d*)\s*A', 'Ground'),
            (r'SEF CT Primary:\s*(\d+\.?\d*)\s*A', r'SEF CT Secondary:\s*(\d+\.?\d*)\s*A', 'SEF'),
        ]
        
        for prim_pattern, sec_pattern, ct_type in ct_patterns:
            prim_match = re.search(prim_pattern, text)
            sec_match = re.search(sec_pattern, text)
            
            if prim_match and sec_match:
                primary = float(prim_match.group(1))
                secondary = float(sec_match.group(1))
                ct_vt_data['current_transformers'].append({
                    'tc_type': ct_type,
                    'primary_rating_a': primary,
                    'secondary_rating_a': secondary,
                    'ratio': f"{int(primary)}:{int(secondary)}"
                })
        
        # Extract VT ratios (Schneider and GE formats)
        # Schneider (P922): "Main VT Primary: 13800V" (no space before V)
        # GE: "Main VT Primary: 13.80 kV" or "4160 V"
        vt_patterns = [
            # Schneider Easergy (P922) - "Main VT Primary: 13800V" (sem espaço antes do V)
            (r'Main VT Primary:\s*(\d+\.?\d*)V\b', r'Main VT Secundary:\s*(\d+\.?\d*)V\b', 'Main'),
            # GE MiCOM - "Main VT Primary: 13.80 kV" ou "4160 V"
            (r'Main VT Primary:\s*(\d+\.?\d*)\s*(?:kV|V)', r'Main VT Sec\'y:\s*(\d+\.?\d*)\s*V', 'Main'),
            (r'C/S VT Primary:\s*(\d+\.?\d*)\s*V', r'C/S VT Secondary:\s*(\d+\.?\d*)\s*V', 'Check Sync'),
            # Schneider (P922) - "E/Gnd VT Primary: 20000V" (sem espaço antes do V)
            (r'E/Gnd VT Primary:\s*(\d+\.?\d*)V\b', r'E/Gnd VT Secundary:\s*(\d+\.?\d*)V\b', 'Residual'),
            (r'NVD VT Primary:\s*(\d+\.?\d*)\s*V', r'NVD VT Secondary:\s*(\d+\.?\d*)\s*V', 'NVD'),
        ]
        
        for prim_pattern, sec_pattern, vt_type in vt_patterns:
            prim_match = re.search(prim_pattern, text)
            sec_match = re.search(sec_pattern, text)
            
            if prim_match and sec_match:
                primary = float(prim_match.group(1))
                secondary = float(sec_match.group(1))
                
                # Convert kV to V if needed
                if primary < 1000 and 'kV' in prim_match.group(0):
                    primary = primary * 1000
                
                ct_vt_data['voltage_transformers'].append({
                    'vt_type': vt_type,
                    'primary_rating_v': primary,
                    'secondary_rating_v': secondary,
                    'ratio': f"{int(primary)}:{int(secondary)}"
                })
        
        return ct_vt_data
    
    def extract_protection_functions(self, text: str) -> List[Dict[str, Any]]:
        """Extract protection functions and their status"""
        functions = []
        
        # Pattern for functions with YES/NO status
        # Example: "0210: I>> FUNCTION ?: YES"
        yes_no_pattern = r'(\d{4}):\s*(.+?)\s+FUNCTION\s*\?:\s*(YES|NO)'
        for match in re.finditer(yes_no_pattern, text):
            code = match.group(1)
            function_name = match.group(2).strip()
            is_enabled = match.group(3) == 'YES'
            
            functions.append({
                'code': code,
                'function_name': function_name,
                'is_enabled': is_enabled,
                'raw_value': match.group(3)
            })
        
        # Pattern for functions with Enabled/Disabled status
        # Example: "09.10: Overcurrent: Enabled"
        enabled_pattern = r'(\d{2}\.\d{2}):\s*(.+?):\s*(Enabled|Disabled)'
        for match in re.finditer(enabled_pattern, text):
            code = match.group(1)
            function_name = match.group(2).strip()
            is_enabled = match.group(3) == 'Enabled'
            
            functions.append({
                'code': code,
                'function_name': function_name,
                'is_enabled': is_enabled,
                'raw_value': match.group(3)
            })
        
        # Pattern for functions with values (may indicate they're configured)
        # Example: "0200: Function I>: Yes" followed by "0201: I>: 0.63In"
        function_value_pattern = r'(\d{4}):\s*Function\s+(.+?):\s*(Yes|No)'
        for match in re.finditer(function_value_pattern, text):
            code = match.group(1)
            function_name = match.group(2).strip()
            is_enabled = match.group(3) == 'Yes'
            
            # Look for associated value
            value_code = str(int(code) + 1).zfill(4)
            value_pattern = f'{value_code}:\\s*{re.escape(function_name)}:\\s*(.+)'
            value_match = re.search(value_pattern, text)
            
            function_data = {
                'code': code,
                'function_name': function_name,
                'is_enabled': is_enabled,
                'raw_value': match.group(3)
            }
            
            if value_match:
                function_data['setpoint'] = value_match.group(1).strip()
            
            functions.append(function_data)
        
        return functions
    
    def extract_all_parameters(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract ALL parameters from PDF with support for multi-line values
        
        Captures:
        - Standard: "0120: Line CT primary: 1500"
        - GE Format: "00.01: Language: English"
        - With ?: "018A: CB Fail ?: Yes"
        - With =: "0201: I>: 0.63In" or "0201: I> = 0.63In"
        - Multi-line: "0171: Trip: RL2" + continuation lines
        - No code continuation: Lines without code that belong to previous param
        
        Returns list of dicts with: code, parameter, value, continuation_lines
        """
        parameters = []
        lines = text.split('\n')
        
        # Multiple patterns to capture different formats
        # Pattern 1: "CODE: Parameter: Value" or "CODE: Parameter ?: Value"
        # Supports: "0120: ..." (4 digits) and "00.01: ..." (GE format)
        param_pattern1 = re.compile(r'^(\d{2}\.?\d{2}):\s*(.+?)(?:\s*\?)?:\s*(.+)$')
        # Pattern 2: "CODE: Parameter = Value" or "CODE: Parameter=Value"
        param_pattern2 = re.compile(r'^(\d{2}\.?\d{2}):\s*(.+?)\s*=\s*(.+)$')
        # Pattern 3: "CODE: Parameter" (value on next line or just parameter name)
        param_pattern3 = re.compile(r'^(\d{2}\.?\d{2}):\s*(.+)$')
        
        current_param = None
        continuation_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match a parameter line with code (try patterns in order)
            match = param_pattern1.match(line) or param_pattern2.match(line)
            
            if match:
                # Save previous parameter if exists
                if current_param:
                    current_param['continuation_lines'] = continuation_lines
                    parameters.append(current_param)
                    continuation_lines = []
                
                # Start new parameter
                code = match.group(1)
                param_name = match.group(2).strip()
                value = match.group(3).strip()
                
                current_param = {
                    'code': code,
                    'parameter': param_name,
                    'value': value,
                    'continuation_lines': []
                }
            
            elif param_pattern3.match(line):
                # Pattern 3: code exists but no clear value separator
                match3 = param_pattern3.match(line)
                
                # Save previous parameter if exists
                if current_param:
                    current_param['continuation_lines'] = continuation_lines
                    parameters.append(current_param)
                    continuation_lines = []
                
                # This might be a parameter name only, value might follow
                code = match3.group(1)
                content = match3.group(2).strip()
                
                current_param = {
                    'code': code,
                    'parameter': content,
                    'value': '',  # No clear value yet
                    'continuation_lines': []
                }
            
            elif current_param:
                # Line without code - treat as continuation of previous parameter
                # Skip common headers and footers
                if not any(skip in line.lower() for skip in 
                          ['easergy studio', 'settings file', 'page:', 'micom']):
                    continuation_lines.append(line)
        
        # Don't forget last parameter
        if current_param:
            current_param['continuation_lines'] = continuation_lines
            parameters.append(current_param)
        
        return parameters
    
    def validate_extraction(self, parameters: List[Dict[str, Any]], 
                          ct_vt_data: Dict[str, List], 
                          protection_functions: List[Dict]) -> Dict[str, Any]:
        """
        Validate extraction completeness
        
        Returns:
            Dict with validation metrics and warnings
        """
        validation = {
            'total_parameters': len(parameters),
            'ct_count': len(ct_vt_data.get('current_transformers', [])),
            'vt_count': len(ct_vt_data.get('voltage_transformers', [])),
            'protection_functions': len(protection_functions),
            'enabled_functions': len([f for f in protection_functions if f.get('is_enabled')]),
            'completeness_score': 0.0,
            'warnings': []
        }
        
        # Check for expected sections
        codes_found = {p['code'][:2] for p in parameters}
        
        expected_sections = {
            '01': 'Configuration/General',
            '02': 'Protection Functions',
            '01': 'CT/VT Ratios',
            '01': 'Outputs/LEDs'
        }
        
        # Calculate completeness
        if validation['total_parameters'] > 0:
            validation['completeness_score'] = min(100.0, 
                (validation['total_parameters'] / 400) * 100)
        
        # Add warnings
        if validation['ct_count'] == 0 and validation['vt_count'] == 0:
            validation['warnings'].append('No CT or VT data extracted')
        
        if validation['enabled_functions'] == 0:
            validation['warnings'].append('No enabled protection functions found')
        
        if validation['total_parameters'] < 300:
            validation['warnings'].append(
                f'Low parameter count ({validation["total_parameters"]}) - expected ~400-450'
            )
        
        return validation
    
    def extract_all(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all data from PDF"""
        text = self.extract_text(pdf_path)
        
        # Extract structured data
        ct_vt_data = self.extract_ct_vt_data(text)
        protection_functions = self.extract_protection_functions(text)
        all_parameters = self.extract_all_parameters(text)
        
        # Validate extraction
        validation = self.validate_extraction(all_parameters, ct_vt_data, protection_functions)
        
        return {
            'manufacturer': self.detect_manufacturer(pdf_path),
            'model_info': self.extract_model_info(text),
            'ct_vt_data': ct_vt_data,
            'protection_functions': protection_functions,
            'all_parameters': all_parameters,
            'validation': validation,
            'raw_text': text
        }
