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
from src.python.exporters.csv_exporter import CsvExporter
from src.python.exporters.excel_exporter import ExcelExporter


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
        self.csv_exporter = CsvExporter(
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
            
            # Step 3: Generate reports
            self.logger.step(3, "Generating reports")
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
            
            # Export to CSV (consolidated)
            try:
                csv_file = self.csv_exporter.export_relay_data(parsed_data, base_filename)
                self.stats['exported_csv'] += 1
                self.logger.info(f"    ✓ CSV export: 1 consolidated file")
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
