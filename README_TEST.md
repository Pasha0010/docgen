# DocGen - AI-Powered Technical Documentation Generator

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)  
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📌 Project Overview

DocGen is an intelligent documentation generator for Python projects. It automatically creates comprehensive README.md files by analyzing source code, identifying key components, and generating structured documentation that helps developers understand, use, and contribute to projects.

This tool integrates with both OpenAI and Ollama APIs to leverage advanced language models for documentation creation.

## ✅ Key Features

- **Automated Documentation**: Generate complete README.md files from source code
- **AI-Powered Writing**: Uses advanced language models for intelligent documentation
- **Multi-Model Support**: Works with OpenAI and Ollama APIs
- **Structured Output**: Creates standardized README.md with best practices
- **Code Analysis**: Understands project architecture and component relationships
- **Customizable**: Configure model parameters and output formats

## 📦 Installation

### Via pip
```bash
pip install docgen
```

### From Source
```bash
git clone https://github.com/yourusername/docgen.git
cd docgen
pip install .
```

**Requirements**:
- Python 3.10+
- Required dependencies: `rich`, `pydantic`, `httpx`

## 🚀 Usage Examples

### Basic Usage
```bash
docgen --input ./your_project_directory
```

### With Custom Configuration
```bash
docgen --input ./project \
  --model "ollama/qwen2.5:7b" \
  --output ./docs \
  --format markdown
```

## 📚 API Documentation

### Main Components

#### `FileScanner`
```python
from docgen import FileScanner

scanner = FileScanner()
python_files = scanner.find_python_files("your_project_directory")
```

#### `LLMIntegration`
```python
from docgen.llm import LLMIntegration

llm = LLMIntegration(model="openai/gpt-3.5-turbo")
documentation = llm.generate_documentation(project_structure)
```

### Configuration Parameters
| Parameter | Default | Description |
|----------|---------|-------------|
| `model` | "ollama/qwen2.5:7b" | Language model to use |
| `format` | "markdown" | Output format (markdown/html) |
| `output` | "." | Output directory |
| `verbose` | false | Enable detailed logging |

## 📁 Project Structure

```
docgen/
├── __init__.py
├── llm.py          # LLM integration logic
├── prompt.py       # System prompts for documentation
├── scanner.py      # File scanning and analysis
└── check.py        # Configuration validation
```

## 📝 Configuration Details

### Environment Variables
```bash
# For OpenAI
export OPENAI_API_KEY="your_api_key"

# For Ollama
export OLLAMA_HOST="http://localhost:11434"
```

### Configuration File (docgen.yaml)
```yaml
model:
  provider: ollama
  model: qwen2.5:7b
format: markdown
output: ./docs
verbose: true
```

## 🤝 Contributing

1. **Report Issues**: [GitHub Issues](https://github.com/yourusername/docgen/issues)
2. **Submit Enhancements**: Pull requests are welcome!
3. **Develop Features**: Check the [roadmap](ROADMAP.md) for upcoming features
4. **Documentation**: Help improve our documentation and examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌐 Support

For questions or assistance, please:

- Check the [documentation](https://docgen.dev/docs)
- Join our [Discord community](https://discord.gg/docgen)
- Open an issue on [GitHub](https://github.com/yourusername/docgen)

--- 
*Documentation generated using DocGen v0.1.0*