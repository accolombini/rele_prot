"""
Test PDF filename parser
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.python.utils.filename_parser import FilenameParser

def test_pdf_filenames():
    """Test parsing of real PDF filenames"""
    parser = FilenameParser()
    
    pdf_files = [
        'P_122 52-MF-03B1_2021-03-17.pdf',
        'P143_204-MF-2B_2018-06-13.pdf',
        'P220_52-MK-02A_2020-07-08.pdf',
        'P241_52-MP-20_2019-08-15.pdf',
        'P922 52-MF-01BC.pdf'
    ]
    
    print("=" * 80)
    print("TESTE DE PARSER DE FILENAME DOS PDFs")
    print("=" * 80)
    
    for i, filename in enumerate(pdf_files, 1):
        print(f"\n{i}. PDF: {filename}")
        result = parser.parse_pdf_filename(filename)
        
        if result.get('valid'):
            print(f"   ✓ Modelo: {result.get('modelo_rele')}")
            print(f"   ✓ ANSI: {result.get('ansi_codigo')}")
            print(f"   ✓ Tipo Painel: {result.get('tipo_painel_codigo')}")
            print(f"   ✓ Barras: {result.get('barras_identificador')}")
            print(f"   ✓ Data: {result.get('data_configuracao')}")
            print(f"   ✓ Fabricante: {result.get('fabricante')}")
        else:
            print(f"   ❌ ERRO: {result.get('error')}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_pdf_filenames()
