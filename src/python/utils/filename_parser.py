"""
Filename Parser Utility
Extrai informações estruturadas dos nomes de arquivos de relés
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime


class FilenameParser:
    """
    Parser genérico para nomes de arquivos de relés de proteção
    
    Suporta múltiplos padrões:
    - SEPAM (.S40): 00-MF-12_2016-03-31.S40
    - PDF GE/Schneider: P###_##-XX-####_YYYY-MM-DD.pdf
    """
    
    # Padrão SEPAM: 00-MF-12_2016-03-31.S40
    SEPAM_PATTERN = r'^(\d+)-([A-Z]{2,})-(\w+)_(\d{4}-\d{2}-\d{2})\.S40$'
    
    # Padrão PDF com data: P###_##-XX-####_YYYY-MM-DD.pdf ou P_### ##-XX-####_YYYY-MM-DD.pdf
    PDF_WITH_DATE_PATTERN = r'^P_?(\d{3})[\s_](\d+)-([A-Z]{2})-(\w+)_(\d{4}-\d{2}-\d{2})\.pdf$'
    
    # Padrão PDF sem data: P### ##-XX-####.pdf
    PDF_NO_DATE_PATTERN = r'^P_?(\d{3})[\s_](\d+)-([A-Z]{2})-(\w+)\.pdf$'
    
    def __init__(self):
        self.tipo_painel_map = {
            'MF': 'Main Feeder (Alimentador Principal)',
            'MK': 'Main Coupling (Acoplamento Principal)',
            'MP': 'Main Protection (Proteção Principal)',
            'TR': 'Transformer (Transformador)',
            'GN': 'Generator (Gerador)',
            'MT': 'Motor',
            'BU': 'Bus (Barramento)',
            'PT': 'Potential Transformer (TP)',
            'CT': 'Current Transformer (TC)'
        }
    
    def parse_sepam_filename(self, filename: str) -> Dict[str, Any]:
        """
        Parse SEPAM .S40 filename
        
        Formato: 00-MF-12_2016-03-31.S40
        - 00: Código da subestação
        - MF: Tipo de painel
        - 12: Identificador das barras
        - 2016-03-31: Data de configuração
        """
        match = re.match(self.SEPAM_PATTERN, filename, re.IGNORECASE)
        
        if not match:
            return {'valid': False, 'error': 'Filename does not match SEPAM pattern'}
        
        subestacao, tipo_painel_code, barras, data_str = match.groups()
        
        try:
            data_config = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            data_config = None
        
        return {
            'valid': True,
            'tipo_arquivo': 'SEPAM_S40',
            'subestacao_codigo': subestacao,
            'tipo_painel_codigo': tipo_painel_code,
            'tipo_painel_descricao': self.tipo_painel_map.get(tipo_painel_code, tipo_painel_code),
            'barras_identificador': barras,
            'data_configuracao': data_config,
            'fabricante': 'SCHNEIDER ELECTRIC'
        }
    
    def parse_pdf_filename(self, filename: str) -> Dict[str, Any]:
        """
        Parse PDF filename (GE ou Schneider)
        
        Formatos suportados:
        1. Com data: P_122 52-MF-03B1_2021-03-17.pdf
        2. Sem data: P922 52-MF-01BC.pdf
        
        Estrutura:
        - P###: Modelo do relé (P122, P143, P220, P241, P922)
        - ##: Código ANSI ou função
        - XX: Tipo de painel
        - ####: Identificador das barras
        - YYYY-MM-DD: Data de configuração (opcional)
        """
        # Tentar padrão com data primeiro
        match = re.match(self.PDF_WITH_DATE_PATTERN, filename, re.IGNORECASE)
        has_date = True
        
        if not match:
            # Tentar padrão sem data
            match = re.match(self.PDF_NO_DATE_PATTERN, filename, re.IGNORECASE)
            has_date = False
        
        if not match:
            return {'valid': False, 'error': f'Filename does not match PDF patterns: {filename}'}
        
        if has_date:
            modelo, ansi_code, tipo_painel_code, barras, data_str = match.groups()
            try:
                data_config = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                data_config = None
        else:
            modelo, ansi_code, tipo_painel_code, barras = match.groups()
            data_config = None
        
        # Determinar fabricante baseado no modelo
        fabricante = self._detect_manufacturer_from_model(modelo)
        
        return {
            'valid': True,
            'tipo_arquivo': 'PDF',
            'modelo_rele': f'P{modelo}',
            'ansi_codigo': ansi_code,
            'tipo_painel_codigo': tipo_painel_code,
            'tipo_painel_descricao': self.tipo_painel_map.get(tipo_painel_code, tipo_painel_code),
            'barras_identificador': barras,
            'data_configuracao': data_config,
            'fabricante': fabricante
        }
    
    def _detect_manufacturer_from_model(self, modelo: str) -> str:
        """
        Detecta fabricante baseado no modelo do relé
        
        GE (MiCOM): P14x, P24x, P44x, P54x series
        Schneider: P1xx, P2xx, P9xx (exceto P14x, P24x)
        """
        modelo_num = int(modelo)
        
        # GE MiCOM patterns
        if modelo_num in [143, 241, 242, 243, 441, 442, 443, 542, 543, 544, 545]:
            return 'GENERAL ELECTRIC'
        
        # Schneider Easergy patterns
        if modelo_num in [122, 123, 125, 127, 220, 221, 222, 223, 225, 922, 923]:
            return 'SCHNEIDER ELECTRIC'
        
        # Default: tentar detectar por faixa
        if 140 <= modelo_num < 150 or 240 <= modelo_num < 250:
            return 'GENERAL ELECTRIC'
        else:
            return 'SCHNEIDER ELECTRIC'
    
    def parse(self, filename: str) -> Dict[str, Any]:
        """
        Parse automático baseado na extensão do arquivo
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.s40'):
            return self.parse_sepam_filename(filename)
        elif filename_lower.endswith('.pdf'):
            return self.parse_pdf_filename(filename)
        else:
            return {
                'valid': False,
                'error': f'Unsupported file extension: {filename}'
            }
