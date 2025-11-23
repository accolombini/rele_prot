"""
ProtecAI Data Pipeline - Main Entry Point
Orchestrates the entire relay data extraction and normalization process
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.python.utils.logger import PipelineLogger
from src.python.utils.file_manager import FileManager
from src.python.utils.glossary_loader import GlossaryLoader
from src.python.database.repository import DatabaseRepository
from src.python.parsers.micon_parser import MiconParser
from src.python.parsers.schneider_parser import SchneiderParser
from src.python.parsers.sepam_parser import SepamParser
from src.python.exporters.excel_exporter import ExcelExporter
from src.python.exporters.full_parameters_exporter import FullParametersExporter


class ProtecAIPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_dir: str = None):
        # Load environment variables
        load_dotenv(project_root / 'docker' / 'postgres' / '.env')
        
        # Initialize utilities
        self.logger = PipelineLogger(log_dir=str(project_root / 'logs'))
        self.file_manager = FileManager(
            registry_path=str(project_root / 'inputs' / 'registry' / 'processed_files.json')
        )
        self.glossary = GlossaryLoader(
            glossary_dir=str(project_root / 'inputs' / 'glossario')
        )
        
        # Initialize database
        self.db = DatabaseRepository()
        
        # Initialize parsers
        self.micon_parser = MiconParser()  # GE relays (P143, P241)
        self.schneider_parser = SchneiderParser()  # Schneider relays (P122, P220, P922)
        self.sepam_parser = SepamParser()  # SEPAM relays
        
        # Paths
        self.input_pdf_dir = project_root / 'inputs' / 'pdf'
        self.input_txt_dir = project_root / 'inputs' / 'txt'
        self.output_csv_dir = project_root / 'outputs' / 'csv'
        self.output_excel_dir = project_root / 'outputs' / 'excel'
        
        # Initialize exporters
        self.csv_exporter = FullParametersExporter(
            output_dir=str(self.output_csv_dir),
            logger=self.logger
        )
        self.excel_exporter = ExcelExporter(
            output_dir=str(self.output_excel_dir),
            logger=self.logger
        )
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'skipped_duplicate': 0,
            'errors': 0,
            'exported_csv': 0,
            'exported_excel': 0,
            'export_errors': 0
        }
    
    def run(self):
        """Execute the complete pipeline"""
        self.logger.section("ProtecAI Data Pipeline - Starting")
        
        try:
            # Step 1: Discover files
            self.logger.step(1, "Discovering input files")
            pdf_files = self.file_manager.get_pdf_files(str(self.input_pdf_dir))
            s40_files = self.file_manager.get_s40_files(str(self.input_txt_dir))
            
            all_files = list(pdf_files) + list(s40_files)
            self.stats['total_files'] = len(all_files)
            
            self.logger.info(f"Found {len(pdf_files)} PDF files")
            self.logger.info(f"Found {len(s40_files)} .S40 files")
            self.logger.info(f"Total files to process: {self.stats['total_files']}")
            
            # Step 2: Process each file
            self.logger.step(2, "Processing files")
            
            for file_path in all_files:
                self._process_file(file_path)
            
            # Step 2.5: Normalize CSV files
            self.logger.info("[STEP 2.5] Normalizing CSV files to 3FN format")
            self._normalize_csv_files()
            
            # Step 3: Load normalized data into database
            self.logger.step(3, "Loading data into database")
            self._load_to_database()
            
            # Step 4: Generate reports
            self.logger.step(4, "Generating reports")
            self._generate_summary()
            
            self.logger.section("Pipeline Completed Successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _process_file(self, file_path: Path):
        """Process a single file"""
        try:
            self.logger.info(f"\nProcessing: {file_path.name}")
            
            # Check if already processed
            if self.file_manager.is_file_processed(str(file_path)):
                self.logger.info("  ✓ File already processed (skipping)")
                self.stats['skipped_duplicate'] += 1
                return
            
            # Parse file based on extension
            if file_path.suffix.lower() == '.pdf':
                # Detect manufacturer first
                from src.python.extractors.pdf_extractor import PdfExtractor
                extractor = PdfExtractor()
                manufacturer = extractor.detect_manufacturer(str(file_path))
                
                if manufacturer == 'GENERAL ELECTRIC':
                    self.logger.info(f"  → Detected: GE (MiCOM S1 Agile)")
                    parsed_data = self.micon_parser.parse_file(str(file_path))
                elif manufacturer == 'SCHNEIDER ELECTRIC':
                    self.logger.info(f"  → Detected: Schneider Electric (Easergy Studio)")
                    parsed_data = self.schneider_parser.parse_file(str(file_path))
                else:
                    self.logger.error(f"  ✗ Unknown manufacturer: {manufacturer}")
                    self.stats['errors'] += 1
                    return
            
            elif file_path.suffix.upper() == '.S40':
                parsed_data = self.sepam_parser.parse_file(str(file_path))
            
            else:
                self.logger.warning(f"  ⚠ Unsupported file type: {file_path.suffix}")
                return
            
            # Validate parsed data
            is_valid, errors = self._validate_parsed_data(parsed_data)
            if not is_valid:
                self.logger.error(f"  ✗ Validation failed: {', '.join(errors)}")
                self.stats['errors'] += 1
                return
            
            # Log parsing success
            self.logger.info(f"  ✓ Parsed successfully")
            self.logger.info(f"    - Manufacturer: {parsed_data['manufacturer']}")
            self.logger.info(f"    - Model: {parsed_data['relay_data']['modelo_rele']}")
            self.logger.info(f"    - Type: {parsed_data['relay_data'].get('tipo_rele', 'N/A')}")
            self.logger.info(f"    - Barras: {parsed_data['relay_data']['barras_identificador']}")
            self.logger.info(f"    - CTs: {len(parsed_data['ct_data'])} | VTs: {len(parsed_data['vt_data'])}")
            
            # Export to CSV and Excel
            base_filename = file_path.stem  # Filename without extension
            export_success = self._export_data(parsed_data, base_filename)
            
            if not export_success:
                self.logger.error(f"  ✗ Export failed for {file_path.name}")
                self.stats['export_errors'] += 1
                # Don't mark as processed if export fails
                return
            
            # Mark as processed only after successful export
            self.file_manager.mark_file_processed(
                str(file_path),
                metadata={
                    'manufacturer': parsed_data['manufacturer'],
                    'model': parsed_data['relay_data']['modelo_rele'],
                    'exported': True,
                    'export_timestamp': datetime.now().isoformat()
                }
            )
            
            self.stats['processed'] += 1
            
        except Exception as e:
            self.logger.error(f"  ✗ Error processing file: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
    
    def _export_data(self, parsed_data: dict, base_filename: str) -> bool:
        """
        Export parsed data to CSV and Excel
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            self.logger.info(f"  → Exporting data...")
            
            # Export to CSV (full parameters format - audited)
            try:
                csv_file = self.csv_exporter.export_full_parameters(parsed_data, base_filename)
                self.stats['exported_csv'] += 1
                self.logger.info(f"    ✓ CSV export: complete parameters")
            except Exception as e:
                self.logger.error(f"    ✗ CSV export failed: {str(e)}")
                return False
            
            # Export to Excel
            try:
                excel_file = self.excel_exporter.export_relay_data(parsed_data, base_filename)
                if excel_file:
                    self.stats['exported_excel'] += 1
                    self.logger.info(f"    ✓ Excel export: 1 workbook")
                else:
                    self.logger.warning(f"    ⚠ Excel export skipped (openpyxl not available)")
            except Exception as e:
                self.logger.error(f"    ✗ Excel export failed: {str(e)}")
                # Don't fail the entire export if only Excel fails
                # CSV is the critical format
            
            return True
            
        except Exception as e:
            self.logger.error(f"  ✗ Export error: {str(e)}", exc_info=True)
            return False
    
    def _validate_parsed_data(self, parsed_data: dict) -> tuple[bool, list]:
        """Validate parsed data"""
        errors = []
        
        if not parsed_data.get('manufacturer'):
            errors.append("Missing manufacturer")
        
        relay_data = parsed_data.get('relay_data', {})
        if not relay_data.get('modelo_rele'):
            errors.append("Missing model name")
        
        return (len(errors) == 0, errors)
    
    def _normalize_csv_files(self):
        """Normalize exported CSV files"""
        from src.python.normalizers.relay_normalizer import RelayNormalizer
        from src.python.exporters.normalized_csv_exporter import NormalizedCsvExporter
        from src.python.exporters.normalized_excel_exporter import NormalizedExcelExporter
        
        try:
            normalizer = RelayNormalizer(logger=self.logger)
            csv_exporter = NormalizedCsvExporter(
                output_dir=str(project_root / 'outputs' / 'norm_csv'),
                logger=self.logger
            )
            excel_exporter = NormalizedExcelExporter(
                output_dir=str(project_root / 'outputs' / 'norm_excel'),
                logger=self.logger
            )
            
            # Initialize consolidated CSVs (with headers)
            csv_exporter.initialize_csvs()
            
            # Clean old normalized Excel files
            norm_excel_dir = project_root / 'outputs' / 'norm_excel'
            for old_excel in norm_excel_dir.glob('*_NORMALIZED.xlsx'):
                old_excel.unlink()
            
            # Find all CSV files in output directory
            csv_files = list(self.output_csv_dir.glob('*.csv'))
            self.logger.info(f"  → Found {len(csv_files)} CSV files to normalize")
            
            for csv_file in csv_files:
                try:
                    self.logger.info(f"  → Normalizing: {csv_file.name}")
                    normalized_data = normalizer.normalize_from_csv(str(csv_file))
                    
                    # Append to consolidated CSVs
                    csv_exporter.append_normalized_data(normalized_data)
                    
                    # Export individual normalized Excel
                    base_filename = csv_file.stem
                    excel_exporter.export_normalized(normalized_data, base_filename)
                    
                    # Log summary
                    relay_id = normalized_data['relay_info']['relay_id']
                    self.logger.info(f"  → Relay: {relay_id}, CTs: {len(normalized_data.get('cts', []))}, VTs: {len(normalized_data.get('vts', []))}, Protections: {len(normalized_data.get('protections', []))}, Parameters: {len(normalized_data.get('parameters', []))}")
                except Exception as e:
                    self.logger.error(f"    ✗ Failed to normalize {csv_file.name}: {str(e)}")
                    raise
            
            self.logger.info("  ✓ CSV normalization completed")
            self.logger.info(f"  ✓ Excel normalization completed: {len(csv_files)} files")
        except Exception as e:
            self.logger.error(f"  ✗ CSV normalization failed: {str(e)}", exc_info=True)
            raise
    
    def _load_to_database(self):
        """Load normalized CSV data into PostgreSQL"""
        from src.python.database.database_loader import DatabaseLoader
        
        try:
            csv_path = project_root / 'outputs' / 'norm_csv'
            loader = DatabaseLoader(
                db_host=os.getenv('POSTGRES_HOST', 'localhost'),
                db_port=int(os.getenv('POSTGRES_PORT', 5432)),
                db_name=os.getenv('POSTGRES_DB', 'protecai_db'),
                db_user=os.getenv('POSTGRES_USER', 'protecai'),
                db_password=os.getenv('POSTGRES_PASSWORD', 'protecai'),
                db_schema='protec_ai',
                csv_base_path=csv_path
            )
            stats = loader.load_all(force=True)  # Force reload para garantir dados atualizados
            self.logger.info("  ✓ Database loading completed")
            self.logger.info(f"    - Relays: {stats.get('relays', 0)}")
            self.logger.info(f"    - Protections: {stats.get('protections', 0)}")
            self.logger.info(f"    - Parameters: {stats.get('parameters', 0)}")
            self.logger.info(f"    - CTs: {stats.get('cts', 0)}")
            self.logger.info(f"    - VTs: {stats.get('vts', 0)}")
        except Exception as e:
            self.logger.error(f"  ✗ Database loading failed: {str(e)}", exc_info=True)
            raise
    
    def _generate_summary(self):
        """Generate processing summary"""
        self.logger.info("\n" + "="*80)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("="*80)
        self.logger.info(f"Total files found:      {self.stats['total_files']}")
        self.logger.info(f"Successfully processed: {self.stats['processed']}")
        self.logger.info(f"Skipped (duplicate):    {self.stats['skipped_duplicate']}")
        self.logger.info(f"Parsing errors:         {self.stats['errors']}")
        self.logger.info(f"CSV files exported:     {self.stats['exported_csv']}")
        self.logger.info(f"Excel files exported:   {self.stats['exported_excel']}")
        self.logger.info(f"Export errors:          {self.stats['export_errors']}")
        self.logger.info("="*80)


def main():
    """Main entry point"""
    pipeline = ProtecAIPipeline()
    pipeline.run()


if __name__ == '__main__':
    main()
