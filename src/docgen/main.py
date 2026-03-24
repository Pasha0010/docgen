"""
Main CLI interface for DocGen.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

from .scanner import FileScanner
from .llm import LLMFactory, get_model_info
from .prompt import get_system_prompt, get_user_prompt
from .exporter import DocumentationExporter
from .cache import DocumentationCache
from .setup import SetupManager
from .config import check_ollama_availability, show_ollama_installation_message


# Load environment variables
load_dotenv()

# Create Typer app
app = typer.Typer(
    name="docgen",
    help="AI-powered technical documentation generator for Python projects",
    no_args_is_help=True,
)

# Rich console
console = Console()


@app.command()
def generate(
    path: str = typer.Argument(
        ".",
        help="Path to the Python project directory to document",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path (default: README.md in project directory)",
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang", "-l",
        help="Documentation language (en/ru). Alias for --language",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        help="Documentation language (en/ru)",
    ),
    template: str = typer.Option(
        "basic",
        "--template", "-t",
        help="Documentation template (basic/detailed/api-only)",
    ),
    format_type: str = typer.Option(
        "markdown",
        "--format", "-f",
        help="Output format (markdown/html)",
    ),
    model: str = typer.Option(
        "medium",
        "--model", "-m",
        help="Model size: tiny (fast, 0.6GB), medium (balanced, 1.6GB), large (quality, 5.2GB)",
    ),
    max_tokens: int = typer.Option(
        4096,
        "--max-tokens",
        help="Maximum tokens to generate",
    ),
    temperature: float = typer.Option(
        0.7,
        "--temperature",
        help="Sampling temperature (0.0-1.0)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching and force regeneration",
    ),
    reconfigure: bool = typer.Option(
        False,
        "--reconfigure",
        help="Reconfigure model selection",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Generate documentation for a Python project."""
    
    try:
        # Check Ollama availability first
        if not check_ollama_availability(console):
            show_ollama_installation_message(console)
            raise typer.Exit(1)
        
        # Handle language parameter (backward compatibility)
        if lang is not None and language is not None:
            console.print("[red]Ошибка: Нельзя указывать одновременно --lang и --language[/red]")
            console.print("[yellow]Совет: Используйте --lang, это короче[/yellow]")
            raise typer.Exit(1)
        
        # Use --lang if provided, otherwise --language, otherwise default to 'en'
        final_language = lang or language or "en"
        
        # Validate language parameter
        if final_language not in ["en", "ru"]:
            console.print(f"[red]Ошибка: Язык должен быть 'en' или 'ru', не '{final_language}'[/red]")
            console.print("[yellow]Доступные языки: en (английский), ru (русский)[/yellow]")
            raise typer.Exit(1)
        
        # Validate template parameter
        if template not in ["basic", "detailed", "api-only"]:
            console.print(f"[red]Ошибка: Шаблон должен быть 'basic', 'detailed', или 'api-only', не '{template}'[/red]")
            console.print("[yellow]Доступные шаблоны:[/yellow]")
            console.print("  - basic: Простой README с основными разделами")
            console.print("  - detailed: Комплексная документация с примерами")
            console.print("  - api-only: Документация только для API")
            raise typer.Exit(1)
        
        # Validate format parameter
        if format_type not in ["markdown", "html"]:
            console.print(f"[red]Ошибка: Формат должен быть 'markdown' или 'html', не '{format_type}'[/red]")
            console.print("[yellow]Доступные форматы: markdown, html[/yellow]")
            raise typer.Exit(1)
        
        # Initialize setup manager
        setup_manager = SetupManager(console)
        
        # Handle reconfiguration
        if reconfigure:
            console.print("[cyan]🔧 Перенастройка модели...[/cyan]")
            model = setup_manager.run_initial_setup()
            model_info = get_model_info(model)
            actual_model_name = model_info["name"]
            model_size = model_info["size_gb"]
            model_description = model_info["description"]
        else:
            # Check for existing configuration
            config = setup_manager.load_config()
            if config and config.get("setup_completed"):
                # Use saved model
                saved_model = config.get("selected_model", "medium")
                if model == "medium":  # Default value, use saved
                    model = saved_model
                
                # Validate saved model
                valid_models = ["tiny", "medium", "large"]
                if model not in valid_models:
                    console.print(f"[red]Error: Saved model '{model}' is invalid[/red]")
                    console.print("[yellow]Running reconfiguration...[/yellow]")
                    model = setup_manager.run_initial_setup()
            else:
                # First run - show setup
                model = setup_manager.run_initial_setup()
        
        # Get model information
        model_info = get_model_info(model)
        actual_model_name = model_info["name"]
        model_size = model_info["size_gb"]
        model_description = model_info["description"]
        
        # Validate model parameter (for manual overrides)
        valid_models = ["tiny", "medium", "large"]
        if model not in valid_models:
            console.print(f"[red]Error: Model must be one of {valid_models}, not '{model}'[/red]")
            console.print("[yellow]Available models:[/yellow]")
            console.print("  - tiny:   tinyllama:1.1b (0.6 GB) - Fast, basic quality")
            console.print("  - medium: gemma2:2b (1.6 GB) - Balanced, good quality")
            console.print("  - large:  qwen3:8b (5.2 GB) - High quality, best results")
            raise typer.Exit(1)
        
        # Validate temperature range
        if not 0.0 <= temperature <= 1.0:
            console.print(f"[red]Error: Temperature must be between 0.0 and 1.0, not {temperature}[/red]")
            raise typer.Exit(1)
        
        # Validate max_tokens
        if max_tokens < 1:
            console.print(f"[red]Error: Max tokens must be positive, not {max_tokens}[/red]")
            raise typer.Exit(1)
        
        # Convert path to absolute Path
        project_path = Path(path).resolve()
        
        if verbose:
            console.print(f"[blue]Project path:[/blue] {project_path}")
            console.print(f"[blue]Language:[/blue] {final_language}")
            console.print(f"[blue]Template:[/blue] {template}")
            console.print(f"[blue]Format:[/blue] {format_type}")
            console.print(f"[blue]Cache enabled:[/blue] {not no_cache}")
            console.print(f"[blue]Model:[/blue] {actual_model_name} ({model_description})")
            if isinstance(model_size, (int, float)):
                console.print(f"[blue]Model size:[/blue] ~{model_size} GB")
        
        # Validate project directory
        if not project_path.exists():
            console.print(f"[red]Error: Directory '{project_path}' does not exist[/red]")
            console.print(f"[yellow]Please check the path and try again[/yellow]")
            raise typer.Exit(1)
        
        if not project_path.is_dir():
            console.print(f"[red]Error: '{project_path}' is not a directory[/red]")
            console.print(f"[yellow]Please provide a directory path, not a file[/yellow]")
            raise typer.Exit(1)
        
        # Determine output path
        if output:
            base_output_path = Path(output).resolve()
        else:
            base_output_path = project_path / "README.md"
        
        # Get correct output path based on format
        exporter = DocumentationExporter(console)
        output_path = exporter.get_output_path(base_output_path, format_type)
        
        if verbose:
            console.print(f"[blue]Output path:[/blue] {output_path}")
        
        # Initialize components
        scanner = FileScanner(console)
        exporter = DocumentationExporter(console)
        cache = DocumentationCache(console=console) if not no_cache else None
        config_manager = SetupManager(console)
        
        # Find Python files with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            scan_task = progress.add_task("🔍 Сканирую Python файлы...", total=None)
            
            try:
                python_files = scanner.find_python_files(
                    project_path, 
                    progress=progress, 
                    task_id=scan_task
                )
            except Exception as e:
                console.print(f"[red]Ошибка при сканировании файлов: {e}[/red]")
                console.print("[yellow]Это может быть связано с проблемами доступа или неверной структурой директории[/yellow]")
                raise typer.Exit(1)
            
            if not python_files:
                console.print("[yellow]⚠ Python файлы не найдены в проекте[/yellow]")
                console.print("[yellow]Убедитесь, что директория содержит .py файлы и они не игнорируются[/yellow]")
                raise typer.Exit(0)
            
            console.print(f"[green]✓ Найдено {len(python_files)} Python файлов[/green]")
            
            # Read files with progress bar
            read_task = progress.add_task("📖 Читаю исходные файлы...", total=None)
            
            try:
                file_contents = scanner.read_files(
                    python_files,
                    progress=progress,
                    task_id=read_task
                )
            except Exception as e:
                console.print(f"[red]Ошибка при чтении файлов: {e}[/red]")
                console.print("[yellow]Некоторые файлы могут быть повреждены или иметь проблемы с кодировкой[/yellow]")
                raise typer.Exit(1)
        
        # Prepare file contents for LLM
        contents_text = ""
        for file_path, content in file_contents:
            relative_path = file_path.relative_to(project_path)
            contents_text += f"\n--- File: {relative_path} ---\n"
            contents_text += content + "\n"
        
        if verbose:
            console.print(f"[blue]Общий размер исходного кода:[/blue] {len(contents_text)} символов")
        
        # Initialize LLM provider
        try:
            provider = LLMFactory.create_provider(console)
        except Exception as e:
            console.print(f"[red]Ошибка инициализации LLM провайдера: {e}[/red]")
            console.print("[yellow]Проверьте вашу конфигурацию (настройки Ollama/OpenAI)[/yellow]")
            raise typer.Exit(1)
        
        # Set the model
        if hasattr(provider, 'model'):
            provider.model = actual_model_name
            # Only show model message if not in setup mode
            if not reconfigure:
                console.print(f"[green]🚀 Используемая модель: {actual_model_name} (~{model_size} GB)[/green]")
        else:
            console.print("[yellow]Предупреждение: Смена модели не поддерживается этим провайдером[/yellow]")
        
        # Get actual model name for caching
        actual_model = getattr(provider, 'model', 'unknown')
        
        # Check cache first
        documentation = None
        if cache and not no_cache:
            try:
                documentation = cache.get_cached_documentation(
                    project_path, file_contents, final_language, template, 
                    actual_model, max_tokens, temperature
                )
            except Exception as e:
                console.print(f"[yellow]Предупреждение: Проверка кэша не удалась: {e}[/yellow]")
                console.print("[yellow]Продолжаю генерацию...[/yellow]")
        
        # Generate documentation if not cached
        if documentation is None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                gen_task = progress.add_task("🤖 Генерирую документацию...", total=None)
                
                try:
                    # Get appropriate prompts
                    system_prompt = get_system_prompt(final_language, template)
                    user_prompt_template = get_user_prompt(final_language)
                    user_prompt = user_prompt_template.format(
                        project_path=str(project_path),
                        file_contents=contents_text
                    )
                    
                    documentation = provider.generate(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    
                    # Cache the result
                    if cache and not no_cache:
                        try:
                            cache.cache_documentation(
                                project_path, file_contents, documentation, 
                                final_language, template, actual_model, max_tokens, temperature
                            )
                        except Exception as e:
                            console.print(f"[yellow]Предупреждение: Не удалось кэшировать документацию: {e}[/yellow]")
                    
                except Exception as e:
                    console.print(f"[red]Ошибка генерации документации: {e}[/red]")
                    console.print("[yellow]Это может быть связано с:[/yellow]")
                    console.print("  - Проблемами с сетевым подключением")
                    console.print("  - Недоступностью LLM сервиса")
                    console.print("  - Неверной конфигурацией API")
                    console.print("  - Превышением лимитов или квоты")
                    raise typer.Exit(1)
        
        # Write documentation to file using exporter
        try:
            title = f"Documentation for {project_path.name}"
            exporter.export_documentation(
                content=documentation,
                output_path=output_path,
                format_type=format_type,
                title=title
            )
            
            console.print(f"[green]✓ Документация успешно сгенерирована![/green]")
            console.print(f"[green]📄 Документация сохранена в:[/green] {output_path}")
            
            # Save last used model
            config_manager.config_manager.update_last_used_model(model)
            
            if format_type == "html":
                console.print(f"[blue]🌐 Open {output_path} in your browser to view the documentation[/blue]")
            
        except IOError as e:
            console.print(f"[red]Ошибка записи файла документации: {e}[/red]")
            console.print("[yellow]Это может быть связано с:[/yellow]")
            console.print("  - Недостаточно места на диске")
            console.print("  - Проблемами с доступом")
            console.print("  - Неверным путем сохранения")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Неожиданная ошибка записи файла: {e}[/red]")
            raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Операция отменена пользователем[/yellow]")
        console.print("[yellow]Файлы не были изменены[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Неожиданная ошибка: {e}[/red]")
        if verbose:
            console.print("[yellow]Полные детали ошибки:[/yellow]")
            import traceback
            console.print(traceback.format_exc())
        else:
            console.print("[yellow]Используйте --verbose для подробной информации об ошибке[/yellow]")
        raise typer.Exit(1)


@app.command()
def models(
    list: bool = typer.Option(
        False,
        "--list",
        help="List all available models and their status",
    ),
) -> None:
    """Show available models and their installation status."""
    from .config import ConfigManager
    
    config_manager = ConfigManager(console)
    model_status = config_manager.get_model_status()
    last_used = config_manager.get_last_used_model()
    
    # Create header
    if last_used:
        console.print(f"[green]Последняя использованная модель: {last_used} ⭐[/green]\n")
    else:
        console.print("[yellow]Первы запуск - нет сохраненной модели[/yellow]\n")
    
    # Create table
    from rich.table import Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Модель", style="cyan", width=12)
    table.add_column("Размер", style="yellow", width=10)
    table.add_column("Статус", style="green", width=20)
    table.add_column("Описание", style="white", width=15)
    
    for model_key, status in model_status.items():
        status_icon = "✅" if status["installed"] else "❌"
        status_text = f"{status_icon} {'Установлена' if status['installed'] else 'Не скачана'}"
        
        if model_key == last_used:
            status_text += " ⭐"
        
        table.add_row(
            model_key,
            status["size"],
            status_text,
            status["desc"]
        )
    
    console.print(table)
    
    # Show summary
    installed_count = sum(1 for status in model_status.values() if status["installed"])
    if installed_count == 0:
        console.print("\n[yellow]⚠️ Ни одна модель не установлена.[/yellow]")
        console.print("[yellow]Используйте 'docgen setup' для установки модели.[/yellow]")
    else:
        console.print(f"\n[green]Установлено моделей: {installed_count}/3[/green]")


@app.command()
def setup() -> None:
    """Run initial setup or reconfigure model selection."""
    # Check Ollama availability first
    if not check_ollama_availability(console):
        show_ollama_installation_message(console)
        raise typer.Exit(1)
    
    setup_manager = SetupManager(console)
    setup_manager.run_initial_setup()


@app.command()
def cache(
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Clear all cached documentation",
    ),
    info: bool = typer.Option(
        False,
        "--info",
        help="Show cache information",
    ),
) -> None:
    """Manage documentation cache."""
    
    cache_manager = DocumentationCache(console=console)
    
    if clear:
        cache_manager.clear_cache()
    elif info:
        cache_info = cache_manager.get_cache_info()
        console.print("[blue]📊 Cache Information:[/blue]")
        console.print(f"  Total entries: {cache_info['total_entries']}")
        console.print(f"  Cache file: {cache_info['cache_file']}")
        console.print(f"  Cache size: {cache_info['cache_size_mb']} MB")
        
        if cache_info['total_entries'] == 0:
            console.print("[yellow]Cache is empty[/yellow]")
        else:
            console.print(f"[green]Cache contains {cache_info['total_entries']} entries[/green]")
    else:
        console.print("[blue]Cache Management:[/blue]")
        console.print("  docgen cache --info    Show cache information")
        console.print("  docgen cache --clear   Clear all cached documentation")


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    console.print(f"docgen version {__version__}")


@app.command()
def check() -> None:
    """Check system configuration and dependencies."""
    console.print("[blue]Checking DocGen configuration...[/blue]")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"✓ Python version: {python_version}")
    
    if sys.version_info < (3, 10):
        console.print("[red]✗ Python 3.10+ is required[/red]")
    else:
        console.print("[green]✓ Python version is compatible[/green]")
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        console.print("[green]✓ OpenAI API key is configured[/green]")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        console.print(f"  Base URL: {base_url}")
    else:
        console.print("[yellow]⚠ OpenAI API key not configured[/yellow]")
    
    # Check Ollama connection
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    console.print(f"Checking Ollama at {ollama_url}...")
    
    try:
        from .llm import OllamaProvider
        ollama = OllamaProvider(base_url=ollama_url, console=console)
        if ollama.check_connection():
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            console.print(f"[green]✓ Ollama is accessible (model: {model})[/green]")
        else:
            console.print("[yellow]⚠ Ollama is not accessible[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error checking Ollama: {e}[/red]")
    
    console.print("\n[blue]Configuration complete![/blue]")


if __name__ == "__main__":
    app()
