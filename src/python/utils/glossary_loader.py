"""
Glossary Loader utility
Loads and manages glossary mappings for protection functions
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


class GlossaryLoader:
    """Loads and provides access to glossary mappings"""
    
    def __init__(self, glossary_dir: str):
        self.glossary_dir = Path(glossary_dir)
        self.mappings: Dict[str, Any] = {}
        self.relay_configs: Dict[str, Any] = {}
        self._load_glossaries()
    
    def _load_glossaries(self):
        """Load all glossary files"""
        # Load glossary mapping
        glossary_file = self.glossary_dir / "glossary_mapping.json"
        if glossary_file.exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                self.mappings = json.load(f)
        
        # Load relay models config
        relay_config_file = self.glossary_dir / "relay_models_config.json"
        if relay_config_file.exists():
            with open(relay_config_file, 'r', encoding='utf-8') as f:
                self.relay_configs = json.load(f)
    
    def get_function_name(self, code: str) -> Optional[str]:
        """Get function name from code"""
        return self.mappings.get(code, {}).get('name')
    
    def get_function_description(self, code: str) -> Optional[str]:
        """Get function description from code"""
        return self.mappings.get(code, {}).get('description')
    
    def get_ansi_code(self, code: str) -> Optional[str]:
        """Get ANSI code from internal code"""
        return self.mappings.get(code, {}).get('ansi_code')
    
    def get_parameter_unit(self, code: str) -> Optional[str]:
        """Get parameter unit from code"""
        return self.mappings.get(code, {}).get('unit')
    
    def get_relay_config(self, model: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific relay model"""
        return self.relay_configs.get(model)
    
    def get_all_ansi_codes(self) -> Dict[str, str]:
        """Get mapping of all codes to ANSI codes"""
        ansi_map = {}
        for code, data in self.mappings.items():
            if 'ansi_code' in data:
                ansi_map[code] = data['ansi_code']
        return ansi_map
    
    def is_code_mapped(self, code: str) -> bool:
        """Check if code exists in mappings"""
        return code in self.mappings
    
    def search_by_name(self, search_term: str) -> Dict[str, Any]:
        """Search mappings by name"""
        results = {}
        search_lower = search_term.lower()
        
        for code, data in self.mappings.items():
            if 'name' in data and search_lower in data['name'].lower():
                results[code] = data
        
        return results
    
    def get_codes_by_ansi(self, ansi_code: str) -> list:
        """Get all internal codes that map to an ANSI code"""
        codes = []
        for code, data in self.mappings.items():
            if data.get('ansi_code') == ansi_code:
                codes.append(code)
        return codes
    
    def get_relay_type(self, model: str) -> str:
        """
        Get relay type (protection category) from model name
        Returns 'Tipo Desconhecido' if model not found
        """
        # Normalize model name
        # Remove: underscore, spaces, "SEPAM", "MICON", etc
        normalized = model.replace('_', '').replace(' ', '').upper()
        normalized = normalized.replace('SEPAM', '').replace('MICON', '').strip()
        
        # Try direct lookup
        relay_types = self.relay_configs.get('relay_types', {})
        if normalized in relay_types:
            return relay_types[normalized]
        
        # Try prefix match (P122_52 -> P122, S40_V1 -> S40)
        for known_model, relay_type in relay_types.items():
            if normalized.startswith(known_model):
                return relay_type
        
        # Try extracting just the alphanumeric code (SEPAM S40 -> S40)
        match = re.search(r'([A-Z]\d+)', normalized)
        if match:
            code = match.group(1)
            if code in relay_types:
                return relay_types[code]
        
        # Model not found - return unknown
        return 'Tipo Desconhecido'
    
    def get_all_relay_types(self) -> Dict[str, str]:
        """Get all relay model to type mappings"""
        return self.relay_configs.get('relay_types', {})
