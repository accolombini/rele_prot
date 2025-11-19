"""
File Manager utility
Handles file operations, hashing, and registry management
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileManager:
    """Manages file operations and processing registry"""
    
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load processing registry from JSON file"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"processed_files": {}, "last_updated": None}
    
    def _save_registry(self):
        """Save processing registry to JSON file"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if file was already processed"""
        file_hash = self.calculate_file_hash(file_path)
        return file_hash in self.registry["processed_files"]
    
    def mark_file_processed(self, file_path: str, metadata: Optional[Dict[str, Any]] = None):
        """Mark file as processed in registry"""
        file_hash = self.calculate_file_hash(file_path)
        self.registry["processed_files"][file_hash] = {
            "file_path": str(file_path),
            "file_name": Path(file_path).name,
            "processed_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save_registry()
    
    def get_files_by_extension(self, directory: str, extension: str) -> List[Path]:
        """Get all files with specific extension from directory"""
        directory_path = Path(directory)
        if not directory_path.exists():
            return []
        
        pattern = f"**/*{extension}" if not extension.startswith('*') else f"**/{extension}"
        return list(directory_path.glob(pattern))
    
    def get_pdf_files(self, directory: str) -> List[Path]:
        """Get all PDF files from directory"""
        return self.get_files_by_extension(directory, ".pdf")
    
    def get_s40_files(self, directory: str) -> List[Path]:
        """Get all .S40 files from directory"""
        return self.get_files_by_extension(directory, ".S40")
    
    def ensure_output_directory(self, directory: str):
        """Ensure output directory exists"""
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path.absolute()),
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "hash": self.calculate_file_hash(file_path)
        }
    
    def backup_registry(self):
        """Create backup of registry file"""
        if self.registry_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.registry_path.parent / f"{self.registry_path.stem}_backup_{timestamp}.json"
            
            with open(self.registry_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            return str(backup_path)
        return None
