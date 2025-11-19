#!/usr/bin/env python3
"""Debug parser test"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.parsers.sepam_parser import SepamParser

# Test SEPAM parser
sepam_file = "inputs/txt/00-MF-12_2016-03-31.S40"
parser = SepamParser()

print("\n=== Testing SEPAM Parser ===")
print(f"File: {sepam_file}")

parsed = parser.parse_file(sepam_file)
relay_data = parsed.get('relay_data', {})

print(f"\nRelay Data Keys: {relay_data.keys()}")
print(f"modelo_rele: {relay_data.get('modelo_rele')}")
print(f"barras_identificador: {relay_data.get('barras_identificador')}")
print(f"subestacao_codigo: {relay_data.get('subestacao_codigo')}")
print(f"tipo_painel: {relay_data.get('tipo_painel')}")
print(f"data_configuracao: {relay_data.get('data_configuracao')}")

print(f"\nValidation...")
is_valid, errors = parser.validate_data(parsed)
print(f"Valid: {is_valid}")
if errors:
    print(f"Errors: {errors}")
