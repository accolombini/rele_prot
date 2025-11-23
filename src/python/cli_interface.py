#!/usr/bin/env python3
"""
Interface CLI para Sistema de Proteção PETROBRAS
Pipeline de Processamento de Relés

Usa Rich para interface moderna e colorida.
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm, IntPrompt

from src.python.utils.database_stats import DatabaseStats
from src.python.utils.file_scanner import FileScanner
from src.python.reporters.report_generator import ReportGenerator
from src.python.main import ProtecAIPipeline


class ProtecAICLI:
    """Interface CLI para o sistema de proteção"""
    
    def __init__(self):
        """Inicializa componentes do sistema"""
        self.console = Console()
        self.db_stats = DatabaseStats()
        self.file_scanner = FileScanner()
        self.report_gen = ReportGenerator()
    
    def clear_screen(self):
        """Limpa a tela"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        """Imprime cabeçalho do sistema"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold white]🔌 SISTEMA DE PROTEÇÃO PETROBRAS[/bold white]\n"
            "[white]Pipeline de Processamento de Relés[/white]",
            border_style="cyan"
        ))
    
    def print_status_bar(self):
        """Imprime barra de status"""
        try:
            db_online = self.db_stats.check_connection()
            total_relays = self.db_stats.get_total_relays() if db_online else 0
            
            status = "[green]✓ Online[/green]" if db_online else "[red]✗ Offline[/red]"
            
            self.console.print(
                f"\n[cyan]Status:[/cyan] {total_relays} relés processados | Database: {status}\n"
            )
        except Exception:
            self.console.print("[yellow]⚠ Não foi possível conectar ao banco de dados[/yellow]\n")
    
    def show_main_menu(self):
        """Exibe menu principal e aguarda escolha"""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_status_bar()
            
            self.console.print("\n[bold cyan]MENU PRINCIPAL[/bold cyan]")
            self.console.print("[cyan]" + "=" * 70 + "[/cyan]")
            self.console.print("  [bold cyan]1.[/bold cyan] [white]Executar Pipeline[/white] [dim](processar novos PDFs)[/dim]")
            self.console.print("  [bold cyan]2.[/bold cyan] [white]Gerar Relatorios[/white]")
            self.console.print("  [bold cyan]3.[/bold cyan] [white]Status do Sistema[/white]")
            self.console.print("  [bold cyan]0.[/bold cyan] [white]Sair[/white]")
            self.console.print("[cyan]" + "=" * 70 + "[/cyan]\n")
            
            choice = Prompt.ask(
                "[bold]Escolha uma opcao[/bold]", 
                choices=["0", "1", "2", "3"], 
                default="1",
                show_choices=False
            )
            
            if choice == '1':
                self.menu_executar_pipeline()
            elif choice == '2':
                self.menu_gerar_relatorios()
            elif choice == '3':
                self.menu_status_sistema()
            elif choice == '0':
                if Confirm.ask("\n[yellow]Deseja realmente sair?[/yellow]", default=True):
                    self.console.print("\n[green]OK - Encerrando sistema...[/green]\n")
                    break
    
    def menu_executar_pipeline(self):
        """Menu para executar pipeline"""
        self.clear_screen()
        self.print_header()
        self.console.print(Panel("[bold cyan]🔄 EXECUTAR PIPELINE[/bold cyan]", border_style="cyan"))
        
        # Escanear arquivos
        summary = self.file_scanner.get_scan_summary()
        
        self.console.print(f"\n📁 Diretório: [cyan]{summary['pdf_directory']}[/cyan]")
        self.console.print(f"📊 Total de PDFs: [cyan]{summary['total_pdfs']}[/cyan]")
        self.console.print(f"✅ Já processados: [green]{summary['processed_count']}[/green]")
        self.console.print(f"⏳ Pendentes: [yellow]{summary['unprocessed_count']}[/yellow]\n")
        
        if summary['unprocessed_count'] == 0:
            self.console.print("[green]✓ Nenhum arquivo novo para processar![/green]")
            Prompt.ask("\n[yellow]Pressione ENTER para voltar[/yellow]", default="")
            return
        
        # Listar arquivos pendentes
        self.console.print("[bold]Arquivos pendentes:[/bold]")
        for i, filename in enumerate(summary['unprocessed_files'][:5], 1):
            self.console.print(f"  {i}. {filename}")
        
        if summary['unprocessed_count'] > 5:
            self.console.print(f"  ... e mais {summary['unprocessed_count'] - 5} arquivo(s)")
        
        if Confirm.ask(f"\n[bold]Deseja processar estes arquivos?[/bold]", default=True):
            self.console.print("\n[cyan]⏳ Processando pipeline... (isso pode demorar alguns minutos)[/cyan]\n")
            
            try:
                # Executar pipeline
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task("[cyan]Executando pipeline...", total=None)
                    
                    pipeline = ProtecAIPipeline()
                    pipeline.run()
                    
                    progress.update(task, completed=True)
                
                self.console.print(f"\n[green]✓ Pipeline executado com sucesso![/green]")
                self.console.print(f"[green]✓ {summary['unprocessed_count']} arquivo(s) processado(s)[/green]")
                
                # Atualizar estatísticas
                self.print_status_bar()
                
            except Exception as e:
                self.console.print(f"\n[red]✗ Erro ao executar pipeline: {str(e)}[/red]")
            
            Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
        else:
            self.console.print("\n[yellow]✗ Operação cancelada[/yellow]")
            Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
    
    def menu_gerar_relatorios(self):
        """Menu para gerar relatórios"""
        self.clear_screen()
        self.print_header()
        self.console.print(Panel("[bold cyan]GERAR RELATORIOS[/bold cyan]", border_style="cyan"))
        
        self.console.print("\n[bold]Escolha o tipo de geracao:[/bold]")
        self.console.print("  [bold cyan]1.[/bold cyan] [white]Gerar TODOS os relatorios[/white] [dim](REL01-REL09)[/dim]")
        self.console.print("  [bold cyan]2.[/bold cyan] [white]Selecionar relatorios individuais[/white]")
        self.console.print("  [bold cyan]0.[/bold cyan] [white]Voltar[/white]\n")
        
        choice = Prompt.ask(
            "[bold]Opcao[/bold]", 
            choices=["0", "1", "2"], 
            default="1",
            show_choices=False
        )
        
        if choice == '1':
            self.gerar_todos_relatorios()
        elif choice == '2':
            self.selecionar_relatorios()
        elif choice == '0':
            return
    
    def gerar_todos_relatorios(self):
        """Gera todos os 9 relatórios"""
        self.clear_screen()
        self.print_header()
        self.console.print(Panel("[bold cyan]📊 GERANDO TODOS OS RELATÓRIOS[/bold cyan]", border_style="cyan"))
        
        # Escolher formatos
        formatos = self.escolher_formatos()
        
        if not formatos:
            self.console.print("\n[yellow]✗ Nenhum formato selecionado[/yellow]")
            Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
            return
        
        self.console.print(f"\n[cyan]⏳ Gerando 9 relatórios nos formatos: {', '.join(formatos).upper()}[/cyan]\n")
        
        relatorios = ['REL01', 'REL02', 'REL03', 'REL04', 'REL05', 'REL06', 'REL07', 'REL08', 'REL09']
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Processando...", total=len(relatorios))
            
            for rel in relatorios:
                try:
                    progress.update(task, description=f"[cyan]Gerando {rel}...")
                    self.report_gen.generate_report(rel, formats=formatos)
                    progress.advance(task)
                except Exception as e:
                    self.console.print(f"[red]✗ Erro ao gerar {rel}: {str(e)}[/red]")
        
        self.console.print(f"\n[green]✓ Relatórios gerados em: outputs/relatorios/[/green]")
        Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
    
    def selecionar_relatorios(self):
        """Permite selecionar relatórios individuais"""
        self.clear_screen()
        self.print_header()
        self.console.print(Panel("[bold cyan]📊 SELECIONAR RELATÓRIOS[/bold cyan]", border_style="cyan"))
        
        relatorios = {
            '1': ('REL01', 'Fabricantes de Relés'),
            '2': ('REL02', 'Setpoints Críticos'),
            '3': ('REL03', 'Tipos de Relés'),
            '4': ('REL04', 'Relés por Fabricante'),
            '5': ('REL05', 'Funções de Proteção'),
            '6': ('REL06', 'Relatório Completo'),
            '7': ('REL07', 'Relés por Subestação'),
            '8': ('REL08', 'Análise de Tensão'),
            '9': ('REL09', 'Parâmetros Críticos')
        }
        
        self.console.print("\n[bold]Relatórios disponíveis:[/bold]")
        for key, (code, name) in relatorios.items():
            self.console.print(f"  [bold]{key}.[/bold] {code} - {name}")
        
        self.console.print("\n[yellow]Digite os números separados por vírgula (ex: 1,2,5)[/yellow]")
        self.console.print("[yellow]ou 'T' para TODOS, '0' para cancelar[/yellow]\n")
        
        escolha = Prompt.ask("[bold]Relatórios[/bold]", default="T")
        
        if escolha == '0':
            return
        
        # Processar escolha
        if escolha.upper() == 'T':
            codigos = [info[0] for info in relatorios.values()]
        else:
            try:
                numeros = [n.strip() for n in escolha.split(',')]
                codigos = [relatorios[n][0] for n in numeros if n in relatorios]
                
                if not codigos:
                    self.console.print("\n[red]✗ Nenhum relatório válido selecionado[/red]")
                    Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
                    return
            except Exception:
                self.console.print("\n[red]✗ Formato inválido[/red]")
                Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
                return
        
        # Escolher formatos
        formatos = self.escolher_formatos()
        
        if not formatos:
            self.console.print("\n[yellow]✗ Nenhum formato selecionado[/yellow]")
            Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
            return
        
        self.console.print(f"\n[cyan]⏳ Gerando {len(codigos)} relatório(s)...[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Processando...", total=len(codigos))
            
            for codigo in codigos:
                try:
                    progress.update(task, description=f"[cyan]Gerando {codigo}...")
                    self.report_gen.generate_report(codigo, formats=formatos)
                    progress.advance(task)
                except Exception as e:
                    self.console.print(f"[red]✗ Erro ao gerar {codigo}: {str(e)}[/red]")
        
        self.console.print(f"\n[green]✓ Relatórios gerados em: outputs/relatorios/[/green]")
        Prompt.ask("\n[yellow]Pressione ENTER para continuar[/yellow]", default="")
    
    def escolher_formatos(self):
        """Permite escolher formatos de exportação"""
        self.console.print("\n[bold cyan]Escolha os formatos de exportação:[/bold cyan]")
        
        self.console.print("\n[bold]Formatos disponíveis:[/bold]")
        self.console.print("  [bold]1.[/bold] CSV")
        self.console.print("  [bold]2.[/bold] Excel (XLSX)")
        self.console.print("  [bold]3.[/bold] PDF")
        self.console.print("  [bold]4.[/bold] Todos os formatos")
        
        escolha = Prompt.ask("[bold]Formato[/bold]", choices=["1", "2", "3", "4"], default="4")
        
        formatos_map = {
            '1': ['csv'],
            '2': ['xlsx'],
            '3': ['pdf'],
            '4': ['csv', 'xlsx', 'pdf']
        }
        
        return formatos_map.get(escolha, ['csv', 'xlsx', 'pdf'])
    
    def menu_status_sistema(self):
        """Menu para exibir status do sistema"""
        self.clear_screen()
        self.print_header()
        self.console.print(Panel("[bold cyan]📈 STATUS DO SISTEMA[/bold cyan]", border_style="cyan"))
        
        try:
            status = self.db_stats.get_database_status()
            
            # Tabela principal
            table = Table(title="\n[bold]Estatísticas do Banco de Dados[/bold]", 
                         show_header=True, 
                         header_style="bold cyan")
            table.add_column("Métrica", style="white")
            table.add_column("Valor", justify="right", style="green")
            
            table.add_row("Total de Relés", str(status['total_relays']))
            table.add_row("Proteções", str(status['total_protections']))
            table.add_row("Parâmetros", str(status['total_parameters']))
            
            self.console.print(table)
            
            # Fabricantes
            if status['manufacturers']:
                self.console.print("\n[bold]Fabricantes:[/bold]")
                for mfg in status['manufacturers']:
                    abbrev = 'GE' if 'GENERAL' in mfg['name'] else 'SNE' if 'SCHNEIDER' in mfg['name'] else mfg['name'][:3]
                    self.console.print(f"  • {mfg['name']} ({abbrev}): [cyan]{mfg['total_relays']} relés[/cyan]")
            
            # Tipos de relé
            if status['relay_types']:
                self.console.print("\n[bold]Tipos de Relé:[/bold]")
                for rt in status['relay_types']:
                    self.console.print(f"  • {rt['type']}: [cyan]{rt['count']}[/cyan]")
            
            self.console.print(f"\n[dim]Última atualização: {status['timestamp']}[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Erro ao obter estatísticas: {str(e)}[/red]")
        
        Prompt.ask("\n[yellow]Pressione ENTER para voltar[/yellow]", default="")


def main():
    """Função principal"""
    try:
        cli = ProtecAICLI()
        cli.show_main_menu()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]✗ Operação cancelada pelo usuário[/yellow]\n")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[red]✗ Erro fatal: {str(e)}[/red]\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
