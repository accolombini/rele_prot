"""Módulo de escaneamento e rastreamento de arquivos PDF do sistema.

Este módulo fornece funcionalidades para identificar arquivos PDF não processados,
manter registro de arquivos já processados e gerenciar o ciclo de vida do processamento
de documentos de configuração de relés.

O registro de arquivos processados é mantido em formato JSON, permitindo rastreamento
persistente entre execuções do sistema.

Exemplo:
    >>> from src.python.utils.file_scanner import FileScanner
    >>> scanner = FileScanner()
    >>> summary = scanner.get_scan_summary()
    >>> print(f"PDFs pendentes: {summary['unprocessed_count']}")

Attributes:
    pdf_dir (Path): Diretório raiz onde residem os arquivos PDF
    registry_file (Path): Arquivo JSON com registro de processamento
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import shutil


class FileScanner:
    """Gerenciador de escaneamento e rastreamento de arquivos PDF.
    
    Esta classe encapsula a lógica de descoberta de arquivos PDF no sistema,
    mantendo um registro persistente de quais arquivos já foram processados
    e fornecendo métodos para consultar status e estatísticas.
    
    Attributes:
        pdf_dir (Path): Caminho do diretório de entrada de PDFs
        registry_file (Path): Caminho do arquivo de registro JSON
    """
    
    def __init__(
        self,
        pdf_dir: str = 'inputs/pdf',
        registry_file: str = 'inputs/registry/processed_files.json'
    ) -> None:
        """Inicializa o scanner de arquivos PDF.
        
        Configura os caminhos de trabalho e cria as estruturas de diretórios
        necessárias caso ainda não existam.
        
        Args:
            pdf_dir: Caminho do diretório contendo os arquivos PDF (padrão: 'inputs/pdf')
            registry_file: Caminho do arquivo de registro JSON (padrão: 'inputs/registry/processed_files.json')
        """
        self.pdf_dir = Path(pdf_dir)
        self.registry_file = Path(registry_file)
        
        # Criar diretórios se não existirem
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_all_pdfs(self) -> List[Path]:
        """Retorna lista de todos os arquivos PDF no diretório de entrada.
        
        Varre o diretório configurado e identifica todos os arquivos com
        extensão .pdf, retornando-os em ordem alfabética.
        
        Returns:
            Lista ordenada de objetos Path representando os arquivos PDF encontrados.
            Retorna lista vazia se o diretório não existir.
        """
        if not self.pdf_dir.exists():
            return []
        
        return sorted([
            f for f in self.pdf_dir.glob('*.pdf')
            if f.is_file()
        ])
    
    def get_processed_files(self) -> Set[str]:
        """Retorna conjunto de nomes de arquivos já processados pelo sistema.
        
        Lê o arquivo de registro JSON e extrai os nomes dos arquivos que já
        foram processados anteriormente. Retorna conjunto vazio em caso de
        arquivo inexistente ou erro de leitura.
        
        Returns:
            Conjunto (set) contendo nomes dos arquivos já processados.
            Retorna conjunto vazio se registro não existir ou estiver corrompido.
        """
        if not self.registry_file.exists():
            return set()
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_files', []))
        except (json.JSONDecodeError, IOError):
            return set()
    
    def get_unprocessed_pdfs(self) -> List[Path]:
        """Identifica arquivos PDF que ainda não foram processados.
        
        Compara a lista de todos os PDFs disponíveis com o registro de
        arquivos processados, retornando apenas aqueles pendentes de processamento.
        
        Returns:
            Lista de objetos Path dos arquivos PDF ainda não processados.
        """
        all_pdfs = self.get_all_pdfs()
        processed = self.get_processed_files()
        
        return [
            pdf for pdf in all_pdfs
            if pdf.name not in processed
        ]
    
    def mark_as_processed(self, pdf_file: Path) -> None:
        """Registra um arquivo PDF como processado no sistema.
        
        Adiciona o nome do arquivo ao registro de processamento e persiste
        a informação em arquivo JSON, incluindo timestamp da operação.
        
        Args:
            pdf_file: Objeto Path do arquivo a ser marcado como processado.
            
        Raises:
            IOError: Se houver erro ao escrever no arquivo de registro.
        """
        processed = self.get_processed_files()
        processed.add(pdf_file.name)
        
        data = {
            'processed_files': sorted(list(processed)),
            'last_update': datetime.now().isoformat()
        }
        
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_scan_summary(self) -> Dict[str, Any]:
        """Retorna resumo estatístico do escaneamento de arquivos.
        
        Consolida informações sobre totais de arquivos, processados e pendentes,
        além de listar os nomes dos arquivos ainda não processados.
        
        Returns:
            Dicionário contendo:
                - total_pdfs (int): Total de arquivos PDF encontrados
                - processed_count (int): Quantidade de arquivos já processados
                - unprocessed_count (int): Quantidade de arquivos pendentes
                - unprocessed_files (List[str]): Nomes dos arquivos pendentes
                - pdf_directory (str): Caminho absoluto do diretório de PDFs
        """
        all_pdfs = self.get_all_pdfs()
        unprocessed = self.get_unprocessed_pdfs()
        processed = self.get_processed_files()
        
        return {
            'total_pdfs': len(all_pdfs),
            'processed_count': len(processed),
            'unprocessed_count': len(unprocessed),
            'unprocessed_files': [pdf.name for pdf in unprocessed],
            'pdf_directory': str(self.pdf_dir.absolute())
        }
    
    def get_pdf_info(self, pdf_file: Path) -> Dict[str, Any]:
        """Retorna metadados e informações de um arquivo PDF específico.
        
        Consulta o sistema de arquivos e extrai informações relevantes
        como tamanho, data de modificação e caminho completo.
        
        Args:
            pdf_file: Objeto Path do arquivo PDF a ser inspecionado.
            
        Returns:
            Dicionário contendo:
                - name (str): Nome do arquivo
                - size_bytes (int): Tamanho em bytes
                - size_mb (float): Tamanho em megabytes (arredondado)
                - modified (str): Data/hora de modificação formatada
                - path (str): Caminho absoluto do arquivo
                
        Raises:
            OSError: Se houver erro ao acessar as propriedades do arquivo.
        """
        stats = pdf_file.stat()
        
        return {
            'name': pdf_file.name,
            'size_bytes': stats.st_size,
            'size_mb': round(stats.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M'),
            'path': str(pdf_file.absolute())
        }
    
    def clear_registry(self) -> None:
        """Remove todos os registros de arquivos processados do sistema.
        
        Deleta completamente o arquivo de registro, permitindo que todos
        os arquivos sejam considerados não processados novamente.
        Operação útil para reprocessamento completo do sistema.
        
        Note:
            Esta operação é irreversível. Considere usar backup_registry()
            antes de executar este método.
        """
        if self.registry_file.exists():
            self.registry_file.unlink()
    
    def backup_registry(self) -> Optional[Path]:
        """Cria cópia de segurança do arquivo de registro atual.
        
        Gera um backup timestamped do arquivo de registro de processamento,
        permitindo recuperação em caso de necessidade.
        
        Returns:
            Objeto Path do arquivo de backup criado.
            Retorna None se o arquivo de registro não existir.
            
        Raises:
            IOError: Se houver erro ao criar o arquivo de backup.
            
        Example:
            >>> scanner = FileScanner()
            >>> backup_path = scanner.backup_registry()
            >>> print(f"Backup criado em: {backup_path}")
        """
        if not self.registry_file.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.registry_file.parent / f'backup_{timestamp}.json'
        
        shutil.copy2(self.registry_file, backup_file)
        
        return backup_file
