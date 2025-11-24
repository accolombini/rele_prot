"""Gerador de relatórios analíticos do sistema de relés.

Este módulo implementa o sistema completo de geração de relatórios, conectando-se
ao banco de dados PostgreSQL e produzindo saídas em múltiplos formatos (CSV, Excel, PDF).

O sistema oferece 9 relatórios pré-definidos com análises específicas:
    REL01: Fabricantes de Relés
    REL02: Setpoints Críticos
    REL03: Tipos de Relés
    REL04: Relés por Fabricante
    REL05: Funções de Proteção
    REL06: Relatório Completo
    REL07: Relés por Subestação
    REL08: Análise de Tensão
    REL09: Parâmetros Críticos

Características:
    - Tradução automática de colunas para português
    - Abreviações inteligentes para headers longos
    - Formatação específica por tipo de relatório
    - Suporte a orientação landscape para relatórios largos
    - Validação de dados e tratamento de erros

Exemplo de uso:
    >>> from src.python.reporters.report_generator import ReportGenerator
    >>> generator = ReportGenerator()
    >>> generator.generate_report('REL01', formats=['csv', 'xlsx', 'pdf'])
    >>> generator.generate_all_reports(formats=['xlsx'])
"""
import psycopg2
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .csv_reporter import CSVReporter
from .excel_reporter import ExcelReporter
from .pdf_reporter import PDFReporter


class ReportGenerator:
    """Orquestrador de geração de relatórios analíticos do sistema.
    
    Gerencia conexão com banco de dados, tradução de colunas, aplicação de
    abreviações e delegação para reporters especializados (CSV, Excel, PDF).
    
    Attributes:
        db_config (Dict): Configuração de conexão PostgreSQL
        schema (str): Nome do schema no banco de dados
        output_base_path (Path): Diretório raiz para saída de relatórios
        csv_reporter (CSVReporter): Reporter para formato CSV
        excel_reporter (ExcelReporter): Reporter para formato Excel
        pdf_reporter (PDFReporter): Reporter para formato PDF
    """
    
    # Relatórios que devem ser SEMPRE em landscape (muitas colunas ou conteúdo longo)
    FORCE_LANDSCAPE = ['REL06', 'REL08', 'REL09']
    
    # Relatórios que usam abreviações especiais de Fabricante e Tensão
    REPORTS_WITH_SPECIAL_ABBREVIATIONS = ['REL02', 'REL03', 'REL04', 'REL05', 'REL06', 'REL07', 'REL08', 'REL09']
    
    # Abreviações especiais aplicadas APENAS em REL05-REL09
    SPECIAL_ABBREVIATIONS = {
        'Fabricante': 'Fab',
        'Fabricantes': 'Fab',
        'C.Tensão\nkV': 'V_kV'
    }
    
    # Dicionário de abreviações para headers longos (aplicado em TODOS os relatórios)
    HEADER_ABBREVIATIONS = {
        'Código ANSI': 'Cd.ANSI',
        'Nome da Função': 'Função',
        'Classe de Tensão (kV)': 'C.Tensão\nkV',
        'Total de Proteções': 'TotProt',
        'Total de Instalações': 'TotInst',
        'Total de Instâncias': 'TotInst',
        'Lista de Parâmetros Críticos': 'L_Par_Crit',
        'Código da Subestação': 'Cd.Subest',
        'Total de Modelos': 'TotMod',
        'Total de Relés': 'TotRelés',
        'Tipo de Relé': 'Tipo\nRelé',
        'ID Relé': 'ID\nRelé',
        'Tipo de Parâmetro': 'Tipo\nParam',
        'Nome da Função de Proteção': 'Função\nProteção',
        'Total de TCs': 'Tot\nTCs',
        'Total de TPs': 'Tot\nTPs',
        'Total de Parâmetros': 'Tot\nParams',
        'Proteções Habilitadas': 'Prot\nHabil',
        'Data de Configuração': 'Data\nConfig',
        'Versão de Software': 'Ver.\nSW',
        'Versão de Firmware': 'Ver.\nFW',
        'TP Definido': 'TP\nDef',
        'TP Habilitado': 'TP\nHabil',
        'Fonte de Tensão': 'Fonte\nTensão',
        'Confiança da Tensão': 'Conf.\nTensão',
        'Habilitadas': 'EN',
        'Desabilitadas': 'DES',
        'Código da Subestação': 'SE',
        'Proteções Habilitadas': 'Prot\nHabil',
        'Data de Configuração': 'Data\nConfig',
        'Versão de Software': 'Ver.\nSW',
        'Versão de Firmware': 'Ver.\nFW'
    }
    
    # Mapeamento de tradução de colunas para headers formatados
    COLUMN_TRANSLATIONS = {
        # Identificadores
        'id_rele': 'ID Relé',
        'relay_id': 'ID Relé',
        'barra': 'Barra',
        'bay_identifier': 'Barra',
        
        # Fabricante e Modelo
        'fabricante': 'Fabricante',
        'manufacturer_name': 'Fabricante',
        'modelo': 'Modelo',
        'model_name': 'Modelo',
        
        # Códigos ANSI e Funções
        'codigo_ansi': 'Código ANSI',
        'ansi_code': 'Código ANSI',
        'nome_funcao': 'Nome da Função',
        'ansi_name': 'Nome da Função',
        
        # Status
        'habilitado': 'Habilitado',
        'is_enabled': 'Habilitado',
        
        # Parâmetros
        'parametro': 'Parâmetro',
        'parameter_name': 'Parâmetro',
        'valor': 'Valor',
        'parameter_value': 'Valor',
        'unidade': 'Unidade',
        'parameter_unit': 'Unidade',
        'tipo_parametro': 'Tipo de Parâmetro',
        'parameter_type': 'Tipo de Parâmetro',
        
        # Totalizadores
        'total_reles': 'Total de Relés',
        'total_relays': 'Total de Relés',
        'total_models': 'Total de Modelos',
        'total_instancias': 'Total de Instâncias',
        'total_instances': 'Total de Instâncias',
        'total_protecoes': 'Total de Proteções',
        'total_protections': 'Total de Proteções',
        'total_parametros': 'Total de Parâmetros',
        'total_params': 'Total de Parâmetros',
        'parametros_criticos': 'Parâmetros Críticos',
        'critical_params': 'Parâmetros Críticos',
        
        # Listas e agregações
        'fabricantes': 'Fabricantes',
        'manufacturers': 'Fabricantes',
        'habilitadas': 'Habilitadas',
        'enabled_count': 'Habilitadas',
        'desabilitadas': 'Desabilitadas',
        'disabled_count': 'Desabilitadas',
        'lista_parametros_criticos': 'Lista de Parâmetros Críticos',
        'critical_params_list': 'Lista de Parâmetros Críticos',
        
        # Tipos e Classes
        'tipo_rele': 'Tipo de Relé',
        'relay_type': 'Tipo de Relé',
        'classe_tensao_kv': 'Classe de Tensão (kV)',
        'voltage_class_kv': 'Classe de Tensão (kV)',
        
        # Subestação
        'codigo_subestacao': 'Código da Subestação',
        'substation_code': 'Código da Subestação',
        
        # Dados completos
        'total_cts': 'Total de TCs',
        'total_vts': 'Total de TPs',
        'total_parameters': 'Total de Parâmetros',
        'enabled_protections': 'Proteções Habilitadas',
        'config_date': 'Data de Configuração',
        'software_version': 'Versão de Software',
        'firmware_version': 'Versão de Firmware',
        'vt_defined': 'TP Definido',
        'vt_enabled': 'TP Habilitado',
        'voltage_source': 'Fonte de Tensão',
        'voltage_confidence': 'Confiança da Tensão',
        
        # Análise de Tensão
        'relays_with_vt_defined': 'Relés com TP Definido',
        'relays_with_vt_enabled': 'Relés com TP Habilitado',
        'voltage_sources': 'Fontes de Tensão',
        'confidence_levels': 'Níveis de Confiança'
    }
    
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
            'view': 'vw_critical_parameters_consolidated',
            'description': 'Consolidação de parâmetros críticos por relé'
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
    
    def translate_columns(self, df: pd.DataFrame, report_code: str = None) -> pd.DataFrame:
        """
        Traduz os nomes das colunas do DataFrame usando o mapeamento
        e aplica abreviações para otimizar espaço nos relatórios
        
        Args:
            df: DataFrame com colunas em inglês/snake_case
            report_code: Código do relatório (REL01-REL09) para abreviações específicas
            
        Returns:
            DataFrame com colunas traduzidas, formatadas e abreviadas
        """
        column_mapping = {}
        for col in df.columns:
            # Se existe tradução, usa; senão mantém original formatado
            if col in self.COLUMN_TRANSLATIONS:
                translated = self.COLUMN_TRANSLATIONS[col]
            else:
                # Fallback: capitalizar primeira letra de cada palavra
                translated = col.replace('_', ' ').title()
            
            # Aplicar abreviações gerais (todos os relatórios)
            if translated in self.HEADER_ABBREVIATIONS:
                abbreviated = self.HEADER_ABBREVIATIONS[translated]
            else:
                abbreviated = translated
            
            # Aplicar abreviações especiais APENAS para relatórios específicos (sobrescreve abreviações gerais)
            if report_code in self.REPORTS_WITH_SPECIAL_ABBREVIATIONS and abbreviated in self.SPECIAL_ABBREVIATIONS:
                column_mapping[col] = self.SPECIAL_ABBREVIATIONS[abbreviated]
            else:
                column_mapping[col] = abbreviated
        
        return df.rename(columns=column_mapping)
    
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
        
        # 🔧 TRADUZIR COLUNAS ANTES DE EXPORTAR (com report_code para abreviações seletivas)
        df = self.translate_columns(df, report_code=report_code)
        
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
            # CORREÇÃO: Forçar landscape para relatórios críticos (REL06, REL08)
            if report_code in self.FORCE_LANDSCAPE:
                orientation = 'landscape'
            elif len(df.columns) > 8:
                orientation = 'landscape'
            else:
                orientation = 'portrait'
            
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
        
        # 🔧 TRADUZIR COLUNAS ANTES DE EXPORTAR
        df = self.translate_columns(df)
        
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
