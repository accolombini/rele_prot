#!/usr/bin/env python3
"""Interface de linha de comando para o Sistema de Proteção de Relés.

Este módulo implementa uma interface CLI interativa para operação do sistema
de extração, normalização e análise de dados de relés de proteção elétrica.

A interface permite:
    - Execução do pipeline de processamento de novos arquivos PDF
    - Geração de relatórios analíticos em múltiplos formatos (CSV, Excel, PDF)
    - Visualização de estatísticas e status do sistema
    - Navegação intuitiva via menus numerados

A interface utiliza a biblioteca Rich para formatação visual aprimorada,
incluindo tabelas, painéis, barras de progresso e esquema de cores.

Exemplo de uso:
    $ python src/python/cli_interface.py
    
    ou via script auxiliar:
    
    $ ./run_cli.sh

Attributes:
    ROOT_DIR (Path): Diretório raiz do projeto
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm

from src.python.utils.database_stats import DatabaseStats
from src.python.utils.file_scanner import FileScanner
from src.python.reporters.report_generator import ReportGenerator
from src.python.main import ProtecAIPipeline


class ProtecAICLI:
    """Interface de linha de comando para o Sistema de Proteção de Relés.
    
    Esta classe orquestra a interação do usuário com o sistema através de menus
    interativos, gerenciando a execução do pipeline de processamento e geração
    de relatórios.
    
    Attributes:
        console (Console): Instância Rich Console para saída formatada
        db_stats (DatabaseStats): Cliente para consultas de estatísticas
        file_scanner (FileScanner): Gerenciador de arquivos PDF
        report_gen (ReportGenerator): Gerador de relatórios do sistema
    """
    
    def __init__(self) -> None:
        """Inicializa a interface CLI e seus componentes.
        
        Cria instâncias dos componentes necessários para operação do sistema,
        incluindo gerenciadores de banco de dados, arquivos e relatórios.
        """
        self.console = Console()
        self.db_stats = DatabaseStats()
        self.file_scanner = FileScanner()
        self.report_gen = ReportGenerator()
    
    def clear_screen(self) -> None:
        """Limpa o conteúdo da tela do terminal.
        
        Executa comando apropriado ao sistema operacional para limpar
        a tela, preparando para nova renderização de interface.
        """
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self) -> None:
        """Renderiza o cabeçalho visual do sistema.
        
        Exibe painel formatado contendo o título do sistema e identificação
        do módulo em execução.
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold white]🔌 SISTEMA DE PROTEÇÃO PETROBRAS[/bold white]\n"
            "[white]Pipeline de Processamento de Relés[/white]",
            border_style="cyan"
        ))
    
    def print_status_bar(self) -> None:
        """Exibe barra de status com métricas do sistema.
        
        Renderiza informações sobre conectividade com banco de dados e
        estatísticas básicas como total de relés processados.
        
        Em caso de falha na conexão, exibe mensagem de alerta ao usuário.
        """
        try:
            db_online = self.db_stats.check_connection()
            total_relays = self.db_stats.get_total_relays() if db_online else 0
            
            status = "[green]✓ Online[/green]" if db_online else "[red]✗ Offline[/red]"
            
            self.console.print(
                f"\n[cyan]Status:[/cyan] {total_relays} relés processados | Database: {status}\n"
            )
        except Exception:
            self.console.print("[yellow]⚠ Não foi possível conectar ao banco de dados[/yellow]\n")
    
    def show_main_menu(self) -> None:
        """Exibe menu principal e processa navegação do usuário.
        
        Renderiza menu principal com opções de operação do sistema,
        captura entrada do usuário e despacha para o submenu apropriado.
        
        Loop continua até que o usuário selecione a opção de saída.
        
        Opções disponíveis:
            1 - Executar Pipeline de processamento
            2 - Gerar Relatórios analíticos
            3 - Visualizar Status do Sistema
            0 - Sair da aplicação
        """
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
    
    def menu_executar_pipeline(self) -> None:
        """Submenu de execução do pipeline de processamento.
        
        Escaneia diretório de entrada, identifica arquivos PDF pendentes
        de processamento e oferece opção de executar pipeline completo.
        
        O pipeline inclui:
            - Extração de dados de PDFs e arquivos .S40
            - Normalização de dados para formato 3FN
            - Carga no banco de dados PostgreSQL
        
        Exibe progressão durante execução e relatório de sucesso ao final.
        """
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
    
    def menu_gerar_relatorios(self) -> None:
        """Submenu de geração de relatórios analíticos.
        
        Oferece opções para geração de relatórios do sistema:
            - Geração em lote de todos os 9 relatórios disponíveis
            - Seleção individual de relatórios específicos
        
        Relatórios podem ser exportados em múltiplos formatos (CSV, Excel, PDF).
        """
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
    
    def gerar_todos_relatorios(self) -> None:
        """Gera todos os nove relatórios analíticos do sistema.
        
        Executa geração em lote de todos os relatórios definidos (REL01-REL09),
        permitindo ao usuário escolher os formatos de exportação desejados.
        
        Relatórios gerados:
            REL01 - Fabricantes de Relés
            REL02 - Setpoints Críticos
            REL03 - Tipos de Relés
            REL04 - Relés por Fabricante
            REL05 - Funções de Proteção
            REL06 - Relatório Completo
            REL07 - Relés por Subestação
            REL08 - Análise de Tensão
            REL09 - Parâmetros Críticos
        
        Exibe barra de progresso durante execução.
        """
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
    
    def selecionar_relatorios(self) -> None:
        """Permite seleção interativa de relatórios individuais.
        
        Exibe lista numerada de todos os relatórios disponíveis e permite
        ao usuário selecionar um subconjunto para geração.
        
        Entrada aceita:
            - Números separados por vírgula (ex: '1,2,5')
            - 'T' para selecionar todos
            - '0' para cancelar
        
        Após seleção, solicita escolha de formatos de exportação.
        """
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
    
    def escolher_formatos(self) -> List[str]:
        """Solicita ao usuário escolha de formatos de exportação.
        
        Oferece opções de formato para geração dos relatórios:
            1 - CSV (valores separados por vírgula)
            2 - Excel (arquivo .xlsx)
            3 - PDF (documento formatado)
            4 - Todos os formatos acima
        
        Returns:
            Lista de strings com formatos selecionados (['csv', 'xlsx', 'pdf']).
            Padrão retorna todos os formatos se nenhum for especificado.
        """
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
    
    def menu_status_sistema(self) -> None:
        """Submenu de visualização de estatísticas e status do sistema.
        
        Consulta banco de dados e exibe métricas consolidadas incluindo:
            - Totais de relés, funções de proteção e parâmetros
            - Distribuição por fabricante
            - Distribuição por tipo de relé
            - Distribuição por classe de tensão
        
        Informações são apresentadas em tabelas formatadas.
        
        Raises:
            Exception: Captura e exibe erros de conexão com banco de dados.
        """
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


def main() -> None:
    """Ponto de entrada principal da aplicação CLI.
    
    Inicializa a interface de linha de comando e gerencia o loop principal
    de interação com o usuário. Trata interrupções de teclado e exceções
    não capturadas de forma apropriada.
    
    Exits:
        0: Saída normal ou interrupção por usuário (Ctrl+C)
        1: Erro fatal durante execução
    
    Raises:
        KeyboardInterrupt: Capturada e tratada como saída limpa
        Exception: Capturada e exibida como erro fatal
    """
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
