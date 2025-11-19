#!/usr/bin/env python3
"""Debug P922 extraction"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.python.extractors.pdf_extractor import PdfExtractor

# Test P922 extraction
pdf_file = "inputs/pdf/P922 52-MF-01BC.pdf"
extractor = PdfExtractor()

print("\n=== P922 PDF Extraction Test ===")
print(f"File: {pdf_file}")

# Extract full text
text = extractor.extract_text(pdf_file)
print(f"\nTotal text length: {len(text)} characters")

# Search for VT RATIO section
import re
vt_section = re.search(r'VT RATIO.*?(?:\n\n|\Z)', text, re.DOTALL)
if vt_section:
    print("\n✓ Found VT RATIO section:")
    print(vt_section.group(0)[:500])
else:
    print("\n✗ VT RATIO section NOT found")
    
# Search for specific VT lines
vt_lines = [
    r'0120:.*?Main VT Primary',
    r'0122:.*?Main VT Secundary',
    r'0123:.*?E/Gnd VT Primary',
    r'0125:.*?E/Gnd VT Secundary'
]

print("\n--- Searching for VT parameter lines ---")
for pattern in vt_lines:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"✓ Found: {match.group(0)}")
    else:
        print(f"✗ NOT found: {pattern}")

# Test extraction
print("\n--- Testing extract_ct_vt_data() ---")
ct_vt_data = extractor.extract_ct_vt_data(text)
print(f"CTs found: {len(ct_vt_data['current_transformers'])}")
print(f"VTs found: {len(ct_vt_data['voltage_transformers'])}")

if ct_vt_data['voltage_transformers']:
    print("\nVT Data extracted:")
    for vt in ct_vt_data['voltage_transformers']:
        print(f"  - Type: {vt['vt_type']}")
        print(f"    Primary: {vt['primary_rating_v']} V")
        print(f"    Secondary: {vt['secondary_rating_v']} V")
        print(f"    Ratio: {vt['ratio']}")
else:
    print("\n✗ NO VT data extracted!")
    
# Show snippet around VT data
print("\n--- Text snippet around 'Main VT' ---")
main_vt_pos = text.find('Main VT')
if main_vt_pos > 0:
    snippet = text[max(0, main_vt_pos-100):main_vt_pos+300]
    print(snippet)
else:
    print("✗ 'Main VT' not found in text")
