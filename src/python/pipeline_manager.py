#!/usr/bin/env python3
"""
Pipeline Manager - CLI Integrado para todo o fluxo ProtecAI
Executa: Extração → Normalização → Carga DB → Relatórios
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from main import main as run_extraction
from database.database_loader import DatabaseLoader
from reporters.report_generator import ReportGenerator


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineManager:
    """Gerenciador do pipeline completo"""
    
    def __init__(
        self,
        db_host: str = 'localhost',
        db_port: int = 5432,
        db_name: str = 'protecai_db',
        db_user: str = 'protecai',
        db_password: str = 'protecai',
        db_schema: str = 'protec_ai'
    ):
        self.db_config = {
            'db_host': db_host,
            'db_port': db_port,
            'db_name': db_name,
            'db_user': db_user,
            'db_password': db_password,
            'db_schema': db_schema
        }
        
        self.loader = DatabaseLoader(**self.db_config)
        self.reporter = ReportGenerator(**self.db_config)
    
    def run_full_pipeline(
        self,
        input_path: Optional[Path] = None,
        skip_extraction: bool = False,
        skip_database: bool = False,
        report_codes: Optional[List[str]] = None,
        report_formats: List[str] = ['csv', 'xlsx', 'pdf']
    ):
        """
        Executa pipeline completo
        
        Args:
            input_path: Pasta com arquivos de entrada (se None, usa inputs/)
            skip_extraction: Se True, pula extração (usa CSVs existentes)
            skip_database: Se True, pula carga no banco
            report_codes: Lista de relatórios (None = todos)
            report_formats: Formatos de saída dos relatórios
        """
        logger.info("=" * 80)
        logger.info("PIPELINE PROTECAI - EXECUÇÃO COMPLETA")
        logger.info("=" * 80)
        
        # FASE 1 e 2: Extração e Normalização
        if not skip_extraction:
            logger.info("\n[FASE 1 e 2] Extração e Normalização")
            logger.info("-" * 80)
            
            try:
                # Chamar main.py (que já faz extração + normalização)
                logger.info("Executando extração e normalização...")
                # Note: main.py precisa ser refatorado para ser importável
                # Por ora, vamos assumir que CSVs normalizados já existem
                logger.warning("⚠️  Execute manualmente: python src/python/main.py")
                logger.info("Continuando com CSVs normalizados existentes...")
            except Exception as e:
                logger.error(f"❌ Erro na extração: {str(e)}")
                raise
        else:
            logger.info("\n[FASE 1 e 2] PULADO (usando CSVs existentes)")
        
        # FASE 4B: Carga no Banco
        if not skip_database:
            logger.info("\n[FASE 4B] Carga no Banco de Dados")
            logger.info("-" * 80)
            
            try:
                stats = self.loader.load_all(force=False)
                logger.info(f"✅ {stats['relays']} relés carregados no banco")
            except Exception as e:
                logger.error(f"❌ Erro na carga: {str(e)}")
                raise
        else:
            logger.info("\n[FASE 4B] PULADO (sem carga no banco)")
        
        # FASE 4A: Geração de Relatórios
        logger.info("\n[FASE 4A] Geração de Relatórios")
        logger.info("-" * 80)
        
        try:
            if report_codes:
                # Relatórios específicos
                for code in report_codes:
                    self.reporter.generate_report(code, formats=report_formats)
            else:
                # Todos os relatórios
                self.reporter.generate_all_reports(formats=report_formats)
            
            logger.info("✅ Relatórios gerados")
        except Exception as e:
            logger.error(f"❌ Erro na geração de relatórios: {str(e)}")
            raise
        
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE CONCLUÍDO COM SUCESSO")
        logger.info("=" * 80)
    
    def interactive_report_selector(self):
        """Menu interativo para selecionar relatórios"""
        print("\n" + "=" * 80)
        print("SELETOR INTERATIVO DE RELATÓRIOS")
        print("=" * 80)
        
        self.reporter.list_available_reports()
        
        print("\nOpções:")
        print("  1. Gerar TODOS os relatórios")
        print("  2. Gerar relatórios específicos")
        print("  3. Sair")
        
        choice = input("\nEscolha (1-3): ").strip()
        
        if choice == '1':
            formats = self._select_formats()
            self.reporter.generate_all_reports(formats=formats)
        
        elif choice == '2':
            codes_input = input("\nDigite os códigos (ex: REL01 REL02 REL03): ").strip()
            codes = codes_input.upper().split()
            
            if codes:
                formats = self._select_formats()
                for code in codes:
                    try:
                        self.reporter.generate_report(code, formats=formats)
                    except Exception as e:
                        logger.error(f"Erro ao gerar {code}: {str(e)}")
        
        elif choice == '3':
            print("Saindo...")
            return
        
        else:
            print("Opção inválida!")
    
    def _select_formats(self) -> List[str]:
        """Menu para selecionar formatos"""
        print("\nFormatos disponíveis: CSV, Excel (XLSX), PDF")
        print("  1. Todos (CSV + XLSX + PDF)")
        print("  2. Apenas CSV")
        print("  3. Apenas Excel (XLSX)")
        print("  4. Apenas PDF")
        print("  5. CSV + Excel")
        print("  6. CSV + PDF")
        
        choice = input("Escolha os formatos (1-6): ").strip()
        
        format_map = {
            '1': ['csv', 'xlsx', 'pdf'],
            '2': ['csv'],
            '3': ['xlsx'],
            '4': ['pdf'],
            '5': ['csv', 'xlsx'],
            '6': ['csv', 'pdf']
        }
        
        return format_map.get(choice, ['csv', 'xlsx', 'pdf'])


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline Manager - ProtecAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Pipeline completo (extração + normalização + DB + relatórios)
  python pipeline_manager.py --full
  
  # Apenas carga no banco (CSVs já existem)
  python pipeline_manager.py --load-db
  
  # Apenas relatórios
  python pipeline_manager.py --reports
  
  # Relatórios específicos
  python pipeline_manager.py --reports --codes REL01 REL02 --formats csv pdf
  
  # Menu interativo
  python pipeline_manager.py --interactive
  
  # Pipeline sem carga no banco
  python pipeline_manager.py --full --skip-database
        """
    )
    
    # Ações
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--full', action='store_true', 
                             help='Executa pipeline completo')
    action_group.add_argument('--load-db', action='store_true',
                             help='Apenas carrega CSVs no banco')
    action_group.add_argument('--reports', action='store_true',
                             help='Apenas gera relatórios')
    action_group.add_argument('--interactive', action='store_true',
                             help='Menu interativo para relatórios')
    
    # Opções
    parser.add_argument('--skip-extraction', action='store_true',
                       help='Pula extração (usa CSVs existentes)')
    parser.add_argument('--skip-database', action='store_true',
                       help='Pula carga no banco')
    parser.add_argument('--codes', nargs='+', 
                       help='Códigos dos relatórios (REL01, REL02, etc)')
    parser.add_argument('--formats', nargs='+', 
                       choices=['csv', 'xlsx', 'pdf'],
                       default=['csv', 'xlsx', 'pdf'],
                       help='Formatos de saída')
    parser.add_argument('--force', action='store_true',
                       help='Força reprocessamento mesmo se já processado')
    
    # Configurações do banco
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-port', type=int, default=5432)
    parser.add_argument('--db-name', default='protecai_db')
    parser.add_argument('--db-user', default='protecai')
    parser.add_argument('--db-password', default='protecai')
    parser.add_argument('--db-schema', default='protec_ai')
    
    args = parser.parse_args()
    
    # Criar manager
    manager = PipelineManager(
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        db_schema=args.db_schema
    )
    
    try:
        if args.full:
            # Pipeline completo
            manager.run_full_pipeline(
                skip_extraction=args.skip_extraction,
                skip_database=args.skip_database,
                report_codes=args.codes,
                report_formats=args.formats
            )
        
        elif args.load_db:
            # Apenas carga no banco
            logger.info("=" * 80)
            logger.info("CARGA NO BANCO DE DADOS")
            logger.info("=" * 80)
            stats = manager.loader.load_all(force=args.force)
            logger.info(f"✅ {stats['relays']} relés carregados")
        
        elif args.reports:
            # Apenas relatórios
            if args.codes:
                for code in args.codes:
                    manager.reporter.generate_report(code, formats=args.formats)
            else:
                manager.reporter.generate_all_reports(formats=args.formats)
        
        elif args.interactive:
            # Menu interativo
            manager.interactive_report_selector()
        
        return 0
    
    except Exception as e:
        logger.error(f"\n❌ ERRO CRÍTICO: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
