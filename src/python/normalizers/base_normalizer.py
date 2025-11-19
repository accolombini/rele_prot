"""
Base Normalizer
Classe base para todos os normalizadores
"""

import csv
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseNormalizer(ABC):
    """Classe base para normalização de dados"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.processed_count = 0
    
    def generate_id(self, prefix: str = '') -> str:
        """Gera ID único"""
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"
    
    def get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def safe_get(self, data: Dict, *keys, default=None) -> Any:
        """
        Acesso seguro a dicionários aninhados
        
        Example:
            safe_get(data, 'relay_data', 'modelo_rele', default='Unknown')
        """
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return default
            
            if result is None:
                return default
        
        return result
    
    def append_to_csv(self, filepath: Path, row: Dict[str, Any], headers: List[str]):
        """
        Append row to CSV file (creates if not exists)
        
        Args:
            filepath: Path to CSV file
            row: Dictionary with data
            headers: List of column headers
        """
        file_exists = filepath.exists()
        
        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=';', extrasaction='ignore')
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row)
    
    def log_info(self, message: str):
        """Log info message"""
        if self.logger:
            self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        if self.logger:
            self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message"""
        if self.logger:
            self.logger.error(message)
    
    @abstractmethod
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data - must be implemented by subclasses
        
        Args:
            data: Raw data dictionary
        
        Returns:
            Normalized data dictionary
        """
        pass
