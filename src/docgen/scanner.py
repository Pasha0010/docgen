"""
File scanner module for discovering and reading Python files.
"""

import os
from pathlib import Path
from typing import List, Generator, Optional
import fnmatch

from rich.console import Console
from rich.progress import Progress, TaskID


class FileScanner:
    """Scanner for discovering and reading Python files in a directory."""
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the file scanner.
        
        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()
        self.ignore_patterns = {
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "node_modules",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "build",
            "dist",
            "*.egg-info",
        }
    
    def is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored.
        
        Args:
            path: Path to check.
            
        Returns:
            True if path should be ignored, False otherwise.
        """
        path_str = str(path)
        
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern) or pattern in path_str:
                return True
        
        return False
    
    def find_python_files(self, directory: Path, progress: Optional[Progress] = None, 
                         task_id: Optional[TaskID] = None) -> List[Path]:
        """Find all Python files in the given directory.
        
        Args:
            directory: Directory to scan.
            progress: Optional progress bar.
            task_id: Optional task ID for progress tracking.
            
        Returns:
            List of Python file paths.
            
        Raises:
            ValueError: If directory doesn't exist.
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        python_files = []
        total_files = 0
        
        # First pass: count total files for progress
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.is_ignored(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not self.is_ignored(file_path) and file.endswith('.py'):
                    total_files += 1
        
        if progress and task_id:
            progress.update(task_id, total=total_files)
        
        # Second pass: collect files
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.is_ignored(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if not self.is_ignored(file_path) and file.endswith('.py'):
                    python_files.append(file_path)
                    
                    if progress and task_id:
                        progress.advance(task_id)
        
        return python_files
    
    def read_file(self, file_path: Path) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            File contents as string.
            
        Raises:
            IOError: If file cannot be read.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            self.console.print(f"[yellow]Warning: Could not read {file_path} as UTF-8[/yellow]")
            return ""
        except IOError as e:
            raise IOError(f"Could not read file {file_path}: {e}")
    
    def read_files(self, file_paths: List[Path], progress: Optional[Progress] = None,
                   task_id: Optional[TaskID] = None) -> List[tuple[Path, str]]:
        """Read multiple files and return their contents.
        
        Args:
            file_paths: List of file paths to read.
            progress: Optional progress bar.
            task_id: Optional task ID for progress tracking.
            
        Returns:
            List of tuples containing (file_path, content).
        """
        results = []
        
        if progress and task_id:
            progress.update(task_id, total=len(file_paths))
        
        for file_path in file_paths:
            try:
                content = self.read_file(file_path)
                results.append((file_path, content))
            except IOError as e:
                self.console.print(f"[red]Error reading {file_path}: {e}[/red]")
            
            if progress and task_id:
                progress.advance(task_id)
        
        return results
