# COBANA - Codebase Architecture Analysis Tool

**Automated Python codebase analysis tool to measure architectural health, code quality, and technical debt with educational explanations for both technical and non-technical stakeholders.**

## Features

### 🔍 Comprehensive Analysis

- **Database Coupling Analysis** (PRIMARY FOCUS) - Detect and categorize database operations, identify architectural violations
- **Cyclomatic Complexity** - Measure code complexity and identify overly complex functions
- **Maintainability Index** - Calculate maintainability scores per file
- **Code Size Metrics** - Track SLOC, comment ratios, large files and functions
- **Test Analysis** - Categorize tests (unit vs integration), calculate testability scores
- **Module Coupling** - Analyze dependencies between modules, calculate instability metrics
- **Class Metrics** - Detect god classes, measure LCOM and WMC
- **Code Smells** - Identify long methods, deep nesting, long parameter lists
- **Technical Debt** - Calculate remediation costs and assign SQALE ratings (A-E)
- **Module Health Scores** - Composite health scores (0-100) per module

### 📊 Module-Level Breakdown

All metrics are tracked both **overall** and **per-module**, enabling:
- Module comparison and ranking
- Targeted improvement recommendations
- Team-specific insights
- Identification of problem areas

### 📑 Multiple Output Formats

- **JSON** - Machine-readable data for automation/CI/CD
- **Markdown** - Text summary for documentation, PRs, commit messages
- **HTML** - Self-contained visual report *(coming soon)*

### 🎯 Educational & Actionable

Every metric includes:
- Plain-language explanation ("What is this?")
- Business impact ("Why it matters")
- Specific recommendations ("What to do")
- File paths and line numbers for issues

## Requirements

- **Python:** 3.11 or higher
- **Package Manager:** `uv` (recommended) or `pip`

## Installation

### Using uv (Recommended)

```bash
# Clone or navigate to the project
cd cobana

# Install in development mode
uv pip install -e .

# Or install dependencies only
uv pip install radon jinja2 pyyaml
```

### Using pip

```bash
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Analyze a codebase
cobana /path/to/your/python/project

# With verbose output
cobana /path/to/project --verbose

# Generate reports
cobana /path/to/project --json analysis.json --markdown summary.md
```

### With Configuration

```bash
# Use custom configuration
cobana /path/to/project --config my_config.yaml

# Override service name
cobana /path/to/project --service-name my_service

# Set module detection depth
cobana /path/to/project --module-depth 2
```

## Configuration

Create a `config.yaml` file to customize analysis. See `config.yaml.example` for a complete template.

### Example Configuration

```yaml
# Service identification
service_name: my_service

# Module detection
module_detection:
  method: auto  # or "manual"
  depth: 1      # Folder depth for modules

# Table ownership (for database coupling analysis)
table_ownership:
  my_service:
    - my_table_1
    - my_table_2
  other_service:
    - other_table_1
  shared:
    - shared_table_1

# Customize thresholds
thresholds:
  complexity: 10
  maintainability: 20
  file_size: 500
  # ... see config.yaml.example for all options
```

## Module Detection

COBANA automatically detects logical modules from your folder structure.

### Auto Detection (Default)

```
project/
├── module_a/          # Module: "module_a"
│   ├── subdir/
│   └── files.py
├── module_b/          # Module: "module_b"
└── shared/            # Module: "shared"
```

### Manual Configuration

```yaml
module_detection:
  method: manual
  manual_modules:
    - name: "Core Module"
      path: "core"
      description: "Core business logic"
    - name: "API Module"
      path: "api"
      description: "REST API endpoints"
```

## Output Examples

### Console Summary

```
======================================================================
ANALYSIS SUMMARY
======================================================================

Service: my_service
Files Analyzed: 173
Modules: 4

Overall Health: 65.3/100 🟡 Good

Technical Debt: 18.5% (SQALE Rating: C) 🟡 Moderate
  Remediation Time: 89.2 hours

Database Coupling:
  Total Operations: 247
  Critical Violations: 17 🔴
  Warnings: 80 🟡

...
```

### JSON Output

Complete machine-readable data including:
- All metrics (overall + per-module)
- Detailed violation lists with file paths and line numbers
- Module rankings and health scores
- Technical debt breakdown

### Markdown Summary

Concise summary suitable for:
- Pull request descriptions
- Documentation
- Team reports
- Stakeholder updates

## Metrics Explained

### Database Coupling (30% weight in health score)

**What it measures:** How tightly code is coupled to database access

**Categories:**
- ✅ **Own tables** - Acceptable
- ⚠️ **Shared tables** - Warning
- ⚠️ **Other service reads** - Coupling warning
- 🔴 **Other service writes** - Critical violation

**Severity Score:** `(other_reads × 1) + (other_writes × 5)`

### Complexity (20% weight)

**What it measures:** Cyclomatic complexity per function

**Thresholds:**
- 1-5: Simple ✅
- 6-10: Moderate ⚠️
- 11-20: Complex 🟠
- 21+: Very Complex 🔴

### Maintainability Index (20% weight)

**What it measures:** How easy code is to maintain (0-100 scale)

**Thresholds:**
- 65-100: High ✅
- 20-64: Moderate ⚠️
- 0-19: Low 🔴

### Testability (15% weight)

**What it measures:** Percentage of code that can be unit tested

**Identifies:** Functions mixing business logic with database access (untestable)

### Code Smells (10% weight)

- Long methods (>50 LOC)
- Long parameter lists (>5 params)
- Deep nesting (>4 levels)

### Technical Debt (5% weight)

**SQALE Ratings:**
- A (≤5%): Excellent ✅
- B (6-10%): Good ✅
- C (11-20%): Moderate ⚠️
- D (21-50%): High 🟠
- E (>50%): Critical 🔴

## Command-Line Options

```
usage: cobana [-h] [--config FILE] [--output FILE] [--json FILE]
              [--markdown FILE] [--service-name NAME] [--module-depth N]
              [-v] [--version]
              path

positional arguments:
  path                  Path to codebase root directory

optional arguments:
  -h, --help            show this help message and exit
  --config FILE         Configuration file
  --output FILE         HTML report output [NOT YET IMPLEMENTED]
  --json FILE           JSON data output
  --markdown FILE       Markdown summary output
  --service-name NAME   Service name for ownership analysis
  --module-depth N      Folder depth for module detection (default: 1)
  -v, --verbose         Show progress during analysis
  --version             show program's version number and exit
```

## Development

### Project Structure

```
cobana/
├── cobana/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── analyzer.py            # Main orchestrator
│   ├── analyzers/             # All analysis modules
│   │   ├── db_coupling.py     # Database coupling (PRIMARY)
│   │   ├── complexity.py
│   │   ├── maintainability.py
│   │   ├── code_size.py
│   │   ├── test_analysis.py
│   │   ├── module_coupling.py
│   │   ├── class_metrics.py
│   │   ├── code_smells.py
│   │   ├── tech_debt.py
│   │   └── module_health.py
│   ├── report/                # Report generators
│   │   ├── json_generator.py
│   │   └── md_generator.py
│   └── utils/                 # Utilities
│       ├── config_utils.py
│       ├── file_utils.py
│       ├── module_detector.py
│       └── ast_utils.py
├── pyproject.toml             # Project config (uv)
├── .python-version            # Python version (3.11)
└── config.yaml.example        # Example configuration
```

### Running from Source

```bash
# Run directly with Python
python -m cobana.cli /path/to/project

# Or with uv
uv run cobana /path/to/project
```

## Roadmap

### ✅ Completed (v1.0)

- All core analyzers
- JSON and Markdown report generation
- Module-level analysis
- CLI interface
- Configuration system

### 🚧 In Progress

- HTML report generation with charts
- Comprehensive test suite

### 📋 Planned

- CI/CD integration examples
- Historical trend analysis
- Automated refactoring suggestions
- Additional language support

## Philosophy

COBANA follows these principles:

1. **Educational** - Every metric includes clear explanations
2. **Actionable** - Specific files, line numbers, and prioritized recommendations
3. **Module-First** - Break down analysis by module for targeted improvements
4. **Objective** - Reproducible measurements, not subjective opinions
5. **Configuration-Driven** - Customize thresholds for your project

## Contributing

Contributions are welcome! Please ensure:

- Code follows Python 3.11+ modern features (match statements, type hints with `|`)
- All functions have type hints and docstrings
- New analyzers follow the `Analyzer` protocol pattern
- Tests are included for new features

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [Radon](https://github.com/rubik/radon) - Code metrics
- [Jinja2](https://jinja.palletsprojects.com/) - Templating
- [PyYAML](https://pyyaml.org/) - Configuration

---

**COBANA** - *Making code quality visible, measurable, and actionable.*
