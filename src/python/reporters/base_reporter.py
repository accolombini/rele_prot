"""
Classe base para todos os relatórios
Define estrutura comum de cabeçalho, rodapé e metadados
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd


class BaseReporter:
    """Classe base com configurações padrão para relatórios"""
    
    # Cabeçalho padrão
    HEADER_SYMBOL = "■"
    HEADER_TITLE = "ENGENHARIA DE PROTEÇÃO PETROBRAS"
    
    # Cores padrão (RGB)
    PRIMARY_COLOR = (0, 51, 102)  # Azul Petrobras
    SECONDARY_COLOR = (255, 184, 28)  # Amarelo Petrobras
    TEXT_COLOR = (33, 33, 33)
    
    def __init__(self, output_base_path: Optional[Path] = None):
        """
        Inicializa o reporter base
        
        Args:
            output_base_path: Caminho base para outputs (default: projeto/outputs/relatorios/)
        """
        if output_base_path is None:
            # Resolve para: src/python/reporters/ -> ... -> root/outputs/relatorios/
            project_root = Path(__file__).parent.parent.parent.parent
            output_base_path = project_root / 'outputs' / 'relatorios'
        
        self.output_base = Path(output_base_path)
        self.csv_dir = self.output_base / 'csv'
        self.xlsx_dir = self.output_base / 'xlsx'
        self.pdf_dir = self.output_base / 'pdf'
        
        # Criar diretórios se não existirem
        for directory in [self.csv_dir, self.xlsx_dir, self.pdf_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_timestamp(self) -> str:
        """Gera timestamp no formato YYYYMMDD_HHMMSS"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_filename(self, report_code: str, report_name: str, extension: str) -> str:
        """
        Gera nome de arquivo padronizado
        
        Args:
            report_code: Código do relatório (ex: REL01)
            report_name: Nome descritivo (ex: fabricantes_reles)
            extension: Extensão sem ponto (csv, xlsx, pdf)
        
        Returns:
            Nome do arquivo (ex: REL01_fabricantes_reles_20251120_155004.csv)
        """
        timestamp = self.generate_timestamp()
        return f"{report_code}_{report_name}_{timestamp}.{extension}"
    
    def get_output_path(self, report_code: str, report_name: str, format_type: str) -> Path:
        """
        Retorna caminho completo para salvar o relatório
        
        Args:
            report_code: Código do relatório
            report_name: Nome descritivo
            format_type: Tipo de formato (csv, xlsx, pdf)
        
        Returns:
            Path completo do arquivo
        """
        filename = self.generate_filename(report_code, report_name, format_type)
        
        if format_type == 'csv':
            return self.csv_dir / filename
        elif format_type == 'xlsx':
            return self.xlsx_dir / filename
        elif format_type == 'pdf':
            return self.pdf_dir / filename
        else:
            raise ValueError(f"Formato não suportado: {format_type}")
    
    def format_footer_text(self, report_title: str, page_num: int = 1) -> dict:
        """
        Formata texto do rodapé
        
        Args:
            report_title: Título do relatório
            page_num: Número da página
        
        Returns:
            Dict com left, center, right
        """
        now = datetime.now()
        return {
            'left': f"Gerado em: {now.strftime('%d/%m/%Y %H:%M')}",
            'center': report_title,
            'right': f"Pag. {page_num}"
        }
    
    def validate_dataframe(self, df: pd.DataFrame, required_columns: list = None) -> bool:
        """
        Valida se o DataFrame tem os dados necessários
        
        Args:
            df: DataFrame a validar
            required_columns: Lista de colunas obrigatórias
        
        Returns:
            True se válido
        
        Raises:
            ValueError: Se validação falhar
        """
        if df is None or df.empty:
            raise ValueError("DataFrame vazio ou nulo")
        
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                raise ValueError(f"Colunas faltando: {missing}")
        
        return True
