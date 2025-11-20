#!/usr/bin/env python3
"""Script de teste do database loader"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database_loader import DatabaseLoader
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 80)
print("TESTE DO DATABASE LOADER")
print("=" * 80)

loader = DatabaseLoader()

try:
    stats = loader.load_all(force=False)
    
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS FINAIS")
    print("=" * 80)
    print(f"Relés carregados: {stats['relays']}")
    print(f"Erros: {len(stats['errors'])}")
    
    if stats['errors']:
        print("\nErros encontrados:")
        for error in stats['errors']:
            print(f"  - {error}")
    
    print("\n✅ TESTE CONCLUÍDO")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
