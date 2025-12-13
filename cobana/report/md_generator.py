"""Markdown Report Generator

Generates concise Markdown summaries from analysis results.
"""

from pathlib import Path
from typing import Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Generates Markdown summary reports from analysis results."""

    def __init__(self, results: dict[str, Any]):
        """Initialize generator.

        Args:
            results: Complete analysis results
        """
        self.results = results
        self.metadata = results.get('metadata', {})
        self.summary = results.get('summary', {})

    def generate(self, output_path: Path | str) -> None:
        """Generate Markdown report and save to file.

        Args:
            output_path: Path where to save the Markdown report
        """
        output_path = Path(output_path)
        content = self.get_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Markdown report generated: {output_path}")

    def get_markdown(self) -> str:
        """Generate Markdown content.

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# Codebase Analysis Report")
        lines.append(f"")
        lines.append(f"**Service:** {self.metadata.get('service_name', 'Unknown')}")
        lines.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Files Analyzed:** {self.metadata.get('total_files_analyzed', 0)}")
        lines.append(f"**Modules:** {self.metadata.get('module_count', 0)}")
        lines.append(f"")

        # Executive Summary
        lines.append(f"## Executive Summary")
        lines.append(f"")

        # Module Health
        health = self.summary.get('overall_health', 0)
        health_emoji = self._get_health_emoji(health)
        lines.append(f"### {health_emoji} Overall Health: {health:.1f}/100")
        lines.append(f"")
        lines.append(f"- **Best Module:** {self.summary.get('best_module', 'N/A')} ({self.summary.get('best_score', 0):.1f})")
        lines.append(f"- **Worst Module:** {self.summary.get('worst_module', 'N/A')} ({self.summary.get('worst_score', 0):.1f})")
        lines.append(f"")

        # Technical Debt
        debt_ratio = self.summary.get('debt_ratio', 0)
        sqale = self.summary.get('sqale_rating', 'A')
        debt_emoji = self._get_debt_emoji(sqale)
        lines.append(f"### {debt_emoji} Technical Debt: {debt_ratio:.1f}% (Rating: {sqale})")
        lines.append(f"")
        lines.append(f"- **Remediation Time:** {self.summary.get('total_remediation_hours', 0):.1f} hours ({self.summary.get('total_remediation_days', 0):.1f} days)")
        lines.append(f"")

        # Key Metrics
        lines.append(f"## Key Metrics")
        lines.append(f"")

        # Database Coupling
        lines.append(f"### 🔗 Database Coupling")
        lines.append(f"")
        lines.append(f"- **Total Operations:** {self.summary.get('total_operations', 0)}")
        lines.append(f"- **Severity Score:** {self.summary.get('severity_score', 0)}")
        lines.append(f"- **Critical Violations (Writes):** {self.summary.get('violation_count_write', 0)} 🔴")
        lines.append(f"- **Warnings (Reads):** {self.summary.get('violation_count_read', 0)} 🟡")
        lines.append(f"")

        # Code Quality
        lines.append(f"### 📊 Code Quality")
        lines.append(f"")
        lines.append(f"- **Average Complexity:** {self.summary.get('avg_complexity', 0):.1f}")
        lines.append(f"- **High Complexity Functions:** {self.summary.get('high_complexity_count', 0)}")
        lines.append(f"- **Average Maintainability:** {self.summary.get('avg_mi', 0):.1f}/100")
        lines.append(f"- **Low Maintainability Files:** {self.summary.get('low_mi_count', 0)}")
        lines.append(f"")

        # Code Size
        lines.append(f"### 📏 Code Size")
        lines.append(f"")
        lines.append(f"- **Total SLOC:** {self.summary.get('total_sloc', 0):,}")
        lines.append(f"- **Average File Size:** {self.summary.get('avg_file_size', 0):.1f} LOC")
        lines.append(f"- **Comment Ratio:** {self.summary.get('comment_ratio', 0):.1f}%")
        lines.append(f"- **Large Files (>500 LOC):** {self.summary.get('large_files_count', 0)}")
        lines.append(f"")

        # Tests
        lines.append(f"### 🧪 Tests")
        lines.append(f"")
        lines.append(f"- **Test Files:** {self.summary.get('total_test_files', 0)}")
        lines.append(f"- **Unit Tests:** {self.summary.get('unit_percentage', 0):.1f}%")
        lines.append(f"- **Integration Tests:** {self.summary.get('integration_percentage', 0):.1f}%")
        lines.append(f"- **Testability Score:** {self.summary.get('testability_score', 0):.1f}%")
        lines.append(f"")

        # Code Smells
        lines.append(f"### 👃 Code Smells")
        lines.append(f"")
        lines.append(f"- **Total Smells:** {self.summary.get('total_smells', 0)}")
        lines.append(f"  - Long Methods: {self.summary.get('long_methods', 0)}")
        lines.append(f"  - Long Parameter Lists: {self.summary.get('long_parameter_lists', 0)}")
        lines.append(f"  - Deep Nesting: {self.summary.get('deep_nesting', 0)}")
        lines.append(f"")

        # Class Metrics
        lines.append(f"### 🏛️ Class Metrics")
        lines.append(f"")
        lines.append(f"- **Total Classes:** {self.summary.get('total_classes', 0)}")
        lines.append(f"- **God Classes:** {self.summary.get('god_classes_count', 0)} 🔴")
        lines.append(f"- **Low Cohesion Classes:** {self.summary.get('low_cohesion_count', 0)}")
        lines.append(f"- **Average LCOM:** {self.summary.get('avg_lcom', 0):.2f}")
        lines.append(f"- **Average WMC:** {self.summary.get('avg_wmc', 0):.1f}")
        lines.append(f"")

        # Module Rankings
        module_health = self.results.get('module_health', {})
        rankings = module_health.get('module_rankings', [])
        if rankings:
            lines.append(f"## Module Rankings")
            lines.append(f"")
            lines.append(f"| Rank | Module | Health Score | Category |")
            lines.append(f"|------|--------|--------------|----------|")
            for idx, ranking in enumerate(rankings, 1):
                category_emoji = self._get_category_emoji(ranking.get('category', ''))
                lines.append(
                    f"| {idx} | {ranking.get('module', 'Unknown')} | "
                    f"{ranking.get('score', 0):.1f} | {category_emoji} {ranking.get('category', 'unknown').title()} |"
                )
            lines.append(f"")

        # Footer
        lines.append(f"---")
        lines.append(f"*Generated by COBANA - Codebase Architecture Analysis Tool*")

        return "\n".join(lines)

    def _get_health_emoji(self, score: float) -> str:
        """Get emoji for health score."""
        if score >= 80:
            return "🟢"
        elif score >= 60:
            return "🟡"
        elif score >= 40:
            return "🟠"
        else:
            return "🔴"

    def _get_debt_emoji(self, rating: str) -> str:
        """Get emoji for SQALE rating."""
        match rating:
            case 'A' | 'B':
                return "🟢"
            case 'C':
                return "🟡"
            case 'D':
                return "🟠"
            case _:
                return "🔴"

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for health category."""
        match category.lower():
            case 'excellent':
                return "🌟"
            case 'good':
                return "✅"
            case 'warning':
                return "⚠️"
            case 'critical':
                return "🔴"
            case _:
                return "🆘"
