"""JSON Report Generator

Generates machine-readable JSON reports from analysis results.
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JSONReportGenerator:
    """Generates JSON reports from analysis results."""

    def __init__(self, results: dict[str, Any]):
        """Initialize generator.

        Args:
            results: Complete analysis results
        """
        self.results = results

    def generate(self, output_path: Path | str) -> None:
        """Generate JSON report and save to file.

        Args:
            output_path: Path where to save the JSON report
        """
        output_path = Path(output_path)

        # Add timestamp
        report_data = {
            'analysis_date': datetime.now().isoformat(),
            **self.results,
        }

        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"JSON report generated: {output_path}")

    def get_json_string(self, pretty: bool = True) -> str:
        """Get JSON report as string.

        Args:
            pretty: Whether to pretty-print the JSON

        Returns:
            JSON string
        """
        report_data = {
            'analysis_date': datetime.now().isoformat(),
            **self.results,
        }

        if pretty:
            return json.dumps(report_data, indent=2, default=str)
        else:
            return json.dumps(report_data, default=str)
