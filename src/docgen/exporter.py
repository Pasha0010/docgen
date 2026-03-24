"""
Export functionality for different output formats.
"""

import os
from pathlib import Path
from typing import Optional
import markdown
from rich.console import Console


class DocumentationExporter:
    """Exporter for documentation in different formats."""
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the exporter.
        
        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()
    
    def export_to_html(self, markdown_content: str, output_path: Path, 
                      title: str = "Documentation") -> None:
        """Convert markdown to HTML and save to file.
        
        Args:
            markdown_content: Markdown content to convert.
            output_path: Path for HTML output file.
            title: HTML document title.
            
        Raises:
            IOError: If file cannot be written.
        """
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=[
                    'fenced_code',
                    'codehilite',
                    'tables',
                    'toc',
                    'nl2br',
                ]
            )
            
            # Create complete HTML document
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 1em 0;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
            border-radius: 0;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 1em 0;
            padding-left: 20px;
            color: #7f8c8d;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .toc {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 2em;
        }}
        .toc h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 5px 0;
        }}
        .toc a {{
            color: #3498db;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
                
        except Exception as e:
            raise IOError(f"Failed to export HTML: {e}")
    
    def export_documentation(self, content: str, output_path: Path, 
                           format_type: str = "markdown", title: str = "Documentation") -> None:
        """Export documentation in specified format.
        
        Args:
            content: Documentation content.
            output_path: Output file path.
            format_type: Output format (markdown/html).
            title: Document title (for HTML).
            
        Raises:
            ValueError: If format is not supported.
            IOError: If file cannot be written.
        """
        if format_type == "markdown":
            # Just save as markdown
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                raise IOError(f"Failed to save markdown: {e}")
                
        elif format_type == "html":
            # Convert to HTML
            html_path = output_path.with_suffix('.html')
            self.export_to_html(content, html_path, title)
            
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_output_path(self, base_path: Path, format_type: str = "markdown") -> Path:
        """Get appropriate output path for format.
        
        Args:
            base_path: Base output path.
            format_type: Output format.
            
        Returns:
            Output path with correct extension.
        """
        if format_type == "html":
            return base_path.with_suffix('.html')
        else:
            return base_path.with_suffix('.md')
