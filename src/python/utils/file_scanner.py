"""
Módulo para escanear e identificar arquivos PDF não processados.
Compara PDFs em inputs/pdf/ com registro de arquivos já processados.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime


class FileScanner:
    """Classe para escanear e gerenciar arquivos PDF"""
    
    def __init__(
        self,
        pdf_dir: str = 'inputs/pdf',
        registry_file: str = 'inputs/registry/processed_files.json'
    ):
        """
        Inicializa scanner de arquivos
        
        Args:
            pdf_dir: Diretório com PDFs de entrada
            registry_file: Arquivo JSON com registro de processados
        """
        self.pdf_dir = Path(pdf_dir)
        self.registry_file = Path(registry_file)
        
        # Criar diretórios se não existirem
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_all_pdfs(self) -> List[Path]:
        """
        Retorna lista de todos os PDFs no diretório
        
        Returns:
            Lista de Path objects dos PDFs encontrados
        """
        if not self.pdf_dir.exists():
            return []
        
        return sorted([
            f for f in self.pdf_dir.glob('*.pdf')
            if f.is_file()
        ])
    
    def get_processed_files(self) -> Set[str]:
        """
        Retorna conjunto de nomes de arquivos já processados
        
        Returns:
            Set com nomes dos arquivos processados
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
        """
        Retorna lista de PDFs que ainda não foram processados
        
        Returns:
            Lista de Path objects dos PDFs não processados
        """
        all_pdfs = self.get_all_pdfs()
        processed = self.get_processed_files()
        
        return [
            pdf for pdf in all_pdfs
            if pdf.name not in processed
        ]
    
    def mark_as_processed(self, pdf_file: Path) -> None:
        """
        Marca um arquivo PDF como processado
        
        Args:
            pdf_file: Path do arquivo a marcar como processado
        """
        processed = self.get_processed_files()
        processed.add(pdf_file.name)
        
        data = {
            'processed_files': sorted(list(processed)),
            'last_update': datetime.now().isoformat()
        }
        
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_scan_summary(self) -> Dict[str, any]:
        """
        Retorna resumo do escaneamento
        
        Returns:
            Dict com estatísticas de arquivos
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
    
    def get_pdf_info(self, pdf_file: Path) -> Dict[str, any]:
        """
        Retorna informações sobre um arquivo PDF
        
        Args:
            pdf_file: Path do arquivo PDF
            
        Returns:
            Dict com informações do arquivo
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
        """Remove todos os registros de arquivos processados"""
        if self.registry_file.exists():
            self.registry_file.unlink()
    
    def backup_registry(self) -> Path:
        """
        Cria backup do registro atual
        
        Returns:
            Path do arquivo de backup criado
        """
        if not self.registry_file.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.registry_file.parent / f'backup_{timestamp}.json'
        
        import shutil
        shutil.copy2(self.registry_file, backup_file)
        
        return backup_file
