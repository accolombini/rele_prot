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
    
    def extract_all(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all data from PDF"""
        text = self.extract_text(pdf_path)
        
        return {
            'manufacturer': self.detect_manufacturer(pdf_path),
            'model_info': self.extract_model_info(text),
            'ct_vt_data': self.extract_ct_vt_data(text),
            'protection_functions': self.extract_protection_functions(text),
            'raw_text': text
        }
