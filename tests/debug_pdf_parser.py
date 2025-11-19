#!/usr/bin/env python3
"""Debug PDF parser test"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.parsers.schneider_parser import SchneiderParser
from src.python.parsers.micon_parser import MiconParser

# Test Schneider parser
pdf1 = "inputs/pdf/P_122 52-MF-03B1_2021-03-17.pdf"
parser_schneider = SchneiderParser()

print("\n=== Testing Schneider Parser ===")
print(f"File: {pdf1}")

parsed = parser_schneider.parse_file(pdf1)
relay_data = parsed.get('relay_data', {})

print(f"\nRelay Data Keys: {relay_data.keys()}")
print(f"modelo_rele: {relay_data.get('modelo_rele')}")
print(f"barras_identificador: {relay_data.get('barras_identificador')}")
print(f"data_configuracao: {relay_data.get('data_configuracao')}")
print(f"fabricante: {relay_data.get('fabricante')}")

print(f"\nValidation...")
is_valid, errors = parser_schneider.validate_data(parsed)
print(f"Valid: {is_valid}")
if errors:
    print(f"Errors: {errors}")

# Test MiCOM parser
pdf2 = "inputs/pdf/P143_204-MF-2B_2018-06-13.pdf"
parser_micon = MiconParser()

print("\n\n=== Testing MiCOM Parser ===")
print(f"File: {pdf2}")

parsed2 = parser_micon.parse_file(pdf2)
relay_data2 = parsed2.get('relay_data', {})

print(f"\nRelay Data Keys: {relay_data2.keys()}")
print(f"modelo_rele: {relay_data2.get('modelo_rele')}")
print(f"barras_identificador: {relay_data2.get('barras_identificador')}")
print(f"data_configuracao: {relay_data2.get('data_configuracao')}")
print(f"fabricante: {relay_data2.get('fabricante')}")

print(f"\nValidation...")
is_valid2, errors2 = parser_micon.validate_data(parsed2)
print(f"Valid: {is_valid2}")
if errors2:
    print(f"Errors: {errors2}")
