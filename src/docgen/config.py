"""
Configuration management module for DocGen.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console


def check_ollama_availability(console: Console) -> bool:
    """Check if Ollama is installed and running.
    
    Args:
        console: Rich console instance for output.
        
    Returns:
        True if Ollama is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            console.print(f"[green]✅ Ollama найдена: {version}[/green]")
            return True
        else:
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    except Exception:
        return False


def show_ollama_installation_message(console: Console) -> None:
    """Show beautiful Ollama installation message.
    
    Args:
        console: Rich console instance for output.
    """
    from rich.panel import Panel
    
    message = """
[bold red]❌ Ollama не найдена![/bold red]

Для работы DocGen нужна программа Ollama.

[bold cyan]📥 Скачать бесплатно:[/bold cyan] [link=https://ollama.com]https://ollama.com[/link]

После установки перезапустите команду.
"""
    
    console.print(Panel(
        message,
        title="[bold red]🚫 Отсутствует зависимость[/bold red]",
        border_style="red"
    ))


class ConfigManager:
    """Manages DocGen configuration and model status."""
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize config manager.
        
        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()
        self.config_file = Path("config.json")
    
    def get_installed_models(self) -> Set[str]:
        """Get list of installed Ollama models.
        
        Returns:
            Set of installed model names.
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse ollama list output
                installed = set()
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        model_name = line.split(':')[0].strip()
                        installed.add(model_name)
                return installed
            else:
                return set()
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return set()
        except Exception:
            return set()
    
    def load_config(self) -> Optional[Dict]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary or None if not found/invalid.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            if self.console:
                self.console.print(f"[yellow]⚠️ Не удалось загрузить конфигурацию: {e}[/yellow]")
        return None
    
    def save_config(self, config: Dict) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.console:
                self.console.print(f"[red]❌ Ошибка сохранения конфигурации: {e}[/red]")
    
    def update_last_used_model(self, model: str) -> None:
        """Update last used model in configuration.
        
        Args:
            model: Model key that was used.
        """
        config = self.load_config() or {}
        config["last_used_model"] = model
        config["last_updated"] = str(Path.cwd())
        self.save_config(config)
    
    def get_last_used_model(self) -> Optional[str]:
        """Get last used model from configuration.
        
        Returns:
            Last used model key or None.
        """
        config = self.load_config()
        if config:
            return config.get("last_used_model")
        return None
    
    def get_model_status(self) -> Dict[str, Dict]:
        """Get status of all available models.
        
        Returns:
            Dictionary with model status information.
        """
        installed_models = self.get_installed_models()
        last_used = self.get_last_used_model()
        
        model_status = {}
        for model_key, model_info in {
            "tiny": {"name": "tinyllama:1.1b", "size": "0.6 GB", "desc": "Быстро"},
            "medium": {"name": "gemma2:2b", "size": "1.6 GB", "desc": "Баланс"},
            "large": {"name": "qwen3:8b", "size": "5.2 GB", "desc": "Качество"},
        }.items():
            model_status[model_key] = {
                "installed": model_info["name"] in installed_models,
                "last_used": model_key == last_used,
                **model_info
            }
        
        return model_status
