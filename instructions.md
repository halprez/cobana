# Codebase Architecture Analysis Tool - Complete Specification

**Version:** 1.0  
**Date:** 2024-12-13  
**Purpose:** Automated Python codebase analysis tool to measure architectural health, code quality, and technical debt with educational explanations for both technical and non-technical stakeholders. Includes module/folder-level breakdown for targeted improvement.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Input/Output Specifications](#2-inputoutput-specifications)
3. [Metrics Specifications](#3-metrics-specifications)
4. [Data Structures](#4-data-structures)
5. [HTML Report Structure](#5-html-report-structure)
6. [Configuration](#6-configuration)
7. [Technical Requirements](#7-technical-requirements)
8. [Implementation Guidelines](#8-implementation-guidelines)
9. [Success Criteria](#9-success-criteria)

---

## 1. Project Overview

### 1.1 Goals

**Primary Goal:** Provide objective, measurable evidence of architectural issues (database coupling, complexity, testability) to support architectural improvement discussions with both overall and module-level insights.

**Secondary Goals:**
- Educate developers on code quality metrics
- Enable non-technical stakeholders to understand technical health
- Provide actionable recommendations prioritized by impact
- Support data-driven architectural decisions
- Identify which modules need the most attention

### 1.2 Key Principles

1. **Educational:** Every metric includes clear explanations of "what it is" and "why it matters"
2. **Actionable:** Specific files, line numbers, and prioritized recommendations
3. **Visual:** Color-coded severity, charts, and intuitive layout
4. **Objective:** Reproducible measurements, not subjective opinions
5. **Professional:** Suitable for sharing with management and stakeholders
6. **Modular:** Break down analysis by module/folder for targeted improvement

### 1.3 Target Audience

- **Developers:** Need specific issues to fix in their modules
- **Tech Leads:** Need architectural overview and module comparison
- **Managers:** Need high-level health indicators and worst-performing areas
- **CTOs:** Need strategic insights and ROI data by team/module

---

## 2. Input/Output Specifications

### 2.1 Input

**Required:**
- Path to Python codebase root directory

**Optional:**
- Configuration YAML file (defaults available)
- Service name (for ownership categorization)
- Output file paths
- Module detection configuration

**Command Line Interface:**
````bash
python analyze_codebase.py <path> [options]

Arguments:
  path                      Path to codebase root directory (required)

Options:
  --config FILE            Configuration file (default: config.yaml)
  --output FILE            HTML report output (default: report.html)
  --json FILE              JSON data output (optional)
  --markdown FILE          Markdown summary (optional)
  --service-name NAME      Service name for ownership analysis
  --module-depth N         Folder depth for module detection (default: 1)
  --verbose               Show progress during analysis
  --help                  Show help message

Examples:
  python analyze_codebase.py /path/to/backend
  python analyze_codebase.py /path/to/backend --config custom.yaml --output analysis.html
  python analyze_codebase.py /path/to/backend --service-name claims --json data.json --verbose
  python analyze_codebase.py /path/to/backend --module-depth 2
````

### 2.2 Module/Folder Detection

**Automatic Detection:**
The tool automatically detects logical modules based on folder structure.

**Default Behavior:**
- Top-level folders (depth 1) are treated as modules
- Example structure:
````
  backend/
  â”œâ”€â”€ claims/          # Module: "claims"
  â”‚   â”œâ”€â”€ inbound/
  â”‚   â”œâ”€â”€ processing/
  â”‚   â””â”€â”€ validation/
  â”œâ”€â”€ promotions/      # Module: "promotions"
  â”œâ”€â”€ contracts/       # Module: "contracts"
  â”œâ”€â”€ shared/          # Module: "shared"
  â””â”€â”€ utils/           # Module: "utils"
````

**Configurable Depth:**
- Can analyze at different depths (e.g., depth=2 for sub-modules)
- Configurable via CLI `--module-depth` or config file

**Manual Override:**
````yaml
# In config.yaml
module_detection:
  method: "auto"  # or "manual"
  depth: 1        # Folder depth to treat as modules
  
  # Optional: Manually define modules
  manual_modules:
    - name: "Claims Processing"
      path: "claims"
      description: "Inbound claim processing and validation"
    - name: "Promotions Engine"
      path: "promotions"
      description: "Promotion matching and application"
    - name: "Shared Utilities"
      path: "shared"
      description: "Cross-cutting concerns and utilities"
````

### 2.3 Output Files

#### Primary Output: HTML Report
- Self-contained HTML file (embedded CSS/JavaScript)
- Responsive design (mobile/desktop friendly)
- Print-friendly styling
- No external dependencies
- **Includes:**
  - Overall codebase executive summary
  - Module-by-module breakdown
  - Module comparison/ranking
  - Overall metrics
  - Module-specific recommendations

#### Secondary Outputs:
- **JSON:** Machine-readable data for automation (includes module breakdown)
- **Markdown:** Text summary for documentation (includes module summary)

---

## 3. Metrics Specifications

### 3.1 Database Coupling Analysis â­ PRIMARY FOCUS

#### What to Measure

1. **Import Count**
   - Count of `from vf_db import db` statements
   - Files containing these imports
   - Line numbers
   - **Per module and overall**

2. **Database Operations** â­ CRITICAL
   - All database operations: `find()`, `find_one()`, `update()`, `insert()`, etc.
   - Categorize by type: READ or WRITE
   - Which collections/tables accessed
   - File location and line numbers
   - **Per module and overall**

3. **Ownership Analysis**
   - Operations on own tables (acceptable)
   - Operations on shared tables (coupling)
   - Read operations on other services' tables (coupling - warning)
   - Write operations on other services' tables (severe violation - critical)
   - **Per module and overall**

4. **Severity Scoring**
   - Formula: `(other_reads Ã— 1) + (other_writes Ã— 5)`
   - Higher weight for writes (architectural violations)
   - **Per module and overall**

5. **Cross-Module Database Coupling**
   - Track which modules access which tables
   - Identify modules violating other modules' table ownership

#### Detection Logic

**Database Operations to Detect:**

**READ Operations:**
- `db.collection.find()`
- `db.collection.find_one()`
- `db.collection.aggregate()`
- `db.collection.count()`
- `db.collection.count_documents()`
- `db.collection.distinct()`

**WRITE Operations:**
- `db.collection.insert()`
- `db.collection.insert_one()`
- `db.collection.insert_many()`
- `db.collection.update()`
- `db.collection.update_one()`
- `db.collection.update_many()`
- `db.collection.replace_one()`
- `db.collection.delete()`
- `db.collection.delete_one()`
- `db.collection.delete_many()`

**Extraction Pattern:**
````python
# Use regex to find: db.{collection_name}.{method_name}
pattern = r'db\.([a-z_]+)\.(find|find_one|update|insert|delete|aggregate|count|distinct|replace|update_one|update_many|insert_one|insert_many|delete_one|delete_many|replace_one|count_documents)\('
````

#### Report Explanation Template
````markdown
## Database Coupling

### ðŸ“š What is Database Coupling?

Database coupling measures how tightly your code is tied to database access. When multiple services share the same database and directly query each other's tables, they become "coupled" - changes in one service can break another.

**Example of Coupling:**
```python
# Claims service directly accessing Promotions table
def process_claim(claim_id):
    claim = db.claim_current.find_one({'_id': claim_id})  # âœ… Own table
    promo = db.promotions.find_one({'_id': claim['promo_id']})  # ðŸ”´ Other service's table
```

### âš¡ Why It Matters

**Impact on Architecture:**
- **Independent Deployment:** Coupled services can't deploy separately - schema changes affect everyone
- **Test Speed:** Coupled code requires slow integration tests instead of fast unit tests
- **Reliability:** Changes to shared tables can break multiple services unpredictably
- **Trunk-based Development:** Fast tests are essential, but coupling forces slow tests

**Impact on dev pace and predictability:**
- Trunk-based development requires fast feedback loops (seconds, not minutes)
- Monthly stable releases need minimal integration issues
- Predictable velocity requires independent team deployments

### ðŸ“Š Health Indicators

- ðŸŸ¢ **Good:** Services only access their own tables via repository pattern
- ðŸŸ¡ **Warning:** Services read from other services' tables (coupling, but manageable)
- ðŸ”´ **Critical:** Services write to other services' tables (architectural violation, prevents independence)

### Your Results - Overall

**Summary:**
- Total Database Operations: {total_operations}
- Operations on Own Tables: {own_operations} ðŸŸ¢
- Read Operations on Other Tables: {other_reads} ðŸŸ¡
- Write Operations on Other Tables: {other_writes} ðŸ”´
- Severity Score: {severity_score}

### Your Results - By Module

[Table showing each module's DB coupling metrics]
[Bar chart comparing modules]

**Module Breakdown:**
[Expandable sections for each module showing detailed coupling analysis]

**Top Coupled Files:**
[Table showing files ranked by operation count and violations]

**Critical Violations (Write Operations to Other Tables):**
[Detailed list with file, line number, table, operation]

### ðŸŽ¯ What To Do

**Priority 1 - CRITICAL:**
1. Fix the {other_writes} write operations to other services' tables
   - Modules affected: {module_list}
   - Files: {list of files}
   - Create service APIs or events for these operations instead

**Priority 2 - HIGH:**
2. Address read coupling ({other_reads} operations)
   - Implement service APIs or caching for cross-service data needs
   - Consider data denormalization where appropriate

**Priority 3 - MEDIUM:**
3. Refactor business logic away from database access
   - Enables unit testing
   - Reduces integration test dependency

**By Module:**
[Module-specific recommendations]
````

---

### 3.2 Code Complexity

#### What to Measure

1. **Cyclomatic Complexity per Function**
   - Count of independent paths through code
   - Uses Radon library: `cc_visit()`
   - **Per module and overall**

2. **Aggregate Metrics**
   - Average complexity across codebase
   - Average complexity per module
   - Complexity distribution (simple/moderate/complex/very complex)
   - Functions exceeding threshold (default: >10)
   - **Per module and overall**

3. **Per-File Metrics**
   - Average complexity per file
   - Max complexity in file
   - List of high-complexity functions
   - **Per module and overall**

#### Thresholds

- **1-5:** Simple (ðŸŸ¢ Good)
- **6-10:** Moderate (ðŸŸ¡ Acceptable)
- **11-20:** Complex (ðŸŸ¡ Warning - should refactor)
- **21+:** Very Complex (ðŸ”´ Critical - must refactor)

#### Report Explanation Template
````markdown
## Code Complexity

### ðŸ“š What is Cyclomatic Complexity?

Cyclomatic complexity measures the number of independent paths through code. Each decision point (`if`, `elif`, `while`, `for`, `and`, `or`, `except`) adds to the complexity count.

**Example:**
```python
# Complexity = 1 (simple, one path)
def greet(name):
    return f"Hello {name}"

# Complexity = 3 (three independent paths)
def greet(name):
    if name is None:           # +1
        return "Hello stranger"
    elif name == "Admin":      # +1
        return "Hello Admin!"
    else:
        return f"Hello {name}"

# Complexity = 8 (very complex)
def process_claim(claim):
    if claim is None:          # +1
        return error
    if not claim.get('name'):  # +1
        return error
    if claim['amount'] < 0:    # +1
        return error
    if claim['status'] == 'pending' and claim['amount'] > 1000:  # +2 (and)
        if claim.get('approved_by'):  # +1
            process_large_claim()
        else:
            return error
    elif claim['status'] == 'approved':  # +1
        finalize_claim()
    return success
```

### âš¡ Why It Matters

**Impact on Quality:**
- **Understandability:** High complexity = hard to understand logic flow
- **Testing:** Each path needs a test case (complexity 20 = 20 test cases minimum)
- **Bugs:** Studies show defect density increases exponentially with complexity
- **Maintenance:** Complex code takes 2-5x longer to modify safely

**Impact on Velocity:**
- Developers spend more time understanding complex code
- More bugs require more debugging time
- Changes are riskier, requiring more testing

### ðŸ“Š Thresholds

- ðŸŸ¢ **1-5:** Simple - Easy to understand and test
- ðŸŸ¡ **6-10:** Moderate - Manageable, acceptable
- ðŸŸ¡ **11-20:** Complex - Should be refactored
- ðŸ”´ **21+:** Very Complex - Must be refactored, high bug risk

### Your Results - Overall

**Summary:**
- Average Complexity: {avg_complexity}
- Total Functions: {total_functions}
- Simple (1-5): {simple_count} functions ðŸŸ¢
- Moderate (6-10): {moderate_count} functions ðŸŸ¡
- Complex (11-20): {complex_count} functions ðŸŸ¡
- Very Complex (21+): {very_complex_count} functions ðŸ”´

### Your Results - By Module

[Table comparing modules by average complexity]
[Chart showing complexity distribution per module]

**Module Breakdown:**
[Expandable sections for each module]

**Highest Complexity Functions:**
[Table: Function name, Module, File, Complexity, Line number]

### ðŸŽ¯ What To Do

**Overall:**
1. **Refactor very complex functions first** (complexity > 20)
   - Break into smaller functions
   - Extract complex conditionals into well-named helper functions
   - Use early returns to reduce nesting

2. **Add tests to complex functions** before refactoring
   - Document current behavior
   - Ensure refactoring doesn't break functionality

3. **Set complexity budget** for new code
   - Enforce max complexity 10 in code reviews
   - Use linters to prevent complexity creep

**By Module:**
[Module-specific complexity reduction recommendations]
````

---

### 3.3 Maintainability Index

#### What to Measure

1. **MI Score per File** (0-100 scale)
   - Uses Radon library: `mi_visit()`
   - Combines: Halstead Volume, Cyclomatic Complexity, Lines of Code
   - **Per module and overall**

2. **Aggregate Metrics**
   - Average MI across codebase
   - Average MI per module
   - Distribution (high/moderate/low)
   - Files below threshold (default: <20)
   - **Per module and overall**

3. **Contributing Factors**
   - High complexity contribution
   - Large file contribution
   - Low comment contribution

#### Formula
````
MI = max(0, (171 - 5.2 Ã— ln(HV) - 0.23 Ã— CC - 16.2 Ã— ln(LOC)) Ã— 100 / 171)

Where:
- HV = Halstead Volume
- CC = Cyclomatic Complexity
- LOC = Lines of Code
````

#### Thresholds

- **65-100:** Highly maintainable (ðŸŸ¢ Good)
- **20-64:** Moderately maintainable (ðŸŸ¡ Acceptable)
- **0-19:** Difficult to maintain (ðŸ”´ Critical)

#### Report Explanation Template
````markdown
## Maintainability Index

### ðŸ“š What is Maintainability Index?

A calculated score (0-100) that combines multiple factors:
- **Lines of code** - Larger files are harder to maintain
- **Cyclomatic complexity** - Complex code is harder to change safely
- **Halstead volume** - Measures code "size" based on operators/operands
- **Comment density** - Well-commented code is easier to understand

**Think of it as:** A health score for each file.

### âš¡ Why It Matters

Low MI means the file is:
- âŒ Difficult to understand when reading
- âŒ Expensive to modify without introducing bugs
- âŒ Hard to test thoroughly
- âŒ Requires experienced developers (can't onboard juniors easily)

**Business Impact:**
- High MI files: 1-2 hours to make changes
- Low MI files: 1-2 days to make changes (5-10x slower)

### ðŸ“Š Thresholds

- ðŸŸ¢ **65-100:** Highly maintainable - Easy to work with
- ðŸŸ¡ **20-64:** Moderately maintainable - Manageable but could improve
- ðŸ”´ **0-19:** Difficult to maintain - Major refactoring needed

### Your Results - Overall

**Summary:**
- Average MI: {avg_mi}
- Highly Maintainable (65-100): {high_count} files ðŸŸ¢
- Moderately Maintainable (20-64): {moderate_count} files ðŸŸ¡
- Low Maintainability (0-19): {low_count} files ðŸ”´

### Your Results - By Module

[Table comparing modules by average MI]
[Chart showing MI distribution per module]

**Module Rankings:**
- Best Module: {best_module} (MI: {score})
- Worst Module: {worst_module} (MI: {score})

**Lowest Maintainability Files:**
[Table: File, Module, MI Score, Main Issues (complexity/size/comments)]

**Example:**
File: `claim_inbound.py`, Module: `claims`, MI: 12.3 ðŸ”´
- 847 lines (too large)
- Complexity 28 (too complex)
- 8% comments (low documentation)

### ðŸŽ¯ What To Do

**Overall:**
1. **Split large files** (>500 LOC)
   - Separate concerns into multiple modules
   - Extract classes/functions to new files

2. **Reduce complexity** in low-MI files
   - Refactor complex functions
   - Break into smaller, focused pieces

3. **Add documentation**
   - Docstrings for classes and functions
   - Comments for complex logic
   - Target 10-15% comment ratio

**By Module:**
[Module-specific maintainability recommendations]
````

---

### 3.4 Code Size Metrics

#### What to Measure

1. **Source Lines of Code (SLOC)**
   - Non-blank, non-comment lines
   - Uses Radon: `raw_visit()`
   - **Per module and overall**

2. **Comment Lines**
   - Count of comment lines
   - Comment ratio = comments / total lines
   - **Per module and overall**

3. **File Size Distribution**
   - Small (<100 LOC)
   - Medium (100-500 LOC)
   - Large (>500 LOC)
   - **Per module and overall**

4. **Function Size**
   - Functions exceeding 50 LOC
   - **Per module and overall**

#### Report Explanation Template
````markdown
## Code Size

### ðŸ“š What is Code Size?

Physical size measurements:
- **SLOC:** Actual code lines (excluding blank lines and comments)
- **Comment Ratio:** Percentage of lines that are comments
- **Large Files/Functions:** Code beyond recommended limits

### âš¡ Why It Matters

**Large Files (>500 LOC):**
- Hard to navigate and find specific code
- Usually indicate too many responsibilities
- Intimidating for new developers

**Large Functions (>50 LOC):**
- Hard to understand at a glance
- Should be broken into smaller, named pieces
- Difficult to test in isolation

**Low Comments (<5%):**
- Code intent is unclear
- Future maintainers spend more time understanding
- Complex logic is undocumented

### ðŸ“Š Recommendations

- **Files:** Keep under 500 LOC (ideally 200-300)
- **Functions:** Keep under 50 LOC (ideally 10-20)
- **Comments:** Aim for 10-20% comment ratio

### Your Results - Overall

**Summary:**
- Total SLOC: {total_sloc}
- Total Files: {file_count}
- Average File Size: {avg_file_size} LOC
- Comment Ratio: {comment_ratio}%

### Your Results - By Module

[Table showing SLOC, file count, avg file size, comment ratio per module]
[Chart comparing module sizes]

**Module Size Breakdown:**
- Largest Module: {module_name} ({sloc} SLOC)
- Smallest Module: {module_name} ({sloc} SLOC)

**Large Files (>500 LOC):**
[Table: File, Module, LOC, Recommendation]

**Large Functions (>50 LOC):**
[Table: Function, Module, File, LOC, Line Number]

**Low Documentation (<5% comments):**
[Table: File, Module, Comment Ratio]

### ðŸŽ¯ What To Do

**Overall:**
1. **Split large files** into focused modules
2. **Extract large functions** into smaller helpers
3. **Add docstrings** and comments for complex logic

**By Module:**
[Module-specific size reduction recommendations]
````

---

### 3.5 Test Analysis

#### What to Measure

1. **Test File Detection**
   - Files matching: `test_*.py` or `*_test.py`
   - Count of test functions (`def test_*`)
   - **Per module and overall**

2. **Test Categorization**
   - **Integration Test:** Contains `from vf_db import db` OR database fixtures
   - **Unit Test:** No database imports, tests pure logic
   - **Per module and overall**

3. **Testability Score**
   - % of functions that can be unit tested
   - Functions mixing business logic + database access (untestable)
   - **Per module and overall**

#### Detection Logic

**Integration Test Indicators:**
````python
# Has database import
from vf_db import db

# OR has database fixtures
@pytest.fixture
def mock_claim_db():
    ...

# OR uses MongoClient
from mongomock import MongoClient
````

**Untestable Function Indicators:**
````python
# Function contains BOTH:
# 1. Database access (db.collection.find/update/etc.)
# 2. Business logic (if/for/while, calculations, validations)

# Example untestable function:
def validate_claim(claim_id):
    claim = db.claim_current.find_one({'_id': claim_id})  # DB access
    if not claim.get('claim_name'):  # Business logic
        return error
    db.claim_current.update_one(...)  # DB access
````

#### Report Explanation Template
````markdown
## Test Analysis

### ðŸ“š What are Unit vs Integration Tests?

**Unit Tests:**
- Test small pieces of code in isolation
- No database, no network, no file system
- Run in milliseconds
- Can run hundreds in seconds

**Integration Tests:**
- Test components working together
- Require database, services, infrastructure
- Run in seconds to minutes
- Slow down as codebase grows

**Example:**
```python
# Unit Test (fast - milliseconds)
def test_calculate_total():
    result = calculate_total([10, 20, 30])
    assert result == 60

# Integration Test (slow - seconds)
def test_save_claim(mock_db):
    claim = create_claim({'amount': 100})
    save_claim(claim, mock_db)
    saved = mock_db.claim_current.find_one({'_id': claim.id})
    assert saved['amount'] == 100
```

### âš¡ Why It Matters

**Impact on Development Speed:**
- **Unit tests (70%):** Run in seconds, developers run constantly
- **Integration tests (30%):** Run in minutes, developers run before commit
- **All integration (your current state):** Run in 10+ minutes, developers avoid running

**Impact on dev pace and predictability:**
- **Trunk-based development requires:** Fast tests on every merge (seconds)
- **Your current state:** Slow tests (minutes) block frequent merging
- **Result:** Integration issues found late, more debugging, slower velocity

**Ideal Ratio:**
- ðŸŸ¢ **70% unit / 30% integration** - Fast test suite, rapid feedback
- ðŸŸ¡ **50% unit / 50% integration** - Moderate speed
- ðŸ”´ **30% unit / 70% integration** - Slow test suite, blocks velocity

### ðŸ“Š Testability

**Testability Score** measures what percentage of your code CAN be unit tested.

**Why low testability?**
Business logic is mixed with database access:
```python
# Untestable (business logic + DB mixed)
def process_claim(claim_id):
    claim = db.find_one({'_id': claim_id})  # DB
    if claim['amount'] > 1000:  # Business logic
        claim['approved'] = True
    db.update_one(...)  # DB

# Testable (separated)
def should_approve(amount):  # Pure business logic
    return amount > 1000

def process_claim(claim_id, db):
    claim = db.find_one({'_id': claim_id})
    if should_approve(claim['amount']):  # Now can unit test this
        claim['approved'] = True
    db.update_one(...)
```

### Your Results - Overall

**Summary:**
- Total Test Files: {total_test_files}
- Unit Tests: {unit_count} ({unit_percentage}%) ðŸ”´
- Integration Tests: {integration_count} ({integration_percentage}%) ðŸ”´
- **Test Ratio:** {unit_percentage}% unit / {integration_percentage}% integration

**Testability:**
- Functions Analyzed: {total_functions}
- Pure Functions (unit testable): {pure_functions}
- Mixed Functions (require integration tests): {mixed_functions}
- **Testability Score:** {testability_score}% ðŸ”´

### Your Results - By Module

[Table showing test metrics per module]
[Chart comparing test ratios across modules]

**Module Test Quality Rankings:**
- Best Testability: {module_name} ({score}%)
- Worst Testability: {module_name} ({score}%)

**Root Cause:**
Business logic is coupled to database access in {mixed_functions} functions, forcing integration tests.

**Untestable Functions (Sample):**
[Table: Function, Module, File, Reason, DB Operations]

### ðŸŽ¯ What To Do

**Priority 1: Enable Unit Testing**
1. Extract business logic from database access
   - Create pure functions for validation, calculation, business rules
   - These can be unit tested (fast)

2. Use repository pattern
   - Separate data access into repository classes
   - Business logic uses repositories (can be mocked)

**Priority 2: Balance Test Types**
3. Write unit tests for new pure business logic
4. Keep integration tests for:
   - Database access verification
   - End-to-end critical paths
   - Not for business logic testing

**Expected Improvement:**
- Current: 10-minute test suite, can't run on every commit
- After refactoring: 30-second unit tests + 5-minute integration tests
- Result: Enables trunk-based development, faster velocity

**By Module:**
[Module-specific test improvement recommendations]
````

---

### 3.6 Module Coupling

#### What to Measure

1. **Afferent Coupling (Ca)**
   - Number of modules that import this module
   - "Fan-in" - who depends on you
   - **Per module**

2. **Efferent Coupling (Ce)**
   - Number of modules this module imports
   - "Fan-out" - who you depend on
   - **Per module**

3. **Instability (I)**
   - Formula: `I = Ce / (Ca + Ce)`
   - Range: 0 (stable) to 1 (unstable)
   - **Per module**

4. **High Coupling Indicators**
   - Modules with Ce > 10 (high fan-out)
   - Modules with Ca > 20 (many dependents)

5. **Cross-Module Dependencies**
   - Which modules depend on which
   - Import graph visualization
   - Circular dependencies between modules

#### Calculation Logic
````python
# For each module:
# 1. Count modules that import it (Ca)
# 2. Count modules it imports (Ce)
# 3. Calculate I = Ce / (Ca + Ce)

# Example:
# module_a/ imported by: module_b/, module_c/, module_d/ (Ca = 3)
# module_a/ imports: module_e/, module_f/ (Ce = 2)
# Instability = 2 / (3+2) = 0.4 (moderately stable)
````

#### Report Explanation Template
````markdown
## Module Coupling

### ðŸ“š What is Module Coupling?

Coupling measures dependencies between modules:
- **Afferent Coupling (Ca):** How many modules import THIS module
- **Efferent Coupling (Ce):** How many modules THIS module imports
- **Instability (I):** How resistant to change (0 = stable, 1 = unstable)

**Example:**
```python
# claims/ module
from promotions import Promotion  # Ce += 1
from contracts import Contract    # Ce += 1

# shared/, utils/, reporting/ modules import claims (Ca = 3)
# Instability = 2 / (3+2) = 0.4 (moderately stable)
```

### âš¡ Why It Matters

**Stable Modules (I < 0.3):**
- Many modules depend on them (high Ca)
- Hard to change (breaks many dependents)
- Should be: Abstract, well-designed interfaces

**Unstable Modules (I > 0.7):**
- Depend on many others (high Ce)
- Easy to change (few dependents)
- Should be: Concrete implementations, details

**High Fan-out (Ce > 10):**
- Module "knows" too much about the system
- Changes in dependencies frequently break it
- Should be refactored to reduce dependencies

### Your Results - Overall

**Summary:**
- Total Modules: {module_count}
- Average Instability: {avg_instability}
- Stable Modules (I < 0.3): {stable_count}
- Unstable Modules (I > 0.7): {unstable_count}
- High Fan-out (Ce > 10): {high_fanout_count}

### Module Dependency Graph

[Visual diagram showing module dependencies]

**Module Coupling Matrix:**
[Table showing which modules depend on which]

**Most Depended On (High Ca):**
[Table: Module, Ca, Ce, Instability, Dependents]

**Highest Fan-out (High Ce):**
[Table: Module, Ca, Ce, Instability, Dependencies]

### ðŸŽ¯ What To Do

1. **Review stable modules** (I < 0.3, high Ca)
   - Are they well-designed?
   - Should they be more abstract?
   - Any changes require coordinating many dependents

2. **Reduce high fan-out** (Ce > 10)
   - Module depends on too many others
   - Consider dependency injection
   - Use interfaces/abstractions

3. **Monitor coupling trends**
   - New modules should have I = 0.5-0.7
   - Avoid creating highly coupled modules
````

---

### 3.7 Class-Level Metrics

#### What to Measure

1. **Lack of Cohesion (LCOM)**
   - Measures if methods in a class use common attributes
   - LCOM = number of disconnected method groups
   - LCOM = 1 is ideal (all methods connected)
   - **Per module and overall**

2. **Weighted Methods per Class (WMC)**
   - Sum of cyclomatic complexity of all methods
   - Indicates total class complexity
   - **Per module and overall**

3. **God Class Detection**
   - Classes with > 20 methods
   - Classes with WMC > 50
   - Classes with LCOM > 2
   - **Per module and overall**

#### Calculation Logic
````python
# LCOM Calculation (simplified):
# 1. Build graph: methods connected if they share instance variables
# 2. Count connected components
# LCOM = number of components

# Example:
class ClaimProcessor:
    def __init__(self):
        self.claim = None      # Shared by method A, B
        self.promotion = None  # Shared by method C, D
    
    def method_a(self): self.claim = ...
    def method_b(self): return self.claim
    def method_c(self): self.promotion = ...
    def method_d(self): return self.promotion

# Graph: (A-B) (C-D) = 2 components
# LCOM = 2 (should split into 2 classes)
````

#### Report Explanation Template
````markdown
## Class Quality

### ðŸ“š What are Class Metrics?

**Lack of Cohesion (LCOM):**
- Measures if methods in a class belong together
- LCOM = 1: All methods use shared instance variables (cohesive)
- LCOM > 1: Methods use different instance variables (should be separate classes)

**Weighted Methods per Class (WMC):**
- Sum of complexity of all methods in a class
- High WMC = complex class, hard to understand/test

**God Class:**
- Class with too many responsibilities
- Violates Single Responsibility Principle
- Indicators: >20 methods, WMC >50, LCOM >2

### âš¡ Why It Matters

**Low Cohesion (LCOM > 2):**
- Class has multiple unrelated responsibilities
- Should be split into focused classes
- Changes affect unrelated functionality

**High Complexity (WMC > 50):**
- Class is too complex to understand
- Testing requires many test cases
- Bug-prone

**God Classes:**
- Central point of failure
- Everyone touches this class â†’ merge conflicts
- Hard to onboard new developers
- Becomes bottleneck for changes

### Your Results - Overall

**Summary:**
- Classes Analyzed: {class_count}
- Average LCOM: {avg_lcom}
- Average WMC: {avg_wmc}
- God Classes: {god_class_count} ðŸ”´

### Your Results - By Module

[Table showing class metrics per module]

**Module Class Quality Rankings:**
- Best Cohesion: {module_name} (avg LCOM: {score})
- Worst Cohesion: {module_name} (avg LCOM: {score})

**God Classes Detected:**
[Table: Class, Module, File, Methods, WMC, LCOM, Issues]

Example:
- Class: `ClaimInboundInterface`
- Module: `claims`
- Methods: 23
- WMC: 98
- LCOM: 3
- Issues: Too many methods, high complexity, low cohesion

### ðŸŽ¯ What To Do

**Overall:**
1. **Split god classes**
   - Identify groups of related methods (use LCOM)
   - Extract to new focused classes
   - Apply Single Responsibility Principle

2. **Reduce WMC**
   - Refactor complex methods
   - Delegate to helper classes
   - Extract algorithms to separate classes

3. **Improve cohesion**
   - Methods in a class should work together
   - Use shared instance variables
   - If not cohesive, split the class

**By Module:**
[Module-specific class improvement recommendations]
````

---

### 3.8 Code Smells

#### What to Detect

1. **Long Methods**
   - Functions/methods > 50 LOC
   - Hard to understand at a glance
   - **Per module and overall**

2. **Long Parameter Lists**
   - Functions with > 5 parameters
   - Hard to remember parameter order
   - **Per module and overall**

3. **Deep Nesting**
   - Nesting depth > 4 levels
   - Hard to follow logic flow
   - **Per module and overall**

4. **Duplicate Code**
   - Similar code blocks (>6 lines, >80% similar)
   - Bug fixes need to be applied multiple times
   - **Per module and overall**

#### Detection Logic
````python
# Long Method: Count LOC per function
# Long Parameter List: Count parameters in function signature
# Deep Nesting: Track nesting depth while parsing AST
# Duplicate Code: Compare code blocks using AST similarity
````

#### Report Explanation Template
````markdown
## Code Smells

### ðŸ“š What are Code Smells?

Code smells are patterns that indicate potential problems (not bugs, but design issues).

### âš¡ Common Smells

**1. Long Methods (>50 LOC)**

Hard to understand at a glance. Should be broken into smaller, well-named functions.
```python
# Smell: 147-line function
def process_claims():
    # 147 lines of code...
    
# Better: Multiple small functions
def process_claims():
    claims = load_claims()
    validated = validate_claims(claims)
    matched = match_promotions(validated)
    return finalize_claims(matched)
```

**2. Long Parameter Lists (>5 params)**

Hard to remember order and meaning.
```python
# Smell: Too many parameters
def create_claim(name, amount, date, account, promo, contract, status, user):
    ...

# Better: Use a data object
def create_claim(claim_data):
    ...
```

**3. Deep Nesting (>4 levels)**

Hard to follow the logic.
```python
# Smell: 7 levels deep
if condition1:
    if condition2:
        for item in items:
            if condition3:
                if condition4:
                    if condition5:
                        if condition6:
                            process()

# Better: Early returns, extract functions
def process_item(item):
    if not condition3: return
    if not condition4: return
    ...
```

**4. Duplicate Code**

Same logic in multiple places = multiple places to fix bugs.

### Your Results - Overall

**Summary:**
- Long Methods (>50 LOC): {long_methods_count} ðŸŸ¡
- Long Parameter Lists (>5): {long_params_count} ðŸŸ¡
- Deep Nesting (>4): {deep_nesting_count} ðŸŸ¡
- Duplicate Code Blocks: {duplicate_count} ðŸŸ¡

### Your Results - By Module

[Table showing code smells per module]

**Module Code Smell Rankings:**
- Cleanest Module: {module_name} ({smell_count} smells)
- Worst Module: {module_name} ({smell_count} smells)

**Details:**
[Tables for each smell type with locations including module]

### ðŸŽ¯ What To Do

**Overall:**
1. **Refactor long methods**
   - Extract logical sections to named functions
   - Aim for 10-20 LOC per function

2. **Reduce parameters**
   - Group related parameters into objects
   - Use builder pattern for complex objects

3. **Flatten nesting**
   - Use early returns (guard clauses)
   - Extract nested logic to functions

4. **Eliminate duplication**
   - Extract to shared functions
   - Use inheritance or composition

**By Module:**
[Module-specific smell elimination recommendations]
````

---

### 3.9 Technical Debt

#### What to Measure

1. **Remediation Cost**
   - Estimated hours to fix each issue type
   - Total remediation time
   - **Per module and overall**

2. **Debt Ratio**
   - Formula: `(Remediation Cost / Development Cost) Ã— 100`
   - Development Cost = SLOC Ã— avg_hours_per_LOC
   - **Per module and overall**

3. **SQALE Rating**
   - A-E rating based on debt ratio
   - **Per module and overall**

4. **Module Debt Ranking**
   - Modules sorted by technical debt
   - Identify highest-debt modules for priority attention

#### Cost Estimation
````python
# Remediation costs per issue type:
issue_costs = {
    'very_high_complexity': 1.0,      # 1 hour per function
    'high_complexity': 0.5,            # 30 minutes
    'low_maintainability': 2.0,        # 2 hours per file
    'god_class': 4.0,                  # 4 hours
    'god_method': 2.0,                 # 2 hours
    'long_method': 0.5,                # 30 minutes
    'long_parameter_list': 0.25,       # 15 minutes
    'deep_nesting': 0.5,               # 30 minutes
    'duplicate_code': 1.0,             # 1 hour per block
    'ownership_violation_write': 2.0,  # 2 hours each
    'ownership_violation_read': 0.5,   # 30 minutes
    'low_cohesion': 3.0,              # 3 hours
}

# Development cost estimation:
avg_hours_per_loc = 0.1  # Industry average
development_cost = total_sloc * avg_hours_per_loc

# Debt ratio:
total_remediation = sum of all issue costs
debt_ratio = (total_remediation / development_cost) Ã— 100
````

#### SQALE Rating

- **A:** â‰¤5% (excellent, minimal debt)
- **B:** 6-10% (good, manageable debt)
- **C:** 11-20% (moderate, should address)
- **D:** 21-50% (high debt, impacts velocity)
- **E:** >50% (critical, major refactoring needed)

#### Report Explanation Template
````markdown
## Technical Debt

### ðŸ“š What is Technical Debt?

Technical debt is like financial debt:
- **Principal:** Cost to fix all quality issues
- **Interest:** Slower development due to bad code quality
- **Compound Interest:** Problems get worse over time

**Example:**
- Adding a feature to good code: 2 hours
- Adding same feature to bad code: 8 hours (4x slower)
- The 6-hour difference is "interest" on technical debt

### âš¡ Why It Matters

**Impact on Velocity:**
- High debt = developers spend more time:
  - Understanding complex code
  - Working around coupling
  - Debugging issues
  - Dealing with fragile code

**Business Impact:**
- Low debt (A-B rating): Fast feature delivery
- High debt (D-E rating): 2-5x slower delivery, more bugs

**Debt Compounds:**
- Ignored debt makes future changes harder
- Today's shortcuts become tomorrow's emergencies
- Eventually: "We need to rewrite from scratch"

### ðŸ“Š SQALE Rating

Industry-standard rating system:
- ðŸŸ¢ **A (â‰¤5%):** Excellent - minimal debt, sustainable
- ðŸŸ¢ **B (6-10%):** Good - manageable, normal for mature codebases
- ðŸŸ¡ **C (11-20%):** Moderate - should plan to reduce debt
- ðŸ”´ **D (21-50%):** High - impacts velocity significantly
- ðŸ”´ **E (>50%):** Critical - major refactoring needed

**Your Overall Rating: {sqale_rating}**

### Your Results - Overall

**Summary:**
- Total Remediation Time: {total_hours} hours ({total_days} days)
- Development Cost: {dev_cost} hours
- **Debt Ratio: {debt_ratio}%** ðŸ”´
- **SQALE Rating: {sqale_rating}** ðŸ”´

**What this means:**
For every {x} hours spent adding features, you're paying {y} hours in "interest" (slower development due to code quality).

**Debt Breakdown:**
- Database Coupling: {db_debt} hours
- Complexity Issues: {complexity_debt} hours
- Maintainability Issues: {maintainability_debt} hours
- Code Smells: {smells_debt} hours
- Class Design: {class_debt} hours

### Your Results - By Module

[Table showing debt metrics per module]
[Chart showing debt ratio by module]

**Module Debt Rankings:**
1. {module_name}: {debt_hours} hours, {debt_ratio}%, Rating: {rating} ðŸ”´
2. {module_name}: {debt_hours} hours, {debt_ratio}%, Rating: {rating} ðŸŸ¡
3. {module_name}: {debt_hours} hours, {debt_ratio}%, Rating: {rating} ðŸŸ¢

**Top Debt Contributors (All Modules):**
[Table: File, Module, Debt Hours, Main Issues, Recommended Action]

**Module-Specific Debt Breakdown:**
[Expandable sections showing debt analysis per module]

### ðŸŽ¯ What To Do

**Strategy: Pay Down Highest-Interest Debt First**

**Overall Priority:**
1. **Fix critical issues** (high impact, moderate effort)
   - Database write violations: {write_violations} Ã— 2 hours = {hours}
   - God classes: {god_classes} Ã— 4 hours = {hours}

2. **Prevent new debt**
   - Code review checklist (complexity, coupling, smells)
   - Automated linting with thresholds
   - "Boy Scout Rule": Leave code better than you found it

3. **Plan systematic reduction**
   - Allocate 20% of sprint capacity to debt reduction
   - Target: Reduce to C rating within 6 months
   - Track progress with monthly analysis

**ROI of Debt Reduction:**
- Current velocity: Slowed by {debt_ratio}%
- After reduction to C (15% debt): {improvement}% faster
- Estimated payback period: {months} months

**By Module Priority:**
1. Focus on {worst_module} first (highest debt: {debt_hours} hours)
   - Specific actions: [list]
   - Expected improvement: {hours} hours saved

2. Then address {second_worst_module}
   - Specific actions: [list]

[Detailed module-by-module recommendations]
````

---

### 3.10 Module Health Score

#### What to Measure

**Composite Score (0-100)** combining:
- Database coupling severity (weight: 30%)
- Average complexity (weight: 20%)
- Average maintainability (weight: 20%)
- Testability score (weight: 15%)
- Code smells density (weight: 10%)
- Technical debt ratio (weight: 5%)

#### Calculation
````python
def calculate_module_health_score(module_metrics):
    # Normalize each metric to 0-100 scale
    coupling_score = normalize_coupling(module_metrics['db_coupling'])
    complexity_score = normalize_complexity(module_metrics['complexity'])
    maintainability_score = module_metrics['maintainability']['avg_mi']
    testability_score = module_metrics['tests']['testability_score']
    smells_score = normalize_smells(module_metrics['code_smells'])
    debt_score = normalize_debt(module_metrics['technical_debt'])
    
    # Weighted average
    health_score = (
        coupling_score * 0.30 +
        complexity_score * 0.20 +
        maintainability_score * 0.20 +
        testability_score * 0.15 +
        smells_score * 0.10 +
        debt_score * 0.05
    )
    
    return health_score
````

#### Rating Categories

- **80-100:** Excellent (ðŸŸ¢)
- **60-79:** Good (ðŸŸ¢)
- **40-59:** Warning (ðŸŸ¡)
- **20-39:** Critical (ðŸ”´)
- **0-19:** Emergency (ðŸ”´ðŸ”´)

---

## 4. Data Structures

### 4.1 Overall Results Structure
````python
{
    "metadata": {
        "analysis_date": "2024-12-13T10:30:00Z",
        "codebase_path": "/path/to/backend",
        "service_name": "claims",
        "total_files_analyzed": 173,
        "total_files_skipped": 5,
        "skipped_files": ["file1.py", "file2.py"],
        "analysis_duration_seconds": 23.4,
        "config_used": "config.yaml",
        "module_detection": {
            "method": "auto",
            "depth": 1,
            "modules_detected": 4
        }
    },
    
    "summary": {
        "total_db_operations": 247,
        "ownership_violations_write": 17,
        "ownership_violations_read": 80,
        "avg_complexity": 4.2,
        "high_complexity_functions": 45,
        "avg_maintainability": 62.5,
        "low_maintainability_files": 15,
        "test_ratio_unit": 21.8,
        "test_ratio_integration": 78.2,
        "testability_score": 44.2,
        "technical_debt_hours": 347.5,
        "debt_ratio": 22.5,
        "sqale_rating": "D"
    },
    
    "modules": { ... },  # See Module Structure below
    "db_coupling": { ... },
    "complexity": { ... },
    "maintainability": { ... },
    "code_size": { ... },
    "tests": { ... },
    "module_coupling": { ... },
    "class_metrics": { ... },
    "code_smells": { ... },
    "technical_debt": { ... }
}
````

### 4.2 Module Structure
````python
{
    "modules": {
        "total_modules": 4,
        "module_list": ["claims", "promotions", "contracts", "shared"],
        
        "modules_analyzed": [
            {
                "name": "claims",
                "path": "claims/",
                "description": "Claims processing and validation",
                "file_count": 45,
                "sloc": 3842,
                "test_file_count": 23,
                
                # Module health score
                "health_score": 42.5,  # 0-100
                "health_rating": "critical",  # excellent/good/warning/critical/emergency
                
                # All metrics for this module
                "db_coupling": {
                    "total_operations": 156,
                    "operations_by_type": {"read": 112, "write": 44},
                    "operations_by_ownership": {
                        "own_table": 98,
                        "shared_table": 22,
                        "other_table_read": 24,
                        "other_table_write": 12
                    },
                    "severity_score": 98,
                    "collections_accessed": {
                        "claim_current": {"reads": 85, "writes": 45, "ownership": "own"},
                        "promotions": {"reads": 18, "writes": 3, "ownership": "other"}
                    },
                    "violations": [...]
                },
                
                "complexity": {
                    "avg_complexity": 6.8,
                    "max_complexity": 28,
                    "distribution": {
                        "simple_1_5": 120,
                        "moderate_6_10": 45,
                        "complex_11_20": 18,
                        "very_complex_21_plus": 5
                    },
                    "high_complexity_functions": 23
                },
                
                "maintainability": {
                    "avg_mi": 48.3,
                    "distribution": {
                        "high_65_100": 12,
                        "moderate_20_64": 25,
                        "low_0_19": 8
                    },
                    "low_maintainability_files": 8
                },
                
                "code_size": {
                    "total_sloc": 3842,
                    "avg_file_size": 85.4,
                    "comment_ratio": 9.2,
                    "large_files_count": 5
                },
                
                "tests": {
                    "total_test_files": 23,
                    "unit_test_files": 4,
                    "integration_test_files": 19,
                    "test_ratio": {"unit_percentage": 17.4, "integration_percentage": 82.6},
                    "testability_score": 38.4
                },
                
                "class_metrics": {
                    "total_classes": 34,
                    "avg_lcom": 2.1,
                    "avg_wmc": 28.5,
                    "god_classes_count": 2
                },
                
                "code_smells": {
                    "long_methods": 15,
                    "long_parameter_lists": 8,
                    "deep_nesting": 6,
                    "duplicate_code_blocks": 4
                },
                
                "technical_debt": {
                    "debt_hours": 156.5,
                    "debt_ratio": 28.3,
                    "sqale_rating": "D",
                    "debt_breakdown": {
                        "db_coupling": 45.0,
                        "complexity": 28.5,
                        "maintainability": 52.0,
                        "code_smells": 18.0,
                        "class_design": 13.0
                    }
                }
            },
            
            {
                "name": "promotions",
                "path": "promotions/",
                "description": "Promotion matching and application",
                # ... same structure ...
            },
            
            {
                "name": "contracts",
                "path": "contracts/",
                # ... same structure ...
            },
            
            {
                "name": "shared",
                "path": "shared/",
                # ... same structure ...
            }
        ],
        
        # Module rankings
        "rankings": {
            "by_health_score": [
                {"module": "shared", "health_score": 78.5, "rating": "good"},
                {"module": "promotions", "health_score": 58.2, "rating": "warning"},
                {"module": "contracts", "health_score": 47.3, "rating": "warning"},
                {"module": "claims", "health_score": 42.5, "rating": "critical"}
            ],
            "by_technical_debt": [
                {"module": "claims", "debt_hours": 156.5, "debt_ratio": 28.3},
                {"module": "promotions", "debt_hours": 98.2, "debt_ratio": 22.1},
                {"module": "contracts", "debt_hours": 65.8, "debt_ratio": 18.5},
                {"module": "shared", "debt_hours": 27.0, "debt_ratio": 8.2}
            ],
            "by_coupling_severity": [
                {"module": "claims", "severity_score": 98},
                {"module": "promotions", "severity_score": 45},
                {"module": "contracts", "severity_score": 22},
                {"module": "shared", "severity_score": 0}
            ],
            "by_testability": [
                {"module": "shared", "testability_score": 72.5},
                {"module": "contracts", "testability_score": 51.2},
                {"module": "promotions", "testability_score": 42.8},
                {"module": "claims", "testability_score": 38.4}
            ]
        },
        
        # Cross-module coupling
        "inter_module_coupling": [
            {
                "from_module": "claims",
                "to_module": "promotions",
                "db_operations": 23,
                "import_count": 15,
                "coupling_type": "database_and_code"
            },
            {
                "from_module": "claims",
                "to_module": "contracts",
                "db_operations": 8,
                "import_count": 7,
                "coupling_type": "database_and_code"
            },
            {
                "from_module": "promotions",
                "to_module": "claims",
                "db_operations": 5,
                "import_count": 3,
                "coupling_type": "database_and_code"
            }
        ],
        
        # Module dependency graph (for visualization)
        "dependency_graph": {
            "claims": ["promotions", "contracts", "shared"],
            "promotions": ["shared"],
            "contracts": ["shared"],
            "shared": []
        }
    }
}
````

### 4.3 Database Coupling Structure (Overall)
````python
{
    "db_coupling": {
        "total_imports": 64,
        "total_operations": 247,
        "files_with_db_access": 45,
        
        "operations_by_type": {
            "read": 180,
            "write": 67
        },
        
        "operations_by_ownership": {
            "own_table": 150,
            "shared_table": 30,
            "other_table_read": 50,
            "other_table_write": 17
        },
        
        "severity_score": 165,  # (50 Ã— 1) + (17 Ã— 5)
        
        "collections_accessed": {
            "claim_current": {"reads": 85, "writes": 45, "ownership": "own", "accessed_by_modules": ["claims"]},
            "promotions": {"reads": 18, "writes": 3, "ownership": "other", "accessed_by_modules": ["claims", "contracts"]},
            "plan_account": {"reads": 15, "writes": 0, "ownership": "shared", "accessed_by_modules": ["claims", "promotions", "contracts"]}
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "total_operations": 156,
                "severity_score": 98,
                "violations_write": 12
            },
            "promotions": {
                "total_operations": 54,
                "severity_score": 32,
                "violations_write": 3
            },
            # ...
        },
        
        "top_coupled_files": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "total_operations": 42,
                "reads": 28,
                "writes": 14,
                "collections": ["claim_current", "promotions", "plan_account"],
                "ownership_violations": 8,
                "severity_score": 42
            },
            # ... Top 20
        ],
        
        "violations": [
            {
                "type": "write",
                "severity": "critical",
                "table": "promotions",
                "owner": "promotions",
                "violating_module": "claims",
                "operation_count": 3,
                "locations": [
                    {
                        "file": "claims/claim_inbound.py",
                        "line": 234,
                        "method": "update_one",
                        "code_snippet": "db.promotions.update_one({'_id': ...})"
                    },
                    # ...
                ]
            },
            # ...
        ]
    }
}
````

### 4.4 Complexity Structure (Overall)
````python
{
    "complexity": {
        "total_functions": 523,
        "avg_complexity": 4.2,
        "max_complexity": 28,
        
        "distribution": {
            "simple_1_5": 380,
            "moderate_6_10": 98,
            "complex_11_20": 35,
            "very_complex_21_plus": 10
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "avg_complexity": 6.8,
                "max_complexity": 28,
                "high_complexity_count": 23
            },
            "promotions": {
                "avg_complexity": 4.1,
                "max_complexity": 15,
                "high_complexity_count": 12
            },
            # ...
        },
        
        "high_complexity_functions": [
            {
                "function": "process_claims",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "line": 145,
                "complexity": 28,
                "category": "very_complex"
            },
            # ...
        ],
        
        "per_file": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "avg_complexity": 8.3,
                "max_complexity": 28,
                "function_count": 23,
                "functions": [
                    {"name": "process_claims", "complexity": 28, "line": 145},
                    # ...
                ]
            },
            # ...
        ]
    }
}
````

### 4.5 Maintainability Structure (Overall)
````python
{
    "maintainability": {
        "avg_mi": 62.5,
        
        "distribution": {
            "high_65_100": 95,
            "moderate_20_64": 63,
            "low_0_19": 15
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "avg_mi": 48.3,
                "low_mi_count": 8
            },
            "promotions": {
                "avg_mi": 58.7,
                "low_mi_count": 4
            },
            # ...
        },
        
        "low_maintainability_files": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "mi_score": 12.3,
                "category": "low",
                "sloc": 847,
                "complexity": 28,
                "comment_ratio": 8.2,
                "main_issues": ["large_file", "high_complexity", "low_comments"]
            },
            # ...
        ],
        
        "per_file": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "mi_score": 12.3
            },
            # ...
        ]
    }
}
````

### 4.6 Code Size Structure (Overall)
````python
{
    "code_size": {
        "total_sloc": 15420,
        "total_comments": 1890,
        "total_blank": 2100,
        "comment_ratio": 12.3,
        
        "file_size_distribution": {
            "small_0_100": 45,
            "medium_101_500": 120,
            "large_501_plus": 8
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "total_sloc": 3842,
                "file_count": 45,
                "avg_file_size": 85.4,
                "comment_ratio": 9.2
            },
            "promotions": {
                "total_sloc": 4521,
                "file_count": 52,
                "avg_file_size": 87.0,
                "comment_ratio": 11.5
            },
            # ...
        },
        
        "large_files": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "sloc": 847,
                "comments": 69,
                "comment_ratio": 8.2
            },
            # ...
        ],
        
        "large_functions": [
            {
                "function": "process_claims",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "sloc": 147,
                "line": 145
            },
            # ...
        ],
        
        "low_documentation": [
            {
                "file": "claims/claim_processor.py",
                "module": "claims",
                "comment_ratio": 3.5
            },
            # ...
        ]
    }
}
````

### 4.7 Test Analysis Structure (Overall)
````python
{
    "tests": {
        "total_test_files": 87,
        "unit_test_files": 19,
        "integration_test_files": 68,
        "total_test_functions": 543,
        "unit_test_functions": 98,
        "integration_test_functions": 445,
        
        "test_ratio": {
            "unit_percentage": 21.8,
            "integration_percentage": 78.2
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "test_files": 23,
                "unit_percentage": 17.4,
                "testability_score": 38.4
            },
            "promotions": {
                "test_files": 28,
                "unit_percentage": 25.0,
                "testability_score": 42.8
            },
            # ...
        },
        
        "testability": {
            "total_functions": 523,
            "functions_with_db_access": 89,
            "functions_with_business_logic": 120,
            "functions_mixing_both": 67,
            "testability_score": 44.2,  # (120-67)/120 * 100
            
            "by_module": {
                "claims": {
                    "testability_score": 38.4,
                    "mixed_functions": 28
                },
                # ...
            },
            
            "untestable_functions": [
                {
                    "function": "validate_claim",
                    "module": "claims",
                    "file": "claims/claim_inbound.py",
                    "line": 234,
                    "reason": "mixes_business_logic_and_db",
                    "db_operations": 3,
                    "business_logic_indicators": ["if", "validation", "calculation"]
                },
                # ...
            ]
        },
        
        "test_details": [
            {
                "file": "test_claim_inbound.py",
                "module": "claims",
                "type": "integration",
                "test_count": 23,
                "db_operations": 45,
                "indicators": ["mock_claim_db fixture", "from vf_db import db"]
            },
            # ...
        ]
    }
}
````

### 4.8 Module Coupling Structure
````python
{
    "module_coupling": {
        "total_modules": 4,
        "avg_afferent_coupling": 1.5,
        "avg_efferent_coupling": 2.0,
        "avg_instability": 0.57,
        
        "per_module": [
            {
                "module": "claims",
                "afferent_coupling": 0,  # No modules import claims
                "efferent_coupling": 3,  # Claims imports: promotions, contracts, shared
                "instability": 1.0,      # Ce/(Ca+Ce) = 3/3
                "stability_category": "unstable",
                "imported_by": [],
                "imports": ["promotions", "contracts", "shared"]
            },
            {
                "module": "shared",
                "afferent_coupling": 3,  # All modules import shared
                "efferent_coupling": 0,  # Shared imports nothing
                "instability": 0.0,      # 0/3
                "stability_category": "stable",
                "imported_by": ["claims", "promotions", "contracts"],
                "imports": []
            },
            # ...
        ],
        
        "stable_modules": [
            {"module": "shared", "instability": 0.0}
        ],
        
        "unstable_modules": [
            {"module": "claims", "instability": 1.0}
        ],
        
        "dependency_graph": {
            "nodes": ["claims", "promotions", "contracts", "shared"],
            "edges": [
                {"from": "claims", "to": "promotions"},
                {"from": "claims", "to": "contracts"},
                {"from": "claims", "to": "shared"},
                {"from": "promotions", "to": "shared"},
                {"from": "contracts", "to": "shared"}
            ]
        }
    }
}
````

### 4.9 Class Metrics Structure (Overall)
````python
{
    "class_metrics": {
        "total_classes": 156,
        "avg_lcom": 1.8,
        "avg_wmc": 23.4,
        "avg_methods_per_class": 8.2,
        
        # By module summary
        "by_module": {
            "claims": {
                "total_classes": 34,
                "avg_lcom": 2.1,
                "avg_wmc": 28.5,
                "god_classes_count": 2
            },
            # ...
        },
        
        "per_class": [
            {
                "class": "ClaimInboundInterface",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "line": 45,
                "methods": 23,
                "attributes": 12,
                "lcom": 3,
                "wmc": 98,
                "cohesion_level": "low"
            },
            # ...
        ],
        
        "god_classes": [
            {
                "class": "ClaimInboundInterface",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "reasons": ["23 methods", "WMC 98", "LCOM 3"],
                "severity": "high"
            },
            # ...
        ],
        
        "low_cohesion_classes": [...]  # LCOM > 2
    }
}
````

### 4.10 Code Smells Structure (Overall)
````python
{
    "code_smells": {
        # By module summary
        "by_module": {
            "claims": {
                "long_methods": 15,
                "long_parameter_lists": 8,
                "deep_nesting": 6,
                "duplicate_code_blocks": 4,
                "total_smells": 33
            },
            # ...
        },
        
        "long_methods": [
            {
                "function": "process_claims",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "sloc": 147,
                "line": 145
            },
            # ...
        ],
        
        "long_parameter_lists": [
            {
                "function": "validate_claim",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "parameters": 8,
                "line": 234,
                "param_names": ["claim_id", "account", "amount", ...]
            },
            # ...
        ],
        
        "deep_nesting": [
            {
                "function": "process_claims",
                "module": "claims",
                "file": "claims/claim_inbound.py",
                "max_depth": 7,
                "line": 145
            },
            # ...
        ],
        
        "duplicate_code": [
            {
                "block_1": {"file": "claims/claim_a.py", "module": "claims", "lines": "45-67"},
                "block_2": {"file": "claims/claim_b.py", "module": "claims", "lines": "123-145"},
                "similarity": 95.5,
                "sloc": 23
            },
            # ...
        ]
    }
}
````

### 4.11 Technical Debt Structure (Overall)
````python
{
    "technical_debt": {
        "total_remediation_hours": 347.5,
        "total_remediation_days": 43.4,
        "development_cost_hours": 1542,
        "debt_ratio": 22.5,
        "sqale_rating": "D",
        
        "debt_breakdown": {
            "db_coupling": 85.0,
            "complexity": 45.5,
            "maintainability": 120.0,
            "code_smells": 47.0,
            "class_design": 50.0
        },
        
        # By module summary
        "by_module": {
            "claims": {
                "debt_hours": 156.5,
                "debt_ratio": 28.3,
                "sqale_rating": "D"
            },
            "promotions": {
                "debt_hours": 98.2,
                "debt_ratio": 22.1,
                "sqale_rating": "D"
            },
            # ...
        },
        
        "top_debt_files": [
            {
                "file": "claims/claim_inbound.py",
                "module": "claims",
                "debt_hours": 18.5,
                "debt_ratio": 35.2,
                "rating": "E",
                "issues": [
                    {"type": "god_class", "cost": 4.0},
                    {"type": "low_maintainability", "cost": 2.0},
                    {"type": "high_complexity", "cost": 2.0},
                    {"type": "long_method", "cost": 0.5},
                    # ...
                ]
            },
            # ...
        ],
        
        "issue_costs": {
            "very_high_complexity": {"count": 10, "total_hours": 10.0},
            "high_complexity": {"count": 35, "total_hours": 17.5},
            "low_maintainability": {"count": 15, "total_hours": 30.0},
            "god_class": {"count": 3, "total_hours": 12.0},
            "ownership_violation_write": {"count": 17, "total_hours": 34.0},
            # ...
        }
    }
}
````

---

## 5. HTML Report Structure

### 5.1 Overall Template
````html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report - {service_name}</title>
    <style>
        /* Embedded CSS - responsive, print-friendly */
        /* Color scheme: Red (#dc3545), Yellow (#ffc107), Green (#28a745), Blue (#007bff) */
    </style>
</head>
<body>
    <header>
        <h1>Codebase Architecture Analysis</h1>
        <div class="metadata">
            <p><strong>Service:</strong> {service_name}</p>
            <p><strong>Analysis Date:</strong> {analysis_date}</p>
            <p><strong>Files Analyzed:</strong> {total_files}</p>
            <p><strong>Modules Detected:</strong> {module_count}</p>
        </div>
    </header>

    <!-- Navigation -->
    <nav>
        <a href="#executive-summary">Summary</a>
        <a href="#module-overview">Modules</a>
        <a href="#database-coupling">DB Coupling</a>
        <a href="#complexity">Complexity</a>
        <a href="#maintainability">Maintainability</a>
        <a href="#tests">Tests</a>
        <a href="#technical-debt">Tech Debt</a>
        <a href="#recommendations">Actions</a>
    </nav>

    <!-- Executive Summary - Overall Codebase -->
    <section id="executive-summary">
        <h2>Executive Summary - Overall Codebase</h2>
        <div class="metric-cards">
            <!-- Overall metric cards -->
        </div>
    </section>

    <!-- Module Overview -->
    <section id="module-overview">
        <h2>Module Overview</h2>
        
        <div class="explanation-box">
            <h3>ðŸ“š What are Modules?</h3>
            <p>Modules are logical groupings of code based on folder structure. This analysis breaks down all metrics by module to help you identify which parts of the codebase need the most attention.</p>
        </div>
        
        <!-- Module Health Summary -->
        <div class="module-health-summary">
            <h3>Module Health Scores</h3>
            <table class="module-health-table">
                <thead>
                    <tr>
                        <th>Module</th>
                        <th>Health Score</th>
                        <th>Tech Debt</th>
                        <th>Coupling</th>
                        <th>Testability</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- For each module -->
                    <tr class="module-row row-{severity}">
                        <td><strong>{module_name}</strong></td>
                        <td>{health_score}/100</td>
                        <td>{debt_hours}h ({sqale_rating})</td>
                        <td>{severity_score}</td>
                        <td>{testability_score}%</td>
                        <td><span class="badge badge-{severity}">{status_emoji} {status}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Module Comparison Charts -->
        <div class="module-charts">
            <div class="chart-container">
                <h4>Health Score by Module</h4>
                <canvas id="module-health-chart"></canvas>
            </div>
            
            <div class="chart-container">
                <h4>Technical Debt by Module</h4>
                <canvas id="module-debt-chart"></canvas>
            </div>
        </div>
        
        <!-- Module Dependency Graph -->
        <div class="dependency-graph">
            <h3>Module Dependencies</h3>
            <!-- Visual graph showing module dependencies -->
            <div id="module-dependency-viz"></div>
        </div>
        
        <!-- Detailed Module Breakdown (Expandable) -->
        <div class="module-details">
            <h3>Detailed Module Analysis</h3>
            
            <!-- For each module -->
            <details class="module-detail-section">
                <summary>
                    <h4>{module_name}</h4>
                    <span class="module-summary">
                        Health: {health_score}/100 | 
                        Debt: {debt_hours}h | 
                        Files: {file_count}
                    </span>
                </summary>
                
                <div class="module-content">
                    <!-- Module-specific metric cards -->
                    <div class="metric-cards">
                        <!-- DB Coupling card for this module -->
                        <!-- Complexity card for this module -->
                        <!-- Maintainability card for this module -->
                        <!-- etc. -->
                    </div>
                    
                    <!-- Module-specific recommendations -->
                    <div class="module-recommendations">
                        <h5>ðŸŽ¯ Priority Actions for {module_name}</h5>
                        <ol>
                            <li>{recommendation}</li>
                        </ol>
                    </div>
                </div>
            </details>
        </div>
    </section>

    <!-- Database Coupling - Overall -->
    <section id="database-coupling">
        <h2>Database Coupling - Overall</h2>
        
        <!-- Explanation box -->
        <div class="explanation-box">
            <!-- As defined in section 3.1 -->
        </div>
        
        <!-- Overall results -->
        <div class="results">
            <h3>Overall Results</h3>
            <!-- Charts and summary -->
        </div>
        
        <!-- By Module breakdown -->
        <div class="by-module">
            <h3>By Module</h3>
            <table class="module-comparison-table">
                <thead>
                    <tr>
                        <th>Module</th>
                        <th>Total Operations</th>
                        <th>Own Tables</th>
                        <th>Read Violations</th>
                        <th>Write Violations</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Module rows -->
                </tbody>
            </table>
        </div>
        
        <!-- Action items -->
        <div class="action-items">
            <!-- Overall and per-module -->
        </div>
    </section>

    <!-- Complexity - Overall -->
    <section id="complexity">
        <h2>Code Complexity - Overall</h2>
        <!-- Similar structure: explanation, overall, by-module, actions -->
    </section>

    <!-- Maintainability - Overall -->
    <section id="maintainability">
        <h2>Maintainability - Overall</h2>
        <!-- Similar structure -->
    </section>

    <!-- Tests - Overall -->
    <section id="tests">
        <h2>Test Analysis - Overall</h2>
        <!-- Similar structure -->
    </section>

    <!-- Module Coupling -->
    <section id="module-coupling">
        <h2>Module Coupling</h2>
        <!-- Module dependency analysis -->
    </section>

    <!-- Technical Debt - Overall -->
    <section id="technical-debt">
        <h2>Technical Debt - Overall</h2>
        
        <!-- Explanation -->
        <div class="explanation-box">
            <!-- As defined in section 3.9 -->
        </div>
        
        <!-- Overall summary -->
        <div class="debt-summary">
            <!-- Overall debt metrics -->
        </div>
        
        <!-- Module debt comparison -->
        <div class="module-debt-comparison">
            <h3>Technical Debt by Module</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Module</th>
                        <th>Debt Hours</th>
                        <th>Debt Ratio</th>
                        <th>SQALE Rating</th>
                        <th>Priority</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="row-{severity}">
                        <td>{rank}</td>
                        <td><strong>{module_name}</strong></td>
                        <td>{debt_hours}h</td>
                        <td>{debt_ratio}%</td>
                        <td><span class="sqale-badge sqale-{rating}">{rating}</span></td>
                        <td>{priority_emoji} {priority}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Debt breakdown chart -->
        <div class="chart-container">
            <h4>Debt Distribution by Module</h4>
            <canvas id="module-debt-distribution"></canvas>
        </div>
    </section>

    <!-- Recommendations - Prioritized -->
    <section id="recommendations">
        <h2>Prioritized Recommendations</h2>
        
        <!-- Overall recommendations -->
        <div class="recommendations-overall">
            <h3>Overall Priorities</h3>
            <div class="action-group priority-critical">
                <h4>ðŸ”´ CRITICAL - Address Immediately</h4>
                <ol>
                    <li>{action}</li>
                </ol>
            </div>
            <!-- HIGH, MEDIUM priorities -->
        </div>
        
        <!-- Module-specific recommendations -->
        <div class="recommendations-by-module">
            <h3>By Module Priority</h3>
            
            <div class="module-recommendations">
                <h4>1. Focus on: {worst_module} (Highest Debt)</h4>
                <p><strong>Health Score:</strong> {health_score}/100 ðŸ”´</p>
                <p><strong>Technical Debt:</strong> {debt_hours} hours</p>
                
                <h5>Priority Actions:</h5>
                <ol>
                    <li>{action}</li>
                </ol>
                
                <h5>Expected Impact:</h5>
                <ul>
                    <li>Reduce debt by {hours} hours</li>
                    <li>Improve health score to {new_score}</li>
                </ul>
            </div>
            
            <!-- Additional modules -->
        </div>
    </section>

    <footer>
        <p>Generated by Codebase Analysis Tool v1.0</p>
        <p>Analysis Date: {date}</p>
    </footer>

    <script>
        /* Embedded JavaScript for:
         * - Interactive charts (Chart.js or similar)
         * - Sortable tables
         * - Expandable sections
         * - Module dependency visualization
         */
    </script>
</body>
</html>
````

### 5.2 Module Health Card Template
````html
<div class="module-card module-{severity}">
    <div class="module-header">
        <h4>{module_name}</h4>
        <span class="health-score score-{severity}">{health_score}/100</span>
    </div>
    <div class="module-metrics">
        <div class="metric">
            <span class="metric-label">Tech Debt:</span>
            <span class="metric-value">{debt_hours}h ({sqale_rating})</span>
        </div>
        <div class="metric">
            <span class="metric-label">Coupling:</span>
            <span class="metric-value">{severity_score}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Testability:</span>
            <span class="metric-value">{testability_score}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Files:</span>
            <span class="metric-value">{file_count}</span>
        </div>
    </div>
    <button class="btn-expand" data-module="{module_name}">View Details</button>
</div>
````

---

## 6. Configuration

### 6.1 Config File Format (YAML)
````yaml
# config.yaml

# Service identification
service_name: claims

# Module detection
module_detection:
  method: "auto"  # "auto" or "manual"
  depth: 1        # Folder depth to treat as modules (1 = top-level folders)
  
  # Optional: Manually define modules (overrides auto-detection)
  manual_modules:
    - name: "Claims Processing"
      path: "claims"
      description: "Inbound claim processing and validation"
    - name: "Promotions Engine"
      path: "promotions"
      description: "Promotion matching and application"
    - name: "Shared Utilities"
      path: "shared"
      description: "Cross-cutting concerns and utilities"

# Table ownership mapping
# Used to categorize database operations
table_ownership:
  claims:
    - claim_current
    - claim_lines
    - claim_history
    - claim_attachments
  
  promotions:
    - promotions
    - promotion_products
    - promotion_media
  
  contracts:
    - contract_lines
    - contract_adjustments
  
  targets:
    - target_current
    - target_achievement
  
  shared:
    - plan_account
    - internal_customer
    - sap_system

# Analysis thresholds (uses industry standards by default)
thresholds:
  complexity: 10              # Cyclomatic complexity warning threshold
  maintainability: 20         # Maintainability Index critical threshold
  file_size: 500             # Large file threshold (LOC)
  function_size: 50          # Large function threshold (LOC)
  parameters: 5              # Long parameter list threshold
  nesting: 4                 # Deep nesting threshold
  class_methods: 20          # God class method count threshold
  class_wmc: 50              # God class WMC threshold
  class_lcom: 2              # Low cohesion threshold
  comment_ratio: 5           # Low documentation threshold (%)
  module_fan_out: 10         # High coupling threshold (efferent)

# Files/directories to exclude from analysis
exclude_patterns:
  - "*/test_*"
  - "*_test.py"
  - "*/__pycache__/*"
  - "*/migrations/*"
  - "*.pyc"
  - ".git/*"
  - "venv/*"
  - "env/*"

# Analysis options
options:
  analyze_tests: true         # Include test analysis
  detect_duplicates: true     # Detect duplicate code (slower)
  detect_dead_code: false     # Detect unused code (expensive, optional)
  generate_charts: true       # Include charts in HTML report
  module_dependency_graph: true  # Generate module dependency visualization

# Remediation cost factors (hours per issue type)
remediation_costs:
  very_high_complexity: 1.0
  high_complexity: 0.5
  low_maintainability: 2.0
  god_class: 4.0
  god_method: 2.0
  long_method: 0.5
  long_parameter_list: 0.25
  deep_nesting: 0.5
  duplicate_code: 1.0
  ownership_violation_write: 2.0
  ownership_violation_read: 0.5
  low_cohesion: 3.0
  high_fan_out: 1.0
````

### 6.2 Default Configuration

If no config file provided, use these defaults:
````python
DEFAULT_CONFIG = {
    'service_name': 'unknown',
    'module_detection': {
        'method': 'auto',
        'depth': 1,
        'manual_modules': []
    },
    'table_ownership': {},
    'thresholds': {
        'complexity': 10,
        'maintainability': 20,
        'file_size': 500,
        'function_size': 50,
        'parameters': 5,
        'nesting': 4,
        'class_methods': 20,
        'class_wmc': 50,
        'class_lcom': 2,
        'comment_ratio': 5,
        'module_fan_out': 10
    },
    'exclude_patterns': [
        '*/test_*', '*_test.py', '*/__pycache__/*',
        '*/migrations/*', '*.pyc', '.git/*', 'venv/*', 'env/*'
    ],
    'options': {
        'analyze_tests': True,
        'detect_duplicates': True,
        'detect_dead_code': False,
        'generate_charts': True,
        'module_dependency_graph': True
    },
    'remediation_costs': {
        'very_high_complexity': 1.0,
        'high_complexity': 0.5,
        'low_maintainability': 2.0,
        'god_class': 4.0,
        'god_method': 2.0,
        'long_method': 0.5,
        'long_parameter_list': 0.25,
        'deep_nesting': 0.5,
        'duplicate_code': 1.0,
        'ownership_violation_write': 2.0,
        'ownership_violation_read': 0.5,
        'low_cohesion': 3.0,
        'high_fan_out': 1.0
    }
}
````

---

## 7. Technical Requirements

### 7.1 Python Version

**Minimum:** Python 3.8+

**Recommended:** Python 3.10+

### 7.2 Required Libraries
````
# requirements.txt
radon>=5.1.0           # Complexity, maintainability, raw metrics
jinja2>=3.1.0          # HTML templating
pyyaml>=6.0            # Config file parsing
pathlib                # Path handling (stdlib in Python 3.4+)
````

### 7.3 Optional Libraries
````
plotly>=5.0.0          # Interactive charts (alternative to Chart.js)
pylint>=2.0.0          # Code duplication detection
````

### 7.4 Performance Requirements

**Speed:**
- Should analyze ~500 files in < 2 minutes on typical hardware
- Module-level analysis should add < 10% overhead
- Progress indicator for long-running analysis

**Memory:**
- Should not exceed 500MB RAM for typical codebases (~1000 files)
- Process files incrementally, not load all at once

### 7.5 Error Handling

**Graceful Degradation:**
- Skip files with syntax errors (log them)
- Handle encoding issues (try UTF-8, fall back to latin-1, then skip)
- Continue analysis if single file fails
- Report skipped files in metadata

**Logging:**
````python
# Log levels:
# - INFO: Progress updates (if --verbose), module detection
# - WARNING: Skipped files, encoding issues
# - ERROR: Critical failures
````

---

## 8. Implementation Guidelines

### 8.1 Architecture
````
analyze_codebase.py
â”œâ”€â”€ main()                      # CLI entry point
â”œâ”€â”€ CodebaseAnalyzer            # Main orchestrator
â”‚   â”œâ”€â”€ __init__(root_path, config)
â”‚   â”œâ”€â”€ detect_modules()        # Detect modules from folder structure
â”‚   â”œâ”€â”€ analyze()               # Run all analyses
â”‚   â”œâ”€â”€ analyze_module()        # Run analyses for single module
â”‚   â”œâ”€â”€ generate_report()       # Create HTML/JSON/MD
â”‚   â””â”€â”€ _load_config()
â”œâ”€â”€ analyzers/
â”‚   â”œâ”€â”€ db_coupling.py          # Database coupling analysis
â”‚   â”œâ”€â”€ complexity.py           # Complexity analysis
â”‚   â”œâ”€â”€ maintainability.py     # MI analysis
â”‚   â”œâ”€â”€ code_size.py           # Size metrics
â”‚   â”œâ”€â”€ test_analysis.py       # Test analysis
â”‚   â”œâ”€â”€ module_coupling.py     # Module dependency analysis
â”‚   â”œâ”€â”€ class_metrics.py       # Class-level metrics
â”‚   â”œâ”€â”€ code_smells.py         # Smell detection
â”‚   â”œâ”€â”€ tech_debt.py           # Debt calculation
â”‚   â””â”€â”€ module_health.py       # Module health score calculation
â”œâ”€â”€ report/
â”‚   â”œâ”€â”€ html_generator.py      # HTML report generation
â”‚   â”œâ”€â”€ json_generator.py      # JSON output
â”‚   â”œâ”€â”€ md_generator.py        # Markdown summary
â”‚   â””â”€â”€ templates/             # Jinja2 templates
â”‚       â”œâ”€â”€ report.html
â”‚       â”œâ”€â”€ module_section.html
â”‚       â””â”€â”€ metric_card.html
â””â”€â”€ utils/
    â”œâ”€â”€ file_utils.py          # File handling
    â”œâ”€â”€ ast_utils.py           # AST parsing helpers
    â”œâ”€â”€ config_utils.py        # Config loading
    â””â”€â”€ module_detector.py     # Module detection logic
````

### 8.2 Analysis Flow
````python
def analyze():
    1. Load configuration
    2. Detect modules from folder structure
    3. Scan directory for Python files
    4. Filter files (exclude patterns)
    5. For each file:
        a. Determine which module it belongs to
        b. Parse AST
        c. Run all analyzers
        d. Collect metrics (overall + per-module)
    6. Aggregate results:
        a. Overall metrics
        b. Per-module metrics
        c. Module comparisons
        d. Module dependency graph
    7. Calculate module health scores
    8. Calculate technical debt (overall + per-module)
    9. Generate module rankings
    10. Generate recommendations (overall + per-module)
    11. Create report(s)
````

### 8.3 Module Detection Logic
````python
def detect_modules(root_path, config):
    """
    Detect modules based on configuration.
    
    Auto mode: Use folder structure at specified depth
    Manual mode: Use explicitly defined modules
    """
    if config['module_detection']['method'] == 'manual':
        return config['module_detection']['manual_modules']
    
    # Auto detection
    depth = config['module_detection']['depth']
    modules = []
    
    for path in root_path.iterdir():
        if path.is_dir() and not should_exclude(path):
            # Check depth
            if get_folder_depth(path) == depth:
                modules.append({
                    'name': path.name,
                    'path': str(path.relative_to(root_path)),
                    'description': f"Module: {path.name}"
                })
    
    return modules

def get_module_for_file(file_path, modules, root_path):
    """Determine which module a file belongs to."""
    relative_path = file_path.relative_to(root_path)
    
    for module in modules:
        if str(relative_path).startswith(module['path']):
            return module['name']
    
    return 'root'  # Files not in any module
````

### 8.4 Code Organization Principles

1. **Single Responsibility:** Each analyzer handles one metric type
2. **Composition:** CodebaseAnalyzer composes all analyzers
3. **Modularity:** Each module analyzed independently
4. **Testability:** Each analyzer can be unit tested independently
5. **Extensibility:** Easy to add new analyzers or metrics
6. **Configuration-Driven:** Thresholds and options in config file

---

## 9. Success Criteria

### 9.1 Functional Requirements

âœ… The tool must:
1. Correctly detect modules from folder structure
2. Correctly count database operations (not just imports)
3. Accurately categorize ownership violations
4. Calculate all specified metrics (overall + per-module)
5. Generate module health scores
6. Create module comparison charts
7. Generate self-contained HTML report with module breakdown
8. Complete analysis in < 2 minutes for ~500 files
9. Handle encoding errors and syntax errors gracefully
10. Export JSON and Markdown with module data

### 9.2 Quality Requirements

âœ… The report must:
1. Be understandable by non-technical stakeholders
2. Provide clear "what it is" and "why it matters" for each metric
3. Include specific, actionable recommendations (overall + per-module)
4. Show file paths, modules, and line numbers for issues
5. Use color coding for severity (ðŸ”´ðŸŸ¡ðŸŸ¢)
6. Clearly show which modules need the most attention
7. Enable drilling down into specific modules
8. Be visually professional and print-friendly
9. Load without external dependencies (self-contained)

### 9.3 Educational Requirements

âœ… Each metric section must include:
1. Plain-language explanation
2. Code examples showing good vs bad
3. "Why it matters" section connecting to business impact
4. Clear thresholds with color coding
5. Actionable "what to do" section (overall + per-module)

### 9.4 Module-Specific Requirements

âœ… The module analysis must:
1. Correctly attribute files to modules
2. Calculate all metrics per-module
3. Provide module-to-module comparison
4. Rank modules by health/debt/coupling
5. Show cross-module dependencies
6. Provide module-specific recommendations
7. Enable filtering/sorting by module

### 9.5 Validation Criteria

âœ… The tool is successful if:
1. A manager can identify which modules/teams need help
2. A tech lead can prioritize refactoring by module
3. A developer can see their module's specific issues
4. A CTO can make architectural decisions based on module health
5. The analysis is reproducible (same input = same output)
6. The tool works on any Python codebase with minimal configuration
7. Module breakdown adds clear value over overall metrics alone

---

## 10. Deliverables

### 10.1 Code

- `analyze_codebase.py` - Main script
- `analyzers/` - All analyzer modules
- `report/` - Report generators and templates
- `utils/` - Utility functions including module detection
- `requirements.txt` - Dependencies
- `config.yaml.example` - Example configuration with module detection

### 10.2 Documentation

- `README.md` - Installation, usage, configuration, module detection
- Inline docstrings - All functions and classes
- Type hints - Function signatures

### 10.3 Examples

- Sample configuration file with module detection examples
- Sample output (HTML, JSON, Markdown) with module breakdown
- Example command usage with module-specific options

---

## 11. Future Enhancements (Out of Scope for V1)

- Historical trend analysis per module (compare reports over time)
- CI/CD integration (fail build if module thresholds exceeded)
- Integration with pytest for runtime test metrics per module
- Interactive web dashboard with module filtering
- Automatic refactoring suggestions with code diffs
- Git history analysis (code churn, authorship) per module
- Module-level ownership tracking (which team owns which module)
- Cross-repository module analysis (for poly-repo setups)

---

**END OF SPECIFICATION**

This document provides complete specifications for building the codebase analysis tool with comprehensive module/folder breakdown capability. Use this to instruct an AI coding assistant to implement the tool in Python.