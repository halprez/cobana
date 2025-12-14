"""HTML template for COBANA reports."""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report - {{ metadata.service_name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }

        header {
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        h1 {
            color: #007bff;
            font-size: 2.5em;
            margin-bottom: 15px;
        }

        .metadata {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            color: #666;
        }

        .metadata p {
            margin: 5px 0;
        }

        nav {
            background: #007bff;
            padding: 15px;
            margin: 30px -40px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        nav a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }

        nav a:hover {
            background: rgba(255,255,255,0.2);
        }

        section {
            margin: 40px 0;
            padding: 30px 0;
            border-bottom: 1px solid #eee;
        }

        h2 {
            color: #333;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }

        h3 {
            color: #555;
            font-size: 1.5em;
            margin: 25px 0 15px 0;
        }

        h4 {
            color: #666;
            font-size: 1.2em;
            margin: 15px 0 10px 0;
        }

        .metric-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }

        .metric-card.success {
            border-left-color: #28a745;
        }

        .metric-card.warning {
            border-left-color: #ffc107;
        }

        .metric-card.danger {
            border-left-color: #dc3545;
        }

        .metric-card h4 {
            color: #666;
            font-size: 0.9em;
            margin: 0 0 10px 0;
            text-transform: uppercase;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }

        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .explanation-box {
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }

        .explanation-box h3 {
            color: #007bff;
            margin-top: 0;
        }

        .explanation-box p {
            margin: 10px 0;
        }

        .explanation-box ul {
            margin: 10px 0 10px 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        th {
            background: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-success {
            background: #d4edda;
            color: #155724;
        }

        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }

        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }

        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        canvas {
            max-width: 100%;
            height: auto !important;
        }

        details {
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
        }

        summary {
            cursor: pointer;
            font-weight: 600;
            font-size: 1.1em;
            color: #007bff;
            padding: 10px;
            user-select: none;
        }

        summary:hover {
            background: #f8f9fa;
        }

        .issue-list {
            margin: 15px 0;
        }

        .issue-item {
            padding: 10px;
            margin: 8px 0;
            background: #f8f9fa;
            border-left: 3px solid #ffc107;
            border-radius: 4px;
        }

        .issue-item.critical {
            border-left-color: #dc3545;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        @media print {
            nav {
                position: static;
            }
            details {
                border: none;
            }
            details[open] summary {
                display: none;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            .metric-cards {
                grid-template-columns: 1fr;
            }
            nav {
                margin: 20px -20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Codebase Architecture Analysis</h1>
            <div class="metadata">
                <p><strong>Service:</strong> {{ metadata.service_name }}</p>
                <p><strong>Analysis Date:</strong> {{ analysis_date }}</p>
                <p><strong>Files Analyzed:</strong> {{ metadata.total_files_analyzed }}</p>
                <p><strong>Modules:</strong> {{ metadata.module_count }}</p>
            </div>
        </header>

        <nav>
            <a href="#executive-summary">📊 Summary</a>
            <a href="#module-overview">📦 Modules</a>
            <a href="#database-coupling">🔗 DB Coupling</a>
            <a href="#complexity">📊 Complexity</a>
            <a href="#maintainability">🔧 Maintainability</a>
            <a href="#tests">🧪 Tests</a>
            <a href="#code-smells">👃 Code Smells</a>
            <a href="#technical-debt">💰 Tech Debt</a>
        </nav>

        <section id="executive-summary">
            <h2>📊 Executive Summary</h2>

            <div class="metric-cards">
                <div class="metric-card {{ 'success' if summary.get('overall_health', 0) >= 80 else 'warning' if summary.get('overall_health', 0) >= 60 else 'danger' }}">
                    <h4>Overall Health</h4>
                    <div class="metric-value">{{ "%.1f"|format(summary.get('overall_health', 0)) }}/100</div>
                    <div class="metric-label">
                        {% if summary.get('overall_health', 0) >= 80 %}🟢 Excellent
                        {% elif summary.get('overall_health', 0) >= 60 %}🟡 Good
                        {% elif summary.get('overall_health', 0) >= 40 %}🟠 Warning
                        {% else %}🔴 Critical{% endif %}
                    </div>
                </div>

                <div class="metric-card {{ 'success' if summary.get('sqale_rating', 'A') in ['A', 'B'] else 'warning' if summary.get('sqale_rating', 'A') == 'C' else 'danger' }}">
                    <h4>Technical Debt</h4>
                    <div class="metric-value">{{ "%.1f"|format(summary.get('debt_ratio', 0)) }}%</div>
                    <div class="metric-label">Rating: {{ summary.get('sqale_rating', 'A') }} | {{ "%.1f"|format(summary.get('total_remediation_hours', 0)) }} hours</div>
                </div>

                <div class="metric-card {{ 'danger' if summary.get('violation_count_write', 0) > 0 else 'warning' if summary.get('violation_count_read', 0) > 0 else 'success' }}">
                    <h4>DB Coupling</h4>
                    <div class="metric-value">{{ summary.get('total_operations', 0) }}</div>
                    <div class="metric-label">
                        🔴 {{ summary.get('violation_count_write', 0) }} writes |
                        🟡 {{ summary.get('violation_count_read', 0) }} reads
                    </div>
                </div>

                <div class="metric-card {{ 'success' if summary.get('avg_complexity', 0) < 6 else 'warning' if summary.get('avg_complexity', 0) < 11 else 'danger' }}">
                    <h4>Average Complexity</h4>
                    <div class="metric-value">{{ "%.1f"|format(summary.get('avg_complexity', 0)) }}</div>
                    <div class="metric-label">{{ summary.get('high_complexity_count', 0) }} high complexity functions</div>
                </div>
            </div>

            <div class="chart-container">
                <h3>Module Health Comparison</h3>
                <canvas id="moduleHealthChart"></canvas>
            </div>
        </section>

        {% include 'module_overview_section.html' ignore missing %}

        {% include 'db_coupling_section.html' ignore missing %}

        {% include 'complexity_section.html' ignore missing %}

        {% include 'maintainability_section.html' ignore missing %}

        {% include 'code_size_section.html' ignore missing %}

        {% include 'tests_section.html' ignore missing %}

        {% include 'code_smells_section.html' ignore missing %}

        {% include 'technical_debt_section.html' ignore missing %}

        <footer style="margin-top: 60px; padding-top: 30px; border-top: 2px solid #eee; text-align: center; color: #666;">
            <p>Generated by <strong>COBANA</strong> - Codebase Architecture Analysis Tool</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Report generated on {{ analysis_date }}</p>
        </footer>
    </div>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Module Health Chart
        const moduleData = {{ module_rankings | tojson }};

        if (moduleData && moduleData.length > 0) {
            const ctx = document.getElementById('moduleHealthChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: moduleData.map(m => m.module),
                        datasets: [{
                            label: 'Health Score',
                            data: moduleData.map(m => m.score),
                            backgroundColor: moduleData.map(m => {
                                if (m.score >= 80) return 'rgba(40, 167, 69, 0.8)';
                                if (m.score >= 60) return 'rgba(255, 193, 7, 0.8)';
                                if (m.score >= 40) return 'rgba(255, 152, 0, 0.8)';
                                return 'rgba(220, 53, 69, 0.8)';
                            }),
                            borderColor: moduleData.map(m => {
                                if (m.score >= 80) return 'rgba(40, 167, 69, 1)';
                                if (m.score >= 60) return 'rgba(255, 193, 7, 1)';
                                if (m.score >= 40) return 'rgba(255, 152, 0, 1)';
                                return 'rgba(220, 53, 69, 1)';
                            }),
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                title: {
                                    display: true,
                                    text: 'Health Score (0-100)'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            title: {
                                display: false
                            }
                        }
                    }
                });
            }
        }
    </script>
</body>
</html>
"""
