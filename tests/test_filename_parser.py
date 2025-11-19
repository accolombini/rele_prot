"""
Test Filename Parser
Valida extração de informações dos nomes dos arquivos
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.python.utils.filename_parser import FilenameParser


def test_sepam_filenames():
    """Test SEPAM .S40 filename parsing"""
    parser = FilenameParser()
    
    test_cases = [
        {
            'filename': '00-MF-12_2016-03-31.S40',
            'expected': {
                'valid': True,
                'subestacao_codigo': '00',
                'tipo_painel_codigo': 'MF',
                'barras_identificador': '12',
                'fabricante': 'SCHNEIDER ELECTRIC'
            }
        },
        {
            'filename': '00-MF-14_2016-03-31.S40',
            'expected': {
                'valid': True,
                'barras_identificador': '14'
            }
        },
        {
            'filename': '00-MF-24_2024-09-10.S40',
            'expected': {
                'valid': True,
                'barras_identificador': '24'
            }
        }
    ]
    
    print("=" * 80)
    print("TESTING SEPAM FILENAME PARSER")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['filename']}")
        result = parser.parse_sepam_filename(test['filename'])
        
        print(f"  Valid: {result.get('valid')}")
        if result.get('valid'):
            print(f"  Subestação: {result.get('subestacao_codigo')}")
            print(f"  Tipo Painel: {result.get('tipo_painel_codigo')} - {result.get('tipo_painel_descricao')}")
            print(f"  Barras: {result.get('barras_identificador')}")
            print(f"  Data: {result.get('data_configuracao')}")
            print(f"  Fabricante: {result.get('fabricante')}")
            
            # Validate expected fields
            for key, expected_value in test['expected'].items():
                actual_value = result.get(key)
                if actual_value != expected_value:
                    print(f"  ❌ MISMATCH: {key} = {actual_value}, expected {expected_value}")
                else:
                    print(f"  ✓ {key} = {actual_value}")
        else:
            print(f"  Error: {result.get('error')}")


def test_pdf_filenames():
    """Test PDF filename parsing with real files"""
    parser = FilenameParser()
    
    # Lista real de PDFs do diretório inputs/pdf/
    test_cases = [
        {
            'filename': 'P_122 52-MF-03B1_2021-03-17.pdf',
            'expected': {
                'valid': True,
                'modelo_rele': 'P122',
                'ansi_codigo': '52',
                'tipo_painel_codigo': 'MF',
                'barras_identificador': '03B1',
                'fabricante': 'SCHNEIDER ELECTRIC',
                'has_date': True
            }
        },
        {
            'filename': 'P143_204-MF-2B_2018-06-13.pdf',
            'expected': {
                'valid': True,
                'modelo_rele': 'P143',
                'ansi_codigo': '204',
                'tipo_painel_codigo': 'MF',
                'barras_identificador': '2B',
                'fabricante': 'GENERAL ELECTRIC',
                'has_date': True
            }
        },
        {
            'filename': 'P220_52-MK-02A_2020-07-08.pdf',
            'expected': {
                'valid': True,
                'modelo_rele': 'P220',
                'ansi_codigo': '52',
                'tipo_painel_codigo': 'MK',
                'barras_identificador': '02A',
                'fabricante': 'SCHNEIDER ELECTRIC',
                'has_date': True
            }
        },
        {
            'filename': 'P241_52-MP-20_2019-08-15.pdf',
            'expected': {
                'valid': True,
                'modelo_rele': 'P241',
                'ansi_codigo': '52',
                'tipo_painel_codigo': 'MP',
                'barras_identificador': '20',
                'fabricante': 'GENERAL ELECTRIC',
                'has_date': True
            }
        },
        {
            'filename': 'P922 52-MF-01BC.pdf',
            'expected': {
                'valid': True,
                'modelo_rele': 'P922',
                'ansi_codigo': '52',
                'tipo_painel_codigo': 'MF',
                'barras_identificador': '01BC',
                'fabricante': 'SCHNEIDER ELECTRIC',
                'has_date': False  # Este arquivo NÃO tem data
            }
        }
    ]
    
    print("\n" + "=" * 80)
    print("TESTING PDF FILENAME PARSER")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['filename']}")
        result = parser.parse_pdf_filename(test['filename'])
        
        print(f"  Valid: {result.get('valid')}")
        if result.get('valid'):
            print(f"  Modelo: {result.get('modelo_rele')}")
            print(f"  ANSI: {result.get('ansi_codigo')}")
            print(f"  Tipo Painel: {result.get('tipo_painel_codigo')} - {result.get('tipo_painel_descricao')}")
            print(f"  Barras: {result.get('barras_identificador')}")
            print(f"  Data: {result.get('data_configuracao')}")
            print(f"  Fabricante: {result.get('fabricante')}")
            
            # Validate expected fields
            all_ok = True
            for key, expected_value in test['expected'].items():
                if key == 'has_date':
                    actual_has_date = result.get('data_configuracao') is not None
                    if actual_has_date != expected_value:
                        print(f"  ❌ MISMATCH: has_date = {actual_has_date}, expected {expected_value}")
                        all_ok = False
                else:
                    actual_value = result.get(key)
                    if actual_value != expected_value:
                        print(f"  ❌ MISMATCH: {key} = {actual_value}, expected {expected_value}")
                        all_ok = False
            
            if all_ok:
                print(f"  ✓ All fields validated successfully")
        else:
            print(f"  ❌ Error: {result.get('error')}")


def test_auto_parse():
    """Test automatic parsing based on extension"""
    parser = FilenameParser()
    
    print("\n" + "=" * 80)
    print("TESTING AUTO PARSER")
    print("=" * 80)
    
    test_files = [
        '00-MF-12_2016-03-31.S40',
        'P143_204-MF-2B_2018-06-13.pdf',
        'invalid_file.txt'
    ]
    
    for filename in test_files:
        print(f"\n{filename}:")
        result = parser.parse(filename)
        print(f"  Valid: {result.get('valid')}")
        if result.get('valid'):
            print(f"  Type: {result.get('tipo_arquivo')}")
            print(f"  Fabricante: {result.get('fabricante')}")
            print(f"  Barras: {result.get('barras_identificador')}")
        else:
            print(f"  Error: {result.get('error')}")


if __name__ == '__main__':
    test_sepam_filenames()
    test_pdf_filenames()
    test_auto_parse()
    
    print("\n" + "=" * 80)
    print("FILENAME PARSER TESTS COMPLETED")
    print("=" * 80)
