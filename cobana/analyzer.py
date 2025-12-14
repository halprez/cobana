"""CodebaseAnalyzer - Main orchestrator for codebase analysis.

This class coordinates all analyzers and produces comprehensive analysis results.
"""

from pathlib import Path
from typing import Any
import logging

from cobana.utils.config_utils import load_config
from cobana.utils.file_utils import FileScanner, read_file_safely
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
    ):
        """Initialize codebase analyzer.

        Args:
            root_path: Root directory of codebase to analyze
            config_path: Optional path to configuration file
            verbose: Enable verbose logging
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.config = load_config(config_path)

        # Setup logging
        if verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

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
        self.test_analyzer = TestAnalyzer(self.config)
        self.class_metrics = ClassMetricsAnalyzer(self.config)
        self.code_smells = CodeSmellsAnalyzer(self.config)

        # Module coupling analyzer needs modules, will init later
        self.module_coupling = None

        # Calculators (run after all analysis)
        self.tech_debt = TechnicalDebtCalculator(self.config)
        self.module_health = ModuleHealthCalculator(self.config)

    def analyze(self) -> dict[str, Any]:
        """Run complete codebase analysis.

        Returns:
            Complete analysis results dictionary
        """
        logger.info(f"Starting analysis of {self.root_path}")

        # Refresh scanner with current config (in case config was modified after init)
        self.scanner = FileScanner(
            self.root_path,
            self.config.get("exclude_patterns", []),
            self.verbose,
            self.config.get("max_depth"),
        )

        # Step 1: Detect modules
        self.modules = self.module_detector.detect_modules()
        logger.info(f"Detected {len(self.modules)} modules")

        # Initialize module coupling analyzer now that we have modules
        self.module_coupling = ModuleCouplingAnalyzer(self.config, self.modules)

        # Step 2: Scan and analyze files
        files_analyzed = 0
        for file_path in self.scanner.scan_python_files():
            module_name = self.module_detector.get_module_for_file(file_path)

            # Run analyzers on this file
            self._analyze_file(file_path, module_name)
            files_analyzed += 1

        logger.info(f"Analyzed {files_analyzed} files")

        # Step 3: Finalize all analyzers
        self._finalize_analyzers()

        # Step 4: Calculate debt and health scores
        self._calculate_composite_metrics()

        # Step 5: Build final results
        self._build_results()

        logger.info("Analysis complete")
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
        logger.info("Finalizing analyzer results...")

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
        logger.info("Calculating technical debt and health scores...")

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
