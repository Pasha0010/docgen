# 📄 DocGen - AI-Powered Technical Documentation Generator

## 🚀 Overview
DocGen is an AI-powered tool that automates the generation of technical documentation for Python projects. It leverages large language models (LLMs) to analyze code, generate API references, tutorials, and more. The tool includes features for model selection, configuration management, and multi-format documentation output.

## 📦 Installation
```bash
git clone https://github.com/your-username/docgen.git
cd docgen
pip install -r requirements.txt
```

## 🧰 Setup
### 1. Initial Configuration
```bash
docgen setup
```
This will:
1. Show model selection menu (tiny/medium/large)
2. Download selected model using Ollama
3. Save configuration to `~/.docgen/config.json`

### 2. Model Configuration
```bash
docgen generate --reconfigure
```
Select from available models:
- `tiny` (1.5GB) - Fast and lightweight
- `medium` (7.5GB) - Balanced performance
- `large` (30GB) - Advanced reasoning

## 💡 Usage
### Generate Documentation
```bash
docgen generate --model medium --input my_project --output docs/
```
Parameters:
- `--model`: Select AI model (default: medium)
- `--input`: Path to Python project
- `--output`: Output directory for documentation
- `--format`: Output format (md/html/both)

### CLI Commands
```bash
docgen --help
docgen generate --help
docgen setup
docgen reconfigure
docgen version
```

## 📁 File Processing
DocGen processes documentation files through these stages:
1. **Analysis**: Parses Python files, identifies classes/functions
2. **Generation**: Uses LLM to create:
   - API references
   - Code examples
   - Architecture diagrams
   - Tutorial guides
3. **Formatting**: Converts output to selected format (Markdown, HTML)

## 📌 Configuration
### config.json
```json
{
  "selected_model": "medium",
  "model_name": "Llama-3-8B",
  "setup_completed": true,
  "last_used_model": "medium"
}
```

## 📚 Examples
### Input
```python
# my_project/utils.py
def calculate_interest(principal, rate, years):
    """Calculate compound interest."""
    return principal * (1 + rate)**years
```

### Output (Markdown)
```markdown
## Utility Functions

### `calculate_interest(principal, rate, years)`
**Description**: Calculate compound interest.

**Parameters**:
- `principal` (float): Initial amount
- `rate` (float): Annual interest rate
- `years` (int): Time period in years

**Returns**:
- float: Calculated interest amount
```

## 🛠️ Development
### File Structure
```
docgen/
├── __init__.py
├── llm.py          # LLM integration
├── config.py       # Configuration manager
├── processor.py    # Documentation processor
├── setup.py        # CLI setup
└── README.md       # This file
```

## 📌 Notes
1. Requires [Ollama](https://ollama.ai) for model downloads
2. Model size affects performance:
   - Tiny: Fast but limited context
   - Medium: Balanced for most use cases
   - Large: Best for complex documentation
3. Use `--reconfigure` to switch models anytime

## 🚀 Next Steps
1. Explore advanced formatting options
2. Integrate with CI/CD pipelines
3. Add support for multiple programming languages

For more details, see the [GitHub repository](https://github.com/your-username/docgen).