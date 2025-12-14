"""Module Coupling Analyzer

Analyzes coupling between modules by tracking imports.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from cobana.utils.ast_utils import ASTParser
from cobana.utils.file_utils import read_file_safely
from cobana.utils.module_detector import Module

logger = logging.getLogger(__name__)


class ModuleCouplingAnalyzer:
    """Analyzes coupling between modules."""

    def __init__(self, config: dict[str, Any], modules: list[Module]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
            modules: List of detected modules
        """
        self.config = config
        self.modules = {m.name: m for m in modules}
        self.module_paths = {m.path: m.name for m in modules}

        # Results storage
        self.results: dict[str, Any] = {
            "total_modules": len(modules),
            "avg_afferent_coupling": 0.0,
            "avg_efferent_coupling": 0.0,
            "avg_instability": 0.0,
            "per_module": {},
            "stable_modules": [],
            "unstable_modules": [],
            "high_fanout_modules": [],
            "dependency_graph": {
                "nodes": [m.name for m in modules],
                "edges": [],
            },
        }

        # Track imports
        self._imports: dict[str, set[str]] = defaultdict(
            set
        )  # module -> modules it imports
        self._imported_by: dict[str, set[str]] = defaultdict(
            set
        )  # module -> modules that import it

    def analyze_file(self, file_path: Path, module_name: str) -> None:
        """Analyze imports in a file to track module coupling.

        Args:
            file_path: Path to file
            module_name: Module the file belongs to
        """
        # For backward compatibility, read and delegate
        content = read_file_safely(file_path)
        if content is None:
            return
        self.analyze_file_content(content, file_path, module_name)

    def analyze_file_content(
        self, content: str, file_path: Path, module_name: str
    ) -> None:
        """Analyze imports from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file
            module_name: Module the file belongs to
        """
        parser = ASTParser(file_path, content)
        imports = parser.get_imports()

        if not imports:
            return

        for import_info in imports:
            # Determine which module is being imported
            imported_module = self._get_imported_module(import_info)

            if imported_module and imported_module != module_name:
                # Track the dependency
                self._imports[module_name].add(imported_module)
                self._imported_by[imported_module].add(module_name)

    def _get_imported_module(self, import_info: dict[str, Any]) -> str | None:
        """Determine which module an import belongs to.

        Args:
            import_info: Import information dictionary

        Returns:
            Module name or None
        """
        # Get the module path from the import
        if import_info["type"] == "from_import":
            module_path = import_info["module"]
        else:
            module_path = import_info["module"]

        if not module_path:
            return None

        # Check if this import is from one of our tracked modules
        for mod_path, mod_name in self.module_paths.items():
            if module_path.startswith(mod_path.replace("/", ".")):
                return mod_name

        return None

    def finalize_results(self) -> dict[str, Any]:
        """Calculate coupling metrics and finalize results.

        Returns:
            Complete analysis results
        """
        fan_out_threshold = self.config.get("thresholds", {}).get(
            "module_fan_out", 10
        )

        total_ca = 0
        total_ce = 0
        total_instability = 0
        module_count = 0

        # Calculate metrics for each module
        for module_name in self.modules.keys():
            ca = len(
                self._imported_by.get(module_name, set())
            )  # Afferent coupling
            ce = len(self._imports.get(module_name, set()))  # Efferent coupling

            # Calculate instability: I = Ce / (Ca + Ce)
            if ca + ce > 0:
                instability = ce / (ca + ce)
            else:
                instability = 0.0

            # Categorize stability
            if instability < 0.3:
                stability_category = "stable"
            elif instability > 0.7:
                stability_category = "unstable"
            else:
                stability_category = "moderate"

            module_info = {
                "module": module_name,
                "afferent_coupling": ca,
                "efferent_coupling": ce,
                "instability": instability,
                "stability_category": stability_category,
                "imported_by": list(self._imported_by.get(module_name, set())),
                "imports": list(self._imports.get(module_name, set())),
            }

            self.results["per_module"][module_name] = module_info

            # Track stable and unstable modules
            if instability <= 0.3:
                self.results["stable_modules"].append(
                    {
                        "module": module_name,
                        "instability": instability,
                    }
                )
            elif instability >= 0.7:
                self.results["unstable_modules"].append(
                    {
                        "module": module_name,
                        "instability": instability,
                    }
                )

            # Track high fan-out modules
            if ce > fan_out_threshold:
                self.results["high_fanout_modules"].append(
                    {
                        "module": module_name,
                        "efferent_coupling": ce,
                        "dependencies": list(
                            self._imports.get(module_name, set())
                        ),
                    }
                )

            # Update averages
            total_ca += ca
            total_ce += ce
            total_instability += instability
            module_count += 1

        # Calculate overall averages
        if module_count > 0:
            self.results["avg_afferent_coupling"] = total_ca / module_count
            self.results["avg_efferent_coupling"] = total_ce / module_count
            self.results["avg_instability"] = total_instability / module_count

        # Build dependency graph edges
        for from_module, to_modules in self._imports.items():
            for to_module in to_modules:
                self.results["dependency_graph"]["edges"].append(
                    {
                        "from": from_module,
                        "to": to_module,
                    }
                )

        # Sort lists
        self.results["stable_modules"].sort(key=lambda x: x["instability"])
        self.results["unstable_modules"].sort(
            key=lambda x: x["instability"], reverse=True
        )
        self.results["high_fanout_modules"].sort(
            key=lambda x: x["efferent_coupling"], reverse=True
        )

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            "total_modules": self.results["total_modules"],
            "avg_instability": round(self.results["avg_instability"], 2),
            "stable_modules_count": len(self.results["stable_modules"]),
            "unstable_modules_count": len(self.results["unstable_modules"]),
            "high_fanout_count": len(self.results["high_fanout_modules"]),
        }
