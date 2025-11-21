"""
ProtecAI - PIPELINE COMPLETA DE DADOS
Executa todas as fases em sequência:
1. Extração (PDF/TXT → CSV/Excel)
2. Normalização (CSV → norm_csv)
3. Carga no Banco (norm_csv → PostgreSQL)

CORREÇÕES CONSOLIDADAS (21/11/2025):
✅ GE P241/P143: Proteções extraídas de continuation_lines (formato 09.XX: Nome: Status)
✅ Regex para parsing: ^([0-9A-F]{2}\.[0-9A-F]{2}):\s*(.+?):\s*(Enabled|Disabled)$
✅ Mapeamento ANSI expandido: 49 (Thermal), 50/51 (OC), 50N/51N (EF), 27/59 (Voltage), 
   81 (Freq), 50BF (CB Fail), 14 (Stall), 32 (Reverse Power), 40 (Loss of Field), etc.
✅ load_parameters() implementado: 3947 parâmetros carregados corretamente
✅ Relés sem CT (P922 voltage relay) não criam linhas vazias no CSV consolidado
✅ Todas as FKs resolvidas: relay_id → protection_function_id → parameters

RESULTADO ESPERADO:
  • 8 relés: P241, P143, P922, P220, P122, 3x SEPAM S40
  • 137 proteções: 33 (P241) + 27 (P143) + 20 (P922) + 29 (P220) + 22 (P122) + 6 (SEPAMs)
  • 3947 parâmetros
  • 4 CTs, 5 VTs

NOTA: Relatórios são gerados SOB DEMANDA via generate_reports.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.python.utils.logger import PipelineLogger


def run_phase(phase_name: str, script_path: str, logger: PipelineLogger) -> bool:
    """
    Executa uma fase da pipeline
    
    Returns:
        True se sucesso, False se erro
    """
    logger.section(f"FASE: {phase_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(line)
        
        logger.info(f"✅ {phase_name} CONCLUÍDA COM SUCESSO")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ ERRO em {phase_name}")
        logger.error(f"Código de saída: {e.returncode}")
        
        if e.stdout:
            logger.error("STDOUT:")
            for line in e.stdout.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
        
        if e.stderr:
            logger.error("STDERR:")
            for line in e.stderr.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
        
        return False
    except Exception as e:
        logger.error(f"❌ EXCEÇÃO em {phase_name}: {str(e)}")
        return False


def main():
    """Executa pipeline completa de dados"""
    
    # Initialize logger
    logger = PipelineLogger(log_dir=str(project_root / 'logs'))
    
    start_time = datetime.now()
    
    logger.section("=" * 80)
    logger.section("PROTECAI - PIPELINE COMPLETA DE DADOS")
    logger.section("=" * 80)
    logger.info(f"Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.section("=" * 80)
    
    # Definir fases da pipeline de dados
    phases = [
        {
            'name': 'FASE 1 - EXTRAÇÃO',
            'script': project_root / 'src' / 'python' / 'main.py',
            'description': 'Extrai dados de PDFs e TXTs → CSV/Excel'
        },
        {
            'name': 'FASE 2 - NORMALIZAÇÃO',
            'script': project_root / 'src' / 'python' / 'normalize.py',
            'description': 'Normaliza CSVs para 3FN → norm_csv'
        },
        {
            'name': 'FASE 3 - CARGA NO BANCO',
            'script': project_root / 'src' / 'python' / 'test_loader.py',
            'description': 'Carrega dados normalizados → PostgreSQL'
        }
    ]
    
    # Executar fases sequencialmente
    results = []
    for i, phase in enumerate(phases, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"EXECUTANDO FASE {i}/3: {phase['name']}")
        logger.info(f"Descrição: {phase['description']}")
        logger.info(f"Script: {phase['script'].name}")
        logger.info(f"{'=' * 80}\n")
        
        success = run_phase(phase['name'], phase['script'], logger)
        results.append({
            'fase': phase['name'],
            'success': success
        })
        
        if not success:
            logger.error(f"\n❌ PIPELINE INTERROMPIDA - Falha em {phase['name']}")
            break
    
    # Sumário final
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.section("\n" + "=" * 80)
    logger.section("SUMÁRIO DA EXECUÇÃO")
    logger.section("=" * 80)
    
    for result in results:
        status = "✅ SUCESSO" if result['success'] else "❌ FALHA"
        logger.info(f"{result['fase']}: {status}")
    
    logger.section("=" * 80)
    logger.info(f"Início:   {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Fim:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duração:  {duration.total_seconds():.1f} segundos")
    
    all_success = all(r['success'] for r in results)
    
    if all_success:
        logger.section("=" * 80)
        logger.section("🎉 PIPELINE DE DADOS CONCLUÍDA COM SUCESSO!")
        logger.section("=" * 80)
        logger.info("")
        logger.info("📊 Para gerar relatórios, execute:")
        logger.info("   python src/python/generate_reports.py --all")
        logger.info("")
        return 0
    else:
        logger.section("=" * 80)
        logger.section("❌ PIPELINE FALHOU - Verifique os logs acima")
        logger.section("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
