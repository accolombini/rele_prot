#!/usr/bin/env python3
"""
Test Full Parameters Extraction
Testa a extração completa de parâmetros com suporte a multi-linha
Baseado na auditoria do arquivo P_122 52-MF-03B1_2021-03-17.pdf
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.extractors.pdf_extractor import PdfExtractor
from src.python.exporters.full_parameters_exporter import FullParametersExporter
from src.python.parsers.schneider_parser import SchneiderParser

# Test with P_122 (the audited file)
pdf_file = "inputs/pdf/P_122 52-MF-03B1_2021-03-17.pdf"

print("\n" + "="*80)
print("TESTE DE EXTRAÇÃO COMPLETA - P122 (Arquivo Auditado)")
print("="*80)

# Extract using updated extractor
print("\n[1] Extraindo dados completos do PDF...")
extractor = PdfExtractor()
extracted = extractor.extract_all(pdf_file)

# Display validation metrics
validation = extracted.get('validation', {})
print("\n[2] MÉTRICAS DE VALIDAÇÃO:")
print(f"  Total de parâmetros: {validation.get('total_parameters', 0)}")
print(f"  CTs extraídos: {validation.get('ct_count', 0)}")
print(f"  VTs extraídos: {validation.get('vt_count', 0)}")
print(f"  Funções de proteção: {validation.get('protection_functions', 0)}")
print(f"  Funções habilitadas: {validation.get('enabled_functions', 0)}")
print(f"  Score de completude: {validation.get('completeness_score', 0):.1f}%")

if validation.get('warnings'):
    print("\n  ⚠️ Avisos:")
    for warning in validation['warnings']:
        print(f"    - {warning}")

# Check specific parameters from audit
print("\n[3] VERIFICAÇÃO DE PARÂMETROS CRÍTICOS (da auditoria):")

all_params = extracted.get('all_parameters', [])
params_by_code = {p['code']: p for p in all_params}

# CT RATIO (deve ter 4 parâmetros)
ct_codes = ['0120', '0121', '0122', '0123']
print("\n  CT RATIO:")
ct_found = 0
for code in ct_codes:
    if code in params_by_code:
        param = params_by_code[code]
        print(f"    ✓ {code}: {param['parameter']} = {param['value']}")
        ct_found += 1
    else:
        print(f"    ✗ {code}: NÃO ENCONTRADO")
print(f"  → CT RATIO: {ct_found}/4 parâmetros ({ct_found/4*100:.0f}%)")

# Protection functions (verificar alguns exemplos)
prot_codes = ['0201', '0204', '0231', '0241', '0242']
print("\n  PROTEÇÕES (amostra):")
prot_found = 0
for code in prot_codes:
    if code in params_by_code:
        param = params_by_code[code]
        print(f"    ✓ {code}: {param['parameter']} = {param['value']}")
        prot_found += 1
    else:
        print(f"    ✗ {code}: NÃO ENCONTRADO")
print(f"  → Proteções: {prot_found}/5 amostras ({prot_found/5*100:.0f}%)")

# Check for multi-line parameters (RL2-RL6 lists)
print("\n[4] PARÂMETROS COM CONTINUAÇÃO MULTI-LINHA:")
multi_line_params = [p for p in all_params if p.get('continuation_lines')]
print(f"  Total com continuação: {len(multi_line_params)}")

if multi_line_params:
    print("\n  Exemplos:")
    for param in multi_line_params[:5]:  # Show first 5
        cont = ' | '.join(param['continuation_lines'][:3])  # First 3 lines
        if len(param['continuation_lines']) > 3:
            cont += f" ... (+{len(param['continuation_lines'])-3} linhas)"
        print(f"    {param['code']}: {param['parameter']}")
        print(f"      Valor: {param['value']}")
        print(f"      Continuação: {cont}")

# Parse complete file
print("\n[5] PARSING COMPLETO COM SCHNEIDER PARSER...")
parser = SchneiderParser()
parsed_data = parser.parse_file(pdf_file)

# Export to full parameters CSV
print("\n[6] EXPORTANDO CSV COMPLETO DE PARÂMETROS...")
exporter = FullParametersExporter()
csv_file = exporter.export_full_parameters(parsed_data, "P_122_52-MF-03B1_2021-03-17")
print(f"  ✓ Arquivo gerado: {csv_file}")

# Summary
print("\n" + "="*80)
print("RESUMO DA EXTRAÇÃO")
print("="*80)
print(f"Total de parâmetros extraídos: {len(all_params)}")
print(f"Parâmetros com multi-linha: {len(multi_line_params)} ({len(multi_line_params)/len(all_params)*100:.1f}%)")
print(f"Cobertura estimada: {min(100, (len(all_params) / 450) * 100):.1f}%")
print(f"\nObjetivo da auditoria: 92-95% → Atual: {validation.get('completeness_score', 0):.1f}%")

# Compare with audit expectations
expected_total = 420  # From audit: ~400-420 parameters
actual_total = len(all_params)
coverage = (actual_total / expected_total) * 100

print(f"\nComparação com auditoria:")
print(f"  Esperado: ~{expected_total} parâmetros")
print(f"  Extraído: {actual_total} parâmetros")
print(f"  Taxa de captura: {coverage:.1f}%")

if coverage >= 95:
    print("\n  ✅ EXCELENTE - Acima da meta de 95%!")
elif coverage >= 90:
    print("\n  ✓ BOM - Dentro da meta (90-95%)")
else:
    print("\n  ⚠️ ATENÇÃO - Abaixo da meta esperada")

print("\n" + "="*80)
