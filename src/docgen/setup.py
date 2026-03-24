"""
Interactive setup module for DocGen initial configuration.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .llm import MODEL_MAPPING
from .config import ConfigManager


class SetupManager:
    """Manages initial setup and configuration for DocGen."""
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize setup manager.
        
        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()
        self.config_manager = ConfigManager(console)
    
    def show_model_selection_menu(self) -> str:
        """Show interactive model selection menu.
        
        Returns:
            Selected model key (tiny/medium/large).
        """
        # Get model status
        model_status = self.config_manager.get_model_status()
        last_used = self.config_manager.get_last_used_model()
        
        # Check if any models are installed
        installed_models = [k for k, v in model_status.items() if v["installed"]]
        
        # Create header with last used model
        header = "[bold cyan]DocGen - Выбор AI модели[/bold cyan]\n"
        if last_used:
            last_model_info = MODEL_MAPPING[last_used]
            header += f"[green]Последняя использованная: {last_used} ⭐[/green]\n"
        else:
            header += "[yellow]Первый запуск - нет сохраненной модели[/yellow]\n"
        
        # Create model comparison table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("№", style="cyan", width=4)
        table.add_column("Модель", style="white", width=12)
        table.add_column("Размер", style="yellow", width=10)
        table.add_column("Статус", style="green", width=15)
        
        models_info = []
        for model_key in ["tiny", "medium", "large"]:
            status = model_status[model_key]
            status_icon = "✅" if status["installed"] else "❌"
            status_text = f"{status_icon} {'Установлена' if status['installed'] else 'Не скачана'}"
            
            if model_key == last_used:
                status_text += " ⭐"
            
            models_info.append((
                model_key.replace("tiny", "1").replace("medium", "2").replace("large", "3"),
                model_key,
                status["size"],
                status_text
            ))
        
        for num, model, size, status in models_info:
            table.add_row(num, model, size, status)
        
        # Show warning if no models installed
        if not installed_models:
            self.console.print("[yellow] Ни одна модель не скачана. Рекомендуется начать с medium.[/yellow]\n")
        
        # Display menu
        self.console.print(Panel(header, 
                           title="[bold]🤖 Настройка DocGen[/bold]",
                           border_style="cyan"))
        self.console.print(table)  # Print table directly
        
        # Ask about using last model if available
        if last_used and last_used in installed_models:
            if Confirm.ask(f"\n[cyan]Использовать последнюю модель ({last_used})?[/cyan]", default=True):
                return last_used
        
        # Get user choice
        while True:
            choice = Prompt.ask(
                "\n[cyan]Выберите модель [1-3] (Enter = medium, рекомендуется):[/cyan]",
                choices=["1", "2", "3"],
                default="2"
            )
            
            model_map = {"1": "tiny", "2": "medium", "3": "large"}
            selected_model = model_map[choice]
            
            # Check if model is installed
            if not model_status[selected_model]["installed"]:
                self.console.print(f"[yellow] Модель {selected_model} не установлена. Будет скачана.[/yellow]")
            
            # Confirm selection
            model_info = MODEL_MAPPING[selected_model]
            confirm_msg = (
                f"Вы выбрали модель [bold]{model_info['name']}[/bold] "
                f"({model_info['size_gb']} GB) - {model_info['description']}. "
                "Продолжить?"
            )
            
            if Confirm.ask(confirm_msg, default=True):
                return selected_model
            else:
                self.console.print("[yellow]Выберите другую модель[/yellow]\n")
    
    def download_model(self, model_name: str) -> bool:
        """Download model using ollama pull.
        
        Args:
            model_name: Name of the model to download.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"📥 Скачивание модели {model_name}...", 
                    total=None
                )
                
                result = subprocess.run(
                    ["ollama", "pull", model_name],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode == 0:
                    progress.update(task, description=f"✅ Модель {model_name} успешно загружена")
                    return True
                else:
                    progress.update(task, description=f"❌ Ошибка загрузки модели")
                    self.console.print(f"[red]Error: {result.stderr}[/red]")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Превышено время ожидания загрузки модели[/red]")
            return False
        except FileNotFoundError:
            self.console.print("[red]❌ Ollama не найден. Установите Ollama: https://ollama.ai[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Ошибка при загрузке модели: {e}[/red]")
            return False
    
    def save_config(self, model: str) -> None:
        """Save selected model to config file.
        
        Args:
            model: Selected model key.
        """
        config = {
            "selected_model": model,
            "model_name": MODEL_MAPPING[model]["name"],
            "setup_completed": True
        }
        
        self.config_manager.save_config(config)
        self.config_manager.update_last_used_model(model)
        
        self.console.print(f"[green]✅ Конфигурация сохранена в {self.config_manager.config_file}[/green]")
    
    def load_config(self) -> Optional[Dict]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary or None if not found/invalid.
        """
        return self.config_manager.load_config()
    
    def show_current_config(self) -> None:
        """Show current configuration."""
        config = self.config_manager.load_config()
        if config:
            model = config.get("selected_model", "unknown")
            model_name = config.get("model_name", "unknown")
            self.console.print(f"[green]Текущая модель: {model_name} ({model})[/green]")
        else:
            self.console.print("[yellow]Конфигурация не найдена. Запустите начальную настройку.[/yellow]")
    
    def run_initial_setup(self) -> str:
        """Run initial setup process.
        
        Returns:
            Selected model key.
        """
        self.console.print("""
[bold cyan]🎉 Добро пожаловать в DocGen![/bold cyan]

Это первый запуск. Давайте настроим генерацию документации.
""")
        
        # Show model selection
        selected_model = self.show_model_selection_menu()
        model_name = MODEL_MAPPING[selected_model]["name"]
        
        # Ask about downloading model
        if Confirm.ask(f"\n[cyan]📥 Скачать модель {model_name} через Ollama?[/cyan]", default=True):
            success = self.download_model(model_name)
            if not success:
                self.console.print("[yellow]⚠️ Модель не загружена. Вы можете скачать её позже вручную.[/yellow]")
        
        # Save configuration
        self.save_config(selected_model)
        
        self.console.print(f"""
[bold green]🎉 Настройка завершена![/bold green]

Выбранная модель: [cyan]{model_name}[/cyan]
Теперь вы можете использовать DocGen:
  [yellow]docgen generate --model {selected_model}[/yellow]

Для смены модели используйте:
  [yellow]docgen generate --reconfigure[/yellow]
""")
        
        return selected_model
    
    def show_current_config(self) -> None:
        """Show current configuration."""
        config = self.load_config()
        if config:
            model = config.get("selected_model", "unknown")
            model_name = config.get("model_name", "unknown")
            self.console.print(f"[green]Текущая модель: {model_name} ({model})[/green]")
        else:
            self.console.print("[yellow]Конфигурация не найдена. Запустите начальную настройку.[/yellow]")
