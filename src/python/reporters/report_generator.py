"""
Gerador de Relatórios - Conecta ao PostgreSQL e gera os 9 relatórios do sistema
"""
import psycopg2
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .csv_reporter import CSVReporter
from .excel_reporter import ExcelReporter
from .pdf_reporter import PDFReporter


class ReportGenerator:
    """Orquestrador principal de geração de relatórios"""
    
    # Definição dos 9 relatórios
    REPORTS = {
        'REL01': {
            'name': 'fabricantes_reles',
            'title': 'Relatório de Fabricantes de Relés',
            'view': 'vw_manufacturers_summary',
            'description': 'Lista fabricantes com total de relés e modelos'
        },
        'REL02': {
            'name': 'setpoints_criticos',
            'title': 'Relatório de Setpoints Críticos',
            'view': 'vw_critical_setpoints',
            'description': 'Proteções principais e seus parâmetros críticos'
        },
        'REL03': {
            'name': 'tipos_reles',
            'title': 'Relatório de Tipos de Relés',
            'view': 'vw_relay_types_summary',
            'description': 'Distribuição de relés por tipo'
        },
        'REL04': {
            'name': 'reles_por_fabricante',
            'title': 'Relatório de Relés por Fabricante',
            'view': 'vw_relays_by_manufacturer',
            'description': 'Relés detalhados agrupados por fabricante'
        },
        'REL05': {
            'name': 'funcoes_protecao',
            'title': 'Relatório de Funções de Proteção',
            'view': 'vw_protection_functions_summary',
            'description': 'Funções de proteção ANSI e seus relés'
        },
        'REL06': {
            'name': 'reles_completo',
            'title': 'Relatório Completo de Relés',
            'view': 'vw_relays_complete',
            'description': 'Visão completa de todos os relés com estatísticas'
        },
        'REL07': {
            'name': 'reles_por_subestacao',
            'title': 'Relatório de Relés por Subestação',
            'view': 'vw_relays_by_substation',
            'description': 'Relés agrupados por barra e subestação'
        },
        'REL08': {
            'name': 'analise_tensao',
            'title': 'Relatório de Análise de Tensão',
            'view': 'vw_relays_complete',
            'description': 'Análise de classes de tensão e VTs',
            'filter': "voltage_class_kv IS NOT NULL"
        },
        'REL09': {
            'name': 'parametros_criticos',
            'title': 'Relatório de Parâmetros Críticos Consolidado',
            'view': 'vw_relays_complete',
            'description': 'Consolidação de parâmetros críticos por relé',
            'filter': "total_parameters > 0"
        }
    }
    
    def __init__(
        self,
        db_host: str = 'localhost',
        db_port: int = 5432,
        db_name: str = 'protecai_db',
        db_user: str = 'protecai',
        db_password: str = 'protecai',
        db_schema: str = 'protec_ai',
        output_base_path: Optional[Path] = None
    ):
        """
        Inicializa o gerador de relatórios
        
        Args:
            db_host: Host do PostgreSQL
            db_port: Porta do PostgreSQL
            db_name: Nome do banco
            db_user: Usuário
            db_password: Senha
            db_schema: Schema (default: protec_ai)
            output_base_path: Caminho base para outputs
        """
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        self.schema = db_schema
        
        # Instanciar reporters
        self.csv_reporter = CSVReporter(output_base_path)
        self.excel_reporter = ExcelReporter(output_base_path)
        self.pdf_reporter = PDFReporter(output_base_path)
    
    def get_connection(self):
        """Cria conexão com o banco de dados"""
        return psycopg2.connect(**self.db_config)
    
    def fetch_data(self, view_name: str, filter_clause: Optional[str] = None) -> pd.DataFrame:
        """
        Busca dados de uma view
        
        Args:
            view_name: Nome da view
            filter_clause: Cláusula WHERE opcional
        
        Returns:
            DataFrame com os dados
        """
        query = f"SELECT * FROM {self.schema}.{view_name}"
        if filter_clause:
            query += f" WHERE {filter_clause}"
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        
        return df
    
    def generate_report(
        self,
        report_code: str,
        formats: List[str] = ['csv', 'xlsx', 'pdf']
    ) -> Dict[str, Path]:
        """
        Gera um relatório específico nos formatos solicitados
        
        Args:
            report_code: Código do relatório (REL01, REL02, etc)
            formats: Lista de formatos ('csv', 'xlsx', 'pdf')
        
        Returns:
            Dict com {formato: path_do_arquivo}
        """
        if report_code not in self.REPORTS:
            raise ValueError(f"Relatório não encontrado: {report_code}")
        
        report_config = self.REPORTS[report_code]
        
        # Buscar dados
        print(f"Gerando {report_code}: {report_config['title']}")
        df = self.fetch_data(
            report_config['view'],
            report_config.get('filter')
        )
        
        if df.empty:
            print(f"  ⚠️  AVISO: Nenhum dado encontrado para {report_code}")
            return {}
        
        print(f"  📊 {len(df)} registros encontrados")
        
        # Gerar nos formatos solicitados
        generated_files = {}
        
        if 'csv' in formats:
            csv_path = self.csv_reporter.export(
                df,
                report_code,
                report_config['name'],
                report_config['title']
            )
            generated_files['csv'] = csv_path
            print(f"  ✅ CSV: {csv_path.name}")
        
        if 'xlsx' in formats:
            xlsx_path = self.excel_reporter.export(
                df,
                report_code,
                report_config['name'],
                report_config['title'],
                sheet_name=report_config['name'].replace('_', ' ').title()
            )
            generated_files['xlsx'] = xlsx_path
            print(f"  ✅ Excel: {xlsx_path.name}")
        
        if 'pdf' in formats:
            # Determinar orientação baseado no número de colunas
            orientation = 'landscape' if len(df.columns) > 6 else 'portrait'
            
            pdf_path = self.pdf_reporter.export(
                df,
                report_code,
                report_config['name'],
                report_config['title'],
                orientation=orientation
            )
            generated_files['pdf'] = pdf_path
            print(f"  ✅ PDF: {pdf_path.name}")
        
        return generated_files
    
    def generate_all_reports(
        self,
        formats: List[str] = ['csv', 'xlsx', 'pdf']
    ) -> Dict[str, Dict[str, Path]]:
        """
        Gera todos os 9 relatórios
        
        Args:
            formats: Lista de formatos para cada relatório
        
        Returns:
            Dict com {report_code: {formato: path}}
        """
        print("=" * 80)
        print("GERAÇÃO DE RELATÓRIOS - ProtecAI")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Formatos: {', '.join(formats)}")
        print(f"Total de relatórios: {len(self.REPORTS)}")
        print("=" * 80)
        print()
        
        all_generated = {}
        
        for report_code in sorted(self.REPORTS.keys()):
            try:
                generated = self.generate_report(report_code, formats)
                all_generated[report_code] = generated
                print()
            except Exception as e:
                print(f"  ❌ ERRO ao gerar {report_code}: {str(e)}")
                print()
                continue
        
        print("=" * 80)
        print(f"CONCLUÍDO: {len(all_generated)}/{len(self.REPORTS)} relatórios gerados")
        print("=" * 80)
        
        return all_generated
    
    def generate_custom_report(
        self,
        query: str,
        report_code: str,
        report_name: str,
        report_title: str,
        formats: List[str] = ['csv', 'xlsx', 'pdf']
    ) -> Dict[str, Path]:
        """
        Gera relatório customizado a partir de query SQL
        
        Args:
            query: Query SQL completa
            report_code: Código do relatório (ex: REL10)
            report_name: Nome descritivo
            report_title: Título completo
            formats: Formatos desejados
        
        Returns:
            Dict com {formato: path_do_arquivo}
        """
        print(f"Gerando relatório customizado: {report_code}")
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print(f"  ⚠️  AVISO: Nenhum dado retornado pela query")
            return {}
        
        print(f"  📊 {len(df)} registros encontrados")
        
        generated_files = {}
        
        if 'csv' in formats:
            csv_path = self.csv_reporter.export(df, report_code, report_name, report_title)
            generated_files['csv'] = csv_path
            print(f"  ✅ CSV: {csv_path.name}")
        
        if 'xlsx' in formats:
            xlsx_path = self.excel_reporter.export(df, report_code, report_name, report_title)
            generated_files['xlsx'] = xlsx_path
            print(f"  ✅ Excel: {xlsx_path.name}")
        
        if 'pdf' in formats:
            orientation = 'landscape' if len(df.columns) > 6 else 'portrait'
            pdf_path = self.pdf_reporter.export(df, report_code, report_name, report_title, orientation)
            generated_files['pdf'] = pdf_path
            print(f"  ✅ PDF: {pdf_path.name}")
        
        return generated_files
    
    def list_available_reports(self):
        """Lista todos os relatórios disponíveis"""
        print("=" * 80)
        print("RELATÓRIOS DISPONÍVEIS")
        print("=" * 80)
        
        for code, config in sorted(self.REPORTS.items()):
            print(f"\n{code}: {config['title']}")
            print(f"  View: {config['view']}")
            print(f"  Descrição: {config['description']}")
            if 'filter' in config:
                print(f"  Filtro: {config['filter']}")
        
        print("\n" + "=" * 80)
