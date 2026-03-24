"""
Caching functionality for documentation generation.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console


class DocumentationCache:
    """Cache system for documentation generation to avoid regenerating unchanged code."""
    
    def __init__(self, cache_dir: Optional[Path] = None, console: Optional[Console] = None) -> None:
        """Initialize the cache system.
        
        Args:
            cache_dir: Directory for cache files (default: .docgen_cache).
            console: Rich console instance for output.
        """
        self.console = console or Console()
        self.cache_dir = cache_dir or Path(".docgen_cache")
        self.cache_file = self.cache_dir / "cache.json"
        self.cache_data: Dict[str, Dict] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache data from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            if self.console:
                self.console.print(f"[yellow]Warning: Could not load cache: {e}[/yellow]")
            self.cache_data = {}
    
    def _save_cache(self) -> None:
        """Save cache data to file."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
        except IOError as e:
            if self.console:
                self.console.print(f"[yellow]Warning: Could not save cache: {e}[/yellow]")
    
    def _get_files_hash(self, files: List[Tuple[Path, str]]) -> str:
        """Generate hash for file contents.
        
        Args:
            files: List of (file_path, content) tuples.
            
        Returns:
            SHA256 hash of all file contents.
        """
        hasher = hashlib.sha256()
        
        # Sort files by path for consistent hashing
        sorted_files = sorted(files, key=lambda x: str(x[0]))
        
        for file_path, content in sorted_files:
            hasher.update(str(file_path).encode('utf-8'))
            hasher.update(content.encode('utf-8'))
        
        return hasher.hexdigest()
    
    def _get_cache_key(self, project_path: Path, language: str, template: str, 
                      model: str, max_tokens: int, temperature: float) -> str:
        """Generate cache key for given parameters.
        
        Args:
            project_path: Path to project.
            language: Documentation language.
            template: Template type.
            model: LLM model.
            max_tokens: Maximum tokens.
            temperature: Temperature.
            
        Returns:
            Cache key string.
        """
        key_data = {
            "project_path": str(project_path.resolve()),
            "language": language,
            "template": template,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_json.encode('utf-8')).hexdigest()
    
    def get_cached_documentation(self, project_path: Path, files: List[Tuple[Path, str]],
                                language: str, template: str, model: str, 
                                max_tokens: int, temperature: float) -> Optional[str]:
        """Get cached documentation if available and valid.
        
        Args:
            project_path: Path to project.
            files: List of (file_path, content) tuples.
            language: Documentation language.
            template: Template type.
            model: LLM model.
            max_tokens: Maximum tokens.
            temperature: Temperature.
            
        Returns:
            Cached documentation or None if not available/invalid.
        """
        cache_key = self._get_cache_key(project_path, language, template, model, max_tokens, temperature)
        files_hash = self._get_files_hash(files)
        
        if cache_key in self.cache_data:
            cache_entry = self.cache_data[cache_key]
            
            # Check if files have changed
            if cache_entry.get("files_hash") == files_hash:
                if self.console:
                    self.console.print("[green]✓ Using cached documentation (no changes detected)[/green]")
                return cache_entry.get("documentation")
        
        return None
    
    def cache_documentation(self, project_path: Path, files: List[Tuple[Path, str]],
                           documentation: str, language: str, template: str, 
                           model: str, max_tokens: int, temperature: float) -> None:
        """Cache generated documentation.
        
        Args:
            project_path: Path to project.
            files: List of (file_path, content) tuples.
            documentation: Generated documentation.
            language: Documentation language.
            template: Template type.
            model: LLM model.
            max_tokens: Maximum tokens.
            temperature: Temperature.
        """
        cache_key = self._get_cache_key(project_path, language, template, model, max_tokens, temperature)
        files_hash = self._get_files_hash(files)
        
        self.cache_data[cache_key] = {
            "project_path": str(project_path.resolve()),
            "language": language,
            "template": template,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "files_hash": files_hash,
            "documentation": documentation,
            "timestamp": time.time(),
        }
        
        self._save_cache()
        
        if self.console:
            self.console.print("[blue]💾 Documentation cached for future use[/blue]")
    
    def clear_cache(self) -> None:
        """Clear all cached documentation."""
        self.cache_data = {}
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.console:
                self.console.print("[green]✓ Cache cleared[/green]")
        except IOError as e:
            if self.console:
                self.console.print(f"[yellow]Warning: Could not clear cache: {e}[/yellow]")
    
    def get_cache_info(self) -> Dict:
        """Get information about cache status.
        
        Returns:
            Dictionary with cache statistics.
        """
        total_entries = len(self.cache_data)
        total_size = self.cache_file.stat().st_size if self.cache_file.exists() else 0
        
        return {
            "total_entries": total_entries,
            "cache_file": str(self.cache_file),
            "cache_size_bytes": total_size,
            "cache_size_mb": round(total_size / (1024 * 1024), 2),
        }
