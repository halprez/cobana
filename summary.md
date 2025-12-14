# Codebase Analysis Report

**Service:** unknown
**Analysis Date:** 2025-12-14 08:23:53
**Files Analyzed:** 23
**Modules:** 4

## Executive Summary

### 🟡 Overall Health: 77.9/100

- **Best Module:** utils (83.3)
- **Worst Module:** analyzers (71.4)

### 🟢 Technical Debt: 6.3% (Rating: B)

- **Remediation Time:** 24.2 hours (3.0 days)

## Key Metrics

### 🔗 Database Coupling

- **Total Operations:** 0
- **Severity Score:** 0
- **Critical Violations (Writes):** 0 🔴
- **Warnings (Reads):** 0 🟡

**📚 What is this?**

Database coupling measures how tightly code is tied to database access. When services directly access each other's tables, they become 'coupled' - changes in one can break another.

**⚡ Why it matters:**

- **Independent Deployment:** Coupled services can't deploy separately
- **Test Speed:** Coupled code requires slow integration tests instead of fast unit tests
- **Reliability:** Changes to shared tables can break multiple services


### 📊 Code Complexity

- **Average Complexity:** 3.6
- **High Complexity Functions:** 5
- **Max Complexity:** 15

**📚 What is this?**

Cyclomatic complexity measures the number of independent paths through code. Higher complexity means more testing needed and harder to understand.

**⚡ Why it matters:**

- **Testability:** Complex functions are harder to test thoroughly
- **Bugs:** High complexity correlates with more defects
- **Maintenance:** Complex code takes longer to modify safely

**Thresholds:** 1-5 (✅ Simple), 6-10 (⚠️ Moderate), 11-20 (🟠 Complex), 21+ (🔴 Very Complex)

**🔴 High Complexity Functions:**

- 🟠 `_calculate_lcom` (complexity: 15) - `/home/al3x/src/cobana/cobana/analyzers/class_metrics.py:206`
- 🟠 `main` (complexity: 13) - `/home/al3x/src/cobana/cobana/cli.py:117`
- 🟠 `_analyze_class` (complexity: 13) - `/home/al3x/src/cobana/cobana/analyzers/class_metrics.py:96`
- 🟠 `_update_results` (complexity: 12) - `/home/al3x/src/cobana/cobana/analyzers/complexity.py:177`
- 🟠 `finalize_results` (complexity: 11) - `/home/al3x/src/cobana/cobana/analyzers/module_coupling.py:98`


### 🔧 Maintainability

- **Average Maintainability Index:** 69.4/100
- **Low Maintainability Files:** 0

**📚 What is this?**

Maintainability Index (0-100) combines complexity, code size, and documentation to estimate how easy code is to maintain.

**⚡ Why it matters:**

- **Developer Velocity:** Low maintainability slows down development
- **Onboarding:** New developers struggle with unmaintainable code
- **Technical Debt:** Low scores indicate accumulating debt

**Thresholds:** 65-100 (✅ High), 20-64 (⚠️ Moderate), 0-19 (🔴 Low)


### 📏 Code Size

- **Total SLOC:** 3,849
- **Average File Size:** 167.3 LOC
- **Comment Ratio:** 5.9%
- **Large Files (>500 LOC):** 1

**📚 What is this?**

Source Lines of Code (SLOC) and file size metrics help identify overly large files that may need splitting.

**⚡ Why it matters:** Large files often indicate mixed responsibilities and are harder to navigate and test.

**🟠 Large Files (>500 LOC):**

- `/home/al3x/src/cobana/cobana/report/html_generator.py` (633 LOC)


### 🧪 Tests

- **Test Files:** 0
- **Unit Tests:** 0.0%
- **Integration Tests:** 0.0%
- **Testability Score:** 100.0%

**📚 What is this?**

Test analysis categorizes tests (unit vs integration) and measures testability - what percentage of code can be unit tested without database access.

**⚡ Why it matters:**

- **Fast Feedback:** Unit tests run in milliseconds, integration tests in seconds/minutes
- **Reliability:** Untestable code (mixed with DB access) is harder to verify
- **Refactoring:** Well-tested code can be safely modified


### 👃 Code Smells

- **Total Smells:** 30
  - Long Methods (>50 LOC): 24
  - Long Parameter Lists (>5 params): 5
  - Deep Nesting (>4 levels): 1

**📚 What is this?**

Code smells are patterns that indicate potential problems: long methods, too many parameters, or deeply nested logic.

**⚡ Why it matters:** These patterns make code harder to understand, test, and modify.

**🟠 Long Methods (>50 LOC):**

- `create_parser` (96 LOC) - `root` (line 19)
- `_create_code_smells_template` (95 LOC) - `report` (line 590)
- `_create_technical_debt_template` (90 LOC) - `report` (line 686)
- `_analyze_class` (90 LOC) - `analyzers` (line 96)
- `finalize_results` (90 LOC) - `analyzers` (line 98)
- `get_markdown` (88 LOC) - `report` (line 41)
- `_categorize_operations` (87 LOC) - `analyzers` (line 216)
- `main` (79 LOC) - `root` (line 117)
- `_calculate_module_health` (76 LOC) - `analyzers` (line 101)
- `_create_db_coupling_template` (73 LOC) - `report` (line 325)
  _(... and 14 more)_


### 🏛️ Class Metrics

- **Total Classes:** 22
- **God Classes (>20 methods):** 2 🔴
- **Low Cohesion Classes:** 0
- **Average LCOM:** 1.36
- **Average WMC:** 22.1

**📚 What is this?**

- **God Classes:** Classes with too many methods (>20), indicating too many responsibilities
- **LCOM (Lack of Cohesion):** Measures if class methods use the same data (lower is better)
- **WMC (Weighted Methods per Class):** Sum of method complexities

**⚡ Why it matters:** God classes violate Single Responsibility Principle and are hard to maintain.

**🔴 God Classes:**

- `MarkdownReportGenerator` (14 methods, WMC: 57) - `/home/al3x/src/cobana/cobana/report/md_generator.py:14`
- `ClassMetricsAnalyzer` (9 methods, WMC: 52) - `/home/al3x/src/cobana/cobana/analyzers/class_metrics.py:19`


## Module-Level Breakdown

Detailed metrics for each module to identify areas needing attention.

### 🟡 Module: `analyzers` (Health: 71.4/100)

| Metric | Value |
|--------|-------|
| Complexity | 3.6 avg |
| Maintainability | 61.7/100 |
| DB Operations | 0 |
| DB Severity | 0 |
| Code Smells | 18 |
| Test Files | 0 |

### 🟡 Module: `report` (Health: 79.1/100)

| Metric | Value |
|--------|-------|
| Complexity | 2.9 avg |
| Maintainability | 77.7/100 |
| DB Operations | 0 |
| DB Severity | 0 |
| Code Smells | 9 |
| Test Files | 0 |

### 🟢 Module: `utils` (Health: 83.3/100)

| Metric | Value |
|--------|-------|
| Complexity | 4.4 avg |
| Maintainability | 71.1/100 |
| DB Operations | 0 |
| DB Severity | 0 |
| Code Smells | 0 |
| Test Files | 0 |


## Module Rankings

| Rank | Module | Health Score | Category |
|------|--------|--------------|----------|
| 1 | analyzers | 71.4 | ✅ Good |
| 2 | report | 79.1 | ✅ Good |
| 3 | utils | 83.3 | 🌟 Excellent |

---
*Generated by COBANA - Codebase Architecture Analysis Tool*