"""
Test script for SEPAM extractor and exporters
Quick validation of the complete extraction → export pipeline
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.python.parsers.sepam_parser import SepamParser
from src.python.exporters.csv_exporter import CsvExporter
from src.python.exporters.excel_exporter import ExcelExporter
from src.python.utils.logger import PipelineLogger


def test_sepam_pipeline():
    """Test SEPAM extraction and export"""
    
    # Initialize
    logger = PipelineLogger(log_dir=str(project_root / 'logs'))
    parser = SepamParser()
    
    # Test file
    test_file = project_root / 'inputs' / 'txt' / '00-MF-12_2016-03-31.S40'
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False
    
    try:
        # Parse
        logger.section("SEPAM Pipeline Test")
        logger.info(f"Testing file: {test_file.name}")
        
        parsed_data = parser.parse_file(str(test_file))
        
        logger.info("✓ Parsing successful")
        logger.info(f"  Manufacturer: {parsed_data['manufacturer']}")
        logger.info(f"  Model: {parsed_data['relay_data']['model_name']}")
        logger.info(f"  Barras: {parsed_data['relay_data']['barras_identificador']}")
        logger.info(f"  CTs: {len(parsed_data['ct_data'])} | VTs: {len(parsed_data['vt_data'])}")
        logger.info(f"  Protection Functions: {len([f for f in parsed_data['protection_functions'] if f.get('is_enabled')])}")
        
        # Export CSV
        logger.info("\nExporting to CSV (consolidated)...")
        csv_exporter = CsvExporter(
            output_dir=str(project_root / 'outputs' / 'csv'),
            logger=logger
        )
        
        csv_file = csv_exporter.export_relay_data(parsed_data, test_file.stem)
        logger.info(f"✓ CSV export successful: 1 consolidated file")
        
        # Export Excel
        logger.info("\nExporting to Excel...")
        excel_exporter = ExcelExporter(
            output_dir=str(project_root / 'outputs' / 'excel'),
            logger=logger
        )
        
        excel_file = excel_exporter.export_relay_data(parsed_data, test_file.stem)
        if excel_file:
            logger.info(f"✓ Excel export successful: {excel_file}")
        else:
            logger.warning("⚠ Excel export skipped")
        
        logger.section("Test Completed Successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False


if __name__ == '__main__':
    success = test_sepam_pipeline()
    sys.exit(0 if success else 1)
