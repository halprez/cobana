"""CodebaseAnalyzer - Main orchestrator for codebase analysis.

This class coordinates all analyzers and produces comprehensive analysis results.
"""

from pathlib import Path
from typing import Any
import logging
from logging.handlers import RotatingFileHandler

from cobana.utils.config_utils import load_config
from cobana.utils.file_utils import FileScanner, read_file_safely, find_tests_directory
from cobana.utils.module_detector import ModuleDetector

# Import all analyzers
from cobana.analyzers.db_coupling import DatabaseCouplingAnalyzer
from cobana.analyzers.complexity import ComplexityAnalyzer
from cobana.analyzers.maintainability import MaintainabilityAnalyzer
from cobana.analyzers.code_size import CodeSizeAnalyzer
from cobana.analyzers.test_analysis import TestAnalyzer
from cobana.analyzers.module_coupling import ModuleCouplingAnalyzer
from cobana.analyzers.class_metrics import ClassMetricsAnalyzer
from cobana.analyzers.code_smells import CodeSmellsAnalyzer
from cobana.analyzers.tech_debt import TechnicalDebtCalculator
from cobana.analyzers.module_health import ModuleHealthCalculator

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Orchestrates comprehensive codebase analysis.

    This class emerged from the pattern of running multiple analyzers
    and aggregating their results. It handles:
    - Module detection
    - File scanning
    - Running all analyzers
    - Aggregating results
    - Calculating composite metrics
    """

    def __init__(
        self,
        root_path: Path | str,
        config_path: Path | str | None = None,
        verbose: bool = False,
        log_file: Path | str = "cobana.log",
        tests_dir: Path | str | None = None,
    ):
        """Initialize codebase analyzer.

        Args:
            root_path: Root directory of codebase to analyze
            config_path: Optional path to configuration file
            verbose: Enable verbose logging
            log_file: Path to log file (default: cobana.log)
            tests_dir: Optional path to tests directory (auto-detects if not provided)
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.config = load_config(config_path)

        # Setup logging to file with rotation
        self._setup_logging(log_file, verbose)

        # Resolve tests directory
        self.tests_dir = self._resolve_tests_dir(tests_dir)

        # Module detection
        self.module_detector = ModuleDetector(self.root_path, self.config)
        self.modules = []

        # File scanner
        self.scanner = FileScanner(
            self.root_path,
            self.config.get("exclude_patterns", []),
            verbose,
            self.config.get("max_depth"),
        )

        # Initialize all analyzers
        self._init_analyzers()

        # Results
        self.results: dict[str, Any] = {}

    def _init_analyzers(self) -> None:
        """Initialize all analyzer instances."""
        self.db_coupling = DatabaseCouplingAnalyzer(self.config)
        self.complexity = ComplexityAnalyzer(self.config)
        self.maintainability = MaintainabilityAnalyzer(self.config)
        self.code_size = CodeSizeAnalyzer(self.config)
        self.test_analyzer = TestAnalyzer(self.config, self.tests_dir)
        self.class_metrics = ClassMetricsAnalyzer(self.config)
        self.code_smells = CodeSmellsAnalyzer(self.config)

        # Module coupling analyzer needs modules, will init later
        self.module_coupling = None

        # Calculators (run after all analysis)
        self.tech_debt = TechnicalDebtCalculator(self.config)
        self.module_health = ModuleHealthCalculator(self.config)

    def _resolve_tests_dir(self, tests_dir: Path | str | None) -> Path | None:
        """Resolve tests directory path.

        Args:
            tests_dir: Optional path to tests directory

        Returns:
            Resolved Path to tests directory, or None if not found
        """
        if tests_dir:
            # User provided a tests directory
            test_path = Path(tests_dir)

            # If relative, make it relative to root_path
            if not test_path.is_absolute():
                test_path = self.root_path / test_path

            test_path = test_path.resolve()

            if test_path.exists() and test_path.is_dir():
                logger.info(f"Using specified tests directory: {test_path}")
                return test_path
            else:
                logger.warning(
                    f"Specified tests directory does not exist: {test_path}. "
                    "Will attempt auto-detection."
                )

        # Auto-detect tests directory
        auto_detected = find_tests_directory(self.root_path)
        if auto_detected:
            return auto_detected

        logger.info("No tests directory found. Will scan all files for tests.")
        return None

    def _setup_logging(self, log_file: Path | str, verbose: bool) -> None:
        """Setup rotating file logging.

        Args:
            log_file: Path to log file
            verbose: Enable verbose logging
        """
        log_path = Path(log_file)

        # Create a rotating file handler
        # Max 10MB per file, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        # Set logging level for file
        if verbose:
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Get root logger and configure it
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels

        # Remove any existing handlers
        root_logger.handlers = []

        # Add file handler
        root_logger.addHandler(file_handler)

        # Add console handler for errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        logger.info(f"Logging to {log_path.resolve()}")

    def analyze(self) -> dict[str, Any]:
        """Run complete codebase analysis.

        Returns:
            Complete analysis results dictionary
        """
        print(f"🔍 Starting analysis of {self.root_path}")

        # Print tests directory info
        if self.tests_dir:
            try:
                rel_tests_dir = self.tests_dir.relative_to(self.root_path)
                print(f"🧪 Tests directory: {rel_tests_dir}")
            except ValueError:
                print(f"🧪 Tests directory: {self.tests_dir}")
        else:
            print("🧪 Tests directory: Not found (will use filename heuristics)")

        # Refresh scanner with current config (in case config was modified after init)
        self.scanner = FileScanner(
            self.root_path,
            self.config.get("exclude_patterns", []),
            self.verbose,
            self.config.get("max_depth"),
        )

        # Step 1: Detect modules
        self.modules = self.module_detector.detect_modules()
        module_names = [m.name if hasattr(m, 'name') else str(m) for m in self.modules]
        print(f"📦 Detected {len(self.modules)} modules: {', '.join(module_names)}")

        # Initialize module coupling analyzer now that we have modules
        self.module_coupling = ModuleCouplingAnalyzer(self.config, self.modules)

        # Step 2: Collect all files first to get total count
        print("📂 Scanning Python files...")
        all_files = list(self.scanner.scan_python_files())
        total_files = len(all_files)
        print(f"📊 Found {total_files} Python files to analyze")

        # Step 3: Analyze files with progress
        files_analyzed = 0
        for file_path in all_files:
            module_name = self.module_detector.get_module_for_file(file_path)

            # Run analyzers on this file
            self._analyze_file(file_path, module_name)
            files_analyzed += 1

            # Show progress every 10 files or at the end
            if files_analyzed % 10 == 0 or files_analyzed == total_files:
                print(f"\r⚙️  Processing: {files_analyzed}/{total_files} files ({files_analyzed*100//total_files}%)", end="", flush=True)

        print()  # New line after progress
        print(f"✅ Analyzed {files_analyzed} files")

        # Step 4: Finalize all analyzers
        print("🔄 Finalizing analysis results...")
        self._finalize_analyzers()

        # Step 5: Calculate debt and health scores
        print("📈 Calculating technical debt and health scores...")
        self._calculate_composite_metrics()

        # Step 6: Build final results
        self._build_results()

        print("✨ Analysis complete!")
        return self.results

    def _analyze_file(self, file_path: Path, module_name: str) -> None:
        """Analyze a single file with all applicable analyzers.

        Reads file once and passes content to all analyzers to avoid
        redundant disk I/O (optimization: 87.5% reduction in file reads).

        Args:
            file_path: Path to file
            module_name: Module the file belongs to
        """
        # Read file ONCE instead of 8 times
        content = read_file_safely(file_path)
        if content is None:
            return

        is_test = self.test_analyzer.is_test_file(file_path)

        if is_test:
            # Analyze as test file
            self.test_analyzer.analyze_test_file_content(
                content, file_path, module_name
            )
        else:
            # Analyze as regular code
            self.db_coupling.analyze_file_content(
                content, file_path, module_name
            )
            self.test_analyzer.analyze_testability_content(
                content, file_path, module_name
            )
            # Track production functions for test coverage calculation
            self.test_analyzer.track_production_functions(
                file_path, module_name, content
            )

        # Run on all files (test and non-test)
        # All analyzers now use pre-read content instead of reading again
        self.complexity.analyze_file_content(content, file_path, module_name)
        self.maintainability.analyze_file_content(
            content, file_path, module_name
        )
        self.code_size.analyze_file_content(content, file_path, module_name)
        self.class_metrics.analyze_file_content(content, file_path, module_name)
        self.code_smells.analyze_file_content(content, file_path, module_name)
        self.module_coupling.analyze_file_content(
            content, file_path, module_name
        )

    def _finalize_analyzers(self) -> None:
        """Finalize all analyzers."""
        self.db_coupling_results = self.db_coupling.finalize_results()
        self.complexity_results = self.complexity.finalize_results()
        self.maintainability_results = self.maintainability.finalize_results()
        self.code_size_results = self.code_size.finalize_results()
        self.test_results = self.test_analyzer.finalize_results()
        self.module_coupling_results = self.module_coupling.finalize_results()
        self.class_metrics_results = self.class_metrics.finalize_results()
        self.code_smells_results = self.code_smells.finalize_results()

    def _calculate_composite_metrics(self) -> None:
        """Calculate technical debt and module health scores."""
        # Calculate technical debt
        self.tech_debt_results = self.tech_debt.calculate(
            self.complexity_results,
            self.maintainability_results,
            self.code_size_results,
            self.db_coupling_results,
            self.class_metrics_results,
            self.code_smells_results,
        )

        # Calculate module health
        module_names = [m.name for m in self.modules]
        self.module_health_results = self.module_health.calculate(
            module_names,
            self.db_coupling_results,
            self.complexity_results,
            self.maintainability_results,
            self.test_results,
            self.code_smells_results,
            self.tech_debt_results,
            self.code_size_results,
        )

    def _build_results(self) -> None:
        """Build final results structure."""
        self.results = {
            "metadata": {
                "codebase_path": str(self.root_path),
                "service_name": self.config.get("service_name", "unknown"),
                "total_files_analyzed": self.scanner.files_scanned,
                "total_files_skipped": self.scanner.files_skipped,
                "module_count": len(self.modules),
                "modules": [m.to_dict() for m in self.modules],
            },
            "summary": {
                **self.db_coupling.get_summary(),
                **self.complexity.get_summary(),
                **self.maintainability.get_summary(),
                **self.code_size.get_summary(),
                **self.test_analyzer.get_summary(),
                **self.module_coupling.get_summary(),
                **self.class_metrics.get_summary(),
                **self.code_smells.get_summary(),
                **self.tech_debt.get_summary(),
                **self.module_health.get_summary(),
            },
            "db_coupling": self.db_coupling_results,
            "complexity": self.complexity_results,
            "maintainability": self.maintainability_results,
            "code_size": self.code_size_results,
            "tests": self.test_results,
            "module_coupling": self.module_coupling_results,
            "class_metrics": self.class_metrics_results,
            "code_smells": self.code_smells_results,
            "technical_debt": self.tech_debt_results,
            "module_health": self.module_health_results,
        }

    def get_results(self) -> dict[str, Any]:
        """Get analysis results.

        Returns:
            Complete analysis results
        """
        return self.results
