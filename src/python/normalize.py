"""
FASE 2 - Normalização de Dados
Lê CSVs da FASE 1, normaliza para 3FN e exporta
"""

import sys
from pathlib import Path
from glob import glob

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.python.utils.logger import PipelineLogger
from src.python.normalizers.relay_normalizer import RelayNormalizer
from src.python.exporters.normalized_csv_exporter import NormalizedCsvExporter
from src.python.exporters.normalized_excel_exporter import NormalizedExcelExporter


class NormalizationPipeline:
    """Pipeline FASE 2: Normalização"""
    
    def __init__(self):
        self.logger = PipelineLogger(log_dir=str(project_root / 'logs'))
        
        # Paths
        self.input_csv_dir = project_root / 'outputs' / 'csv'
        
        # Normalizer
        self.normalizer = RelayNormalizer(logger=self.logger)
        
        # Exporters
        self.csv_exporter = NormalizedCsvExporter(
            output_dir=str(project_root / 'outputs' / 'norm_csv'),
            logger=self.logger
        )
        self.excel_exporter = NormalizedExcelExporter(
            output_dir=str(project_root / 'outputs' / 'norm_excel'),
            logger=self.logger
        )
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'errors': 0,
            'csv_exported': 0,
            'excel_exported': 0
        }
    
    def run(self):
        """Execute FASE 2 pipeline"""
        self.logger.section("FASE 2 - Normalization Pipeline - Starting")
        
        try:
            # Step 1: Discover CSV files from FASE 1
            self.logger.step(1, "Discovering CSV files from FASE 1")
            csv_files = list(self.input_csv_dir.glob('*.csv'))
            self.stats['total_files'] = len(csv_files)
            
            if self.stats['total_files'] == 0:
                self.logger.error("No CSV files found in outputs/csv/")
                self.logger.info("Please run FASE 1 first (main.py)")
                return
            
            self.logger.info(f"Found {self.stats['total_files']} CSV files to normalize")
            
            # Step 2: Initialize consolidated CSVs
            self.logger.step(2, "Initializing consolidated CSVs")
            self.csv_exporter.initialize_csvs()
            
            # Step 3: Normalize each file
            self.logger.step(3, "Normalizing files")
            
            for csv_file in csv_files:
                self._process_file(csv_file)
            
            # Step 4: Generate summary
            self.logger.step(4, "Generating reports")
            self._generate_summary()
            
            self.logger.section("FASE 2 - Normalization Completed Successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _process_file(self, csv_file: Path):
        """Process a single CSV file"""
        try:
            self.logger.info(f"\nNormalizing: {csv_file.name}")
            
            # Normalize from CSV
            normalized_data = self.normalizer.normalize_from_csv(str(csv_file))
            
            # Append to consolidated CSVs
            self.csv_exporter.append_normalized_data(normalized_data)
            self.stats['csv_exported'] += 1
            
            # Export individual Excel
            base_filename = csv_file.stem
            excel_file = self.excel_exporter.export_normalized(normalized_data, base_filename)
            if excel_file:
                self.stats['excel_exported'] += 1
            
            self.stats['processed'] += 1
            self.logger.info(f"  ✓ Normalized successfully")
            
        except Exception as e:
            self.logger.error(f"  ✗ Error normalizing file: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
    
    def _generate_summary(self):
        """Generate processing summary"""
        self.logger.info("\n" + "="*80)
        self.logger.info("NORMALIZATION SUMMARY")
        self.logger.info("="*80)
        self.logger.info(f"Total files found:      {self.stats['total_files']}")
        self.logger.info(f"Successfully processed: {self.stats['processed']}")
        self.logger.info(f"Errors:                 {self.stats['errors']}")
        self.logger.info(f"Consolidated CSVs:      5 files (all_*.csv)")
        self.logger.info(f"Individual Excel:       {self.stats['excel_exported']} files")
        self.logger.info("="*80)


def main():
    """Main entry point"""
    pipeline = NormalizationPipeline()
    pipeline.run()


if __name__ == '__main__':
    main()
