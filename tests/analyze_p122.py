#!/usr/bin/env python3
"""Análise rápida de padrões no P122"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.extractors.pdf_extractor import PdfExtractor

ext = PdfExtractor()
text = ext.extract_text('inputs/pdf/P_122 52-MF-03B1_2021-03-17.pdf')
lines = text.split('\n')

print(f"Total de linhas no PDF: {len(lines)}")
print(f"Linhas não vazias: {len([l for l in lines if l.strip()])}")

# Contar linhas com códigos
pattern = re.compile(r'^\d{4}:')
code_lines = [l.strip() for l in lines if pattern.match(l.strip())]

print(f"\nLinhas com código (0xxx:): {len(code_lines)}")
print(f"Códigos únicos: {len(set([l[:4] for l in code_lines]))}")

# Mostrar primeiras 20
print("\n--- Primeiras 20 linhas com código ---")
for i, line in enumerate(code_lines[:20], 1):
    print(f"{i:2}. {line[:80]}")

# Verificar se alguma tem continuação multi-linha
print("\n--- Verificando continuações ---")
has_continuation = 0
for i, line in enumerate(lines):
    if pattern.match(line.strip()):
        # Check next line
        if i+1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line and not pattern.match(next_line):
                if 'easergy' not in next_line.lower() and 'page' not in next_line.lower():
                    has_continuation += 1
                    if has_continuation <= 5:
                        print(f"\nCódigo: {line.strip()[:60]}")
                        print(f"  → Cont: {next_line[:60]}")

print(f"\nTotal com continuação: {has_continuation}")
