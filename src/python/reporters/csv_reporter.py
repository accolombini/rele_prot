"""
Exportador de relatórios em formato CSV
"""
import pandas as pd
from pathlib import Path
from typing import Optional
from .base_reporter import BaseReporter


class CSVReporter(BaseReporter):
    """Gera relatórios em formato CSV com metadados no cabeçalho"""
    
    def export(
        self,
        df: pd.DataFrame,
        report_code: str,
        report_name: str,
        report_title: str,
        include_header: bool = True
    ) -> Path:
        """
        Exporta DataFrame para CSV com cabeçalho de metadados
        
        Args:
            df: DataFrame com os dados
            report_code: Código do relatório (ex: REL01)
            report_name: Nome descritivo (ex: fabricantes_reles)
            report_title: Título completo do relatório
            include_header: Se True, inclui cabeçalho com metadados
        
        Returns:
            Path do arquivo gerado
        """
        self.validate_dataframe(df)
        
        output_path = self.get_output_path(report_code, report_name, 'csv')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if include_header:
                # Cabeçalho com metadados
                footer = self.format_footer_text(report_title)
                f.write(f"# {self.HEADER_TITLE}\n")
                f.write(f"# {report_title}\n")
                f.write(f"# {footer['left']}\n")
                f.write("#\n")
            
            # Dados
            df.to_csv(f, index=False, encoding='utf-8')
        
        return output_path
    
    def export_multiple_sections(
        self,
        sections: dict,
        report_code: str,
        report_name: str,
        report_title: str
    ) -> Path:
        """
        Exporta múltiplas seções em um único CSV
        
        Args:
            sections: Dict onde chave=nome_secao, valor=DataFrame
            report_code: Código do relatório
            report_name: Nome descritivo
            report_title: Título completo
        
        Returns:
            Path do arquivo gerado
        """
        output_path = self.get_output_path(report_code, report_name, 'csv')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Cabeçalho
            footer = self.format_footer_text(report_title)
            f.write(f"# {self.HEADER_TITLE}\n")
            f.write(f"# {report_title}\n")
            f.write(f"# {footer['left']}\n")
            f.write("#\n")
            
            # Seções
            for section_name, df in sections.items():
                f.write(f"\n# === {section_name.upper()} ===\n")
                df.to_csv(f, index=False, encoding='utf-8')
                f.write("\n")
        
        return output_path
