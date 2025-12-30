"""Command-line interface for COBANA.

Provides the main entry point for running codebase analysis from the command line.
"""

import argparse
import sys
from pathlib import Path
import logging

from cobana.analyzer import CodebaseAnalyzer
from cobana.report.json_generator import JSONReportGenerator
from cobana.report.md_generator import MarkdownReportGenerator
from cobana.report.html_generator import HtmlReportGenerator

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog='cobana',
        description='COBANA - Codebase Architecture Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cobana /path/to/backend
  cobana /path/to/backend --output report.html
  cobana /path/to/backend --config custom.yaml --output analysis.html --json data.json
  cobana /path/to/backend --service-name claims --markdown summary.md --verbose
  cobana /path/to/backend --html report.html --json data.json --markdown summary.md
  cobana /path/to/backend --output report.html --max-items 50
  cobana /path/to/backend --tests-dir tests --output report.html
  cobana /path/to/backend --tests-dir /absolute/path/to/tests --verbose
        """
    )

    # Required arguments
    parser.add_argument(
        'path',
        type=str,
        help='Path to codebase root directory'
    )

    # Optional arguments
    parser.add_argument(
        '--config',
        type=str,
        metavar='FILE',
        help='Configuration file (default: config.yaml if exists)'
    )

    parser.add_argument(
        '--output',
        '--html',
        type=str,
        metavar='FILE',
        dest='output',
        help='HTML report output (optional)'
    )

    parser.add_argument(
        '--json',
        type=str,
        metavar='FILE',
        help='JSON data output (optional)'
    )

    parser.add_argument(
        '--markdown',
        '--md',
        type=str,
        metavar='FILE',
        dest='markdown',
        help='Markdown summary output (optional)'
    )

    parser.add_argument(
        '--service-name',
        type=str,
        metavar='NAME',
        help='Service name for ownership analysis'
    )

    parser.add_argument(
        '--module-depth',
        type=int,
        metavar='N',
        default=1,
        help='Folder depth for module detection (default: 1)'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        metavar='N',
        help='Maximum folder depth for file analysis (default: unlimited). '
             'Depth 1 = only root files, 2 = root + 1 level, 3 = root + 2 levels, etc.'
    )

    parser.add_argument(
        '--tests-dir',
        type=str,
        metavar='PATH',
        help='Path to tests directory (default: auto-detect). '
             'Can be absolute or relative to codebase root. '
             'If not specified, will search for common test directory names (tests/, test/, etc.)'
    )

    parser.add_argument(
        '--max-items',
        type=int,
        metavar='N',
        default=0,
        help='Maximum number of items to display in HTML report lists (default: 0 = unlimited)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        metavar='FILE',
        default='cobana.log',
        help='Log file path with rotation (default: cobana.log)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show progress during analysis'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='COBANA 1.0.0'
    )

    return parser


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Validate path
    codebase_path = Path(args.path)
    if not codebase_path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    if not codebase_path.is_dir():
        print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
        return 1

    try:
        # Initialize analyzer
        print(f"🔍 Analyzing codebase: {codebase_path}")
        print(f"📝 Logging to: {Path(args.log_file).resolve()}")
        print()

        analyzer = CodebaseAnalyzer(
            root_path=codebase_path,
            config_path=args.config,
            verbose=args.verbose,
            log_file=args.log_file,
            tests_dir=args.tests_dir
        )

        # Override config with CLI arguments if provided
        if args.service_name:
            analyzer.config['service_name'] = args.service_name

        if args.module_depth:
            analyzer.config['module_detection']['depth'] = args.module_depth

        if args.max_depth:
            analyzer.config['max_depth'] = args.max_depth

        # Run analysis
        results = analyzer.analyze()

        # Print summary to console
        print_summary(results)

        # Generate reports
        if args.output:
            html_generator = HtmlReportGenerator(results, max_items=args.max_items)
            html_generator.generate(args.output)
            print(f"\n✅ HTML report saved to: {args.output}")
            if args.max_items > 0:
                print(f"   (Limited to {args.max_items} items per list)")

        if args.json:
            json_generator = JSONReportGenerator(results)
            json_generator.generate(args.json)
            print(f"✅ JSON report saved to: {args.json}")

        if args.markdown:
            md_generator = MarkdownReportGenerator(results)
            md_generator.generate(args.markdown)
            print(f"✅ Markdown summary saved to: {args.markdown}")

        # Suggest next steps if no output specified
        if not any([args.json, args.markdown, args.output]):
            print(f"\n💡 Tip: Use --output, --json, or --markdown to save detailed reports")
            print(f"   Example: cobana {args.path} --output report.html --json analysis.json")

        return 0

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Analysis interrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def print_summary(results: dict) -> None:
    """Print analysis summary to console.

    Args:
        results: Analysis results
    """
    summary = results.get('summary', {})
    metadata = results.get('metadata', {})

    print("=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print()

    print(f"Service: {metadata.get('service_name', 'Unknown')}")
    print(f"Files Analyzed: {metadata.get('total_files_analyzed', 0)}")
    print(f"Modules: {metadata.get('module_count', 0)}")
    print()

    # Overall Health
    health = summary.get('overall_health', 0)
    health_status = get_health_status(health)
    print(f"Overall Health: {health:.1f}/100 {health_status}")
    print()

    # Technical Debt
    debt_ratio = summary.get('debt_ratio', 0)
    sqale = summary.get('sqale_rating', 'A')
    debt_status = get_debt_status(sqale)
    print(f"Technical Debt: {debt_ratio:.1f}% (SQALE Rating: {sqale}) {debt_status}")
    print(f"  Remediation Time: {summary.get('total_remediation_hours', 0):.1f} hours")
    print()

    # Database Coupling
    print("Database Coupling:")
    print(f"  Total Operations: {summary.get('total_operations', 0)}")
    print(f"  Critical Violations: {summary.get('violation_count_write', 0)} 🔴")
    print(f"  Warnings: {summary.get('violation_count_read', 0)} 🟡")
    print()

    # Code Quality
    print("Code Quality:")
    print(f"  Avg Complexity: {summary.get('avg_complexity', 0):.1f}")
    print(f"  High Complexity Functions: {summary.get('high_complexity_count', 0)}")
    print(f"  Avg Maintainability: {summary.get('avg_mi', 0):.1f}/100")
    print()

    # Tests
    tests = results.get('tests', {})
    total_test_files = tests.get('total_test_files', 0)
    total_test_functions = tests.get('total_test_functions', 0)

    print("Tests:")
    print(f"  Test Files Found: {total_test_files}")
    print(f"  Test Functions Found: {total_test_functions}")
    print(f"  Unit Tests: {summary.get('unit_percentage', 0):.1f}%")
    print(f"  Integration Tests: {summary.get('integration_percentage', 0):.1f}%")
    print(f"  Testability Score: {summary.get('testability_score', 0):.1f}%")
    print()

    # Edge Case Testing
    edge_pct = summary.get('edge_case_percentage', 0)
    edge_status = "🟢" if edge_pct >= 30 else "🟡" if edge_pct >= 15 else "🔴"
    print("Edge Case Testing:")
    print(f"  Edge Case Coverage: {edge_pct:.1f}% {edge_status}")
    print(f"  Edge Case Tests: {summary.get('total_edge_case_tests', 0)}")
    print(f"  Happy Path Tests: {summary.get('total_happy_path_tests', 0)}")
    if edge_pct < 30:
        print(f"  ⚠️  Warning: Low edge case coverage (recommended: ≥30%)")
    print()

    # Top Module
    best_module = summary.get('best_module')
    worst_module = summary.get('worst_module')
    if best_module and worst_module:
        print("Module Rankings:")
        print(f"  Best: {best_module} ({summary.get('best_score', 0):.1f})")
        print(f"  Worst: {worst_module} ({summary.get('worst_score', 0):.1f})")
        print()

    print("=" * 70)


def get_health_status(score: float) -> str:
    """Get health status emoji/text.

    Args:
        score: Health score

    Returns:
        Status string
    """
    if score >= 80:
        return "🟢 Excellent"
    elif score >= 60:
        return "🟡 Good"
    elif score >= 40:
        return "🟠 Warning"
    else:
        return "🔴 Critical"


def get_debt_status(rating: str) -> str:
    """Get debt status emoji/text.

    Args:
        rating: SQALE rating

    Returns:
        Status string
    """
    match rating:
        case 'A':
            return "🟢 Excellent"
        case 'B':
            return "🟢 Good"
        case 'C':
            return "🟡 Moderate"
        case 'D':
            return "🟠 High"
        case _:
            return "🔴 Critical"


if __name__ == '__main__':
    sys.exit(main())
