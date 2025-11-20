#!/usr/bin/env python3
"""
Script de exemplo para geração de relatórios
Uso:
    python generate_reports.py --all                    # Gera todos os 9 relatórios
    python generate_reports.py --report REL01           # Gera apenas o REL01
    python generate_reports.py --report REL01 --format csv pdf  # Apenas CSV e PDF
    python generate_reports.py --list                   # Lista relatórios disponíveis
"""
import argparse
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from reporters.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description='Gerador de Relatórios ProtecAI')
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Gera todos os 9 relatórios'
    )
    
    parser.add_argument(
        '--report',
        type=str,
        help='Código do relatório específico (REL01, REL02, etc)'
    )
    
    parser.add_argument(
        '--format',
        nargs='+',
        choices=['csv', 'xlsx', 'pdf'],
        default=['csv', 'xlsx', 'pdf'],
        help='Formatos de saída (padrão: todos)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Lista todos os relatórios disponíveis'
    )
    
    # Configurações do banco (podem vir de .env)
    parser.add_argument('--db-host', default='localhost', help='Host do PostgreSQL')
    parser.add_argument('--db-port', type=int, default=5432, help='Porta do PostgreSQL')
    parser.add_argument('--db-name', default='protecai_db', help='Nome do banco')
    parser.add_argument('--db-user', default='protecai', help='Usuário do banco')
    parser.add_argument('--db-password', default='protecai', help='Senha do banco')
    parser.add_argument('--db-schema', default='protec_ai', help='Schema do banco')
    
    args = parser.parse_args()
    
    # Criar gerador
    generator = ReportGenerator(
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        db_schema=args.db_schema
    )
    
    # Listar relatórios
    if args.list:
        generator.list_available_reports()
        return 0
    
    # Gerar todos
    if args.all:
        try:
            generator.generate_all_reports(formats=args.format)
            return 0
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            return 1
    
    # Gerar específico
    if args.report:
        try:
            generator.generate_report(args.report, formats=args.format)
            return 0
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            return 1
    
    # Sem argumentos: mostrar help
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
