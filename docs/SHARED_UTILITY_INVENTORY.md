# Shared Utility Inventory

## Executive Summary

The repository contains multiple areas where functionality is duplicated across modules. The largest consolidation opportunities are:

1. Color management
2. Excel file operations
3. File/path handling
4. Progress/state persistence
5. Logging
6. Image processing helpers
7. Configuration loading

Consolidating these areas would reduce maintenance cost and migration risk while improving consistency.

---

# Candidate 1 — Color Management Utilities

## Location

```text
product_extraction/color_manager.py
product_extraction/utils/color_manager.py
import_builder/color_manager.py
```

## Usage Count

High (used throughout extraction and import workflows)

## Dependencies

* color_mapping.xlsx
* pandas
* openpyxl

## Duplicate Logic

* Color normalization
* Color matching
* Color lookup
* Mapping file loading
* Similarity calculations

## Status

PARTIAL COMPLETE within approved Unit 6 product_extraction scope.

Implemented:

```text
product_extraction/common/color_utils.py
```

Unit 6 centralized shared helpers for:

```python
normalize_persian_color_text()
simple_color_slug()
split_color_values()
collect_unique_normalized_colors()
```

Approved consumers migrated:

```text
product_extraction/color_manager.py
product_extraction/utils/color_manager.py
product_extraction/scrapers/spec_scraper.py
```

Deferred:

```text
import_builder/color_manager.py
import_builder/color_mapping.xlsx
image_processing/
product_extraction/scrapers/Old/ (archive-only)
```

## Migration Complexity

Medium

## Consolidation Recommendation

Create:

```text
shared/color_manager.py
```

Current migration implementation uses:

```text
product_extraction/common/color_utils.py
```

Expose:

```python
normalize_color()
lookup_color()
load_color_mapping()
find_closest_color()
```

Priority: Critical

---

# Candidate 2 — Excel File Loading

## Location

Observed across:

```text
link_scraper.py
spec_scraper.py
price_tracker.py
woocommerce_generator_v12.py
Image_Downloader.py
product_name_manager.py
```

## Usage Count

Very High

## Dependencies

* pandas
* openpyxl

## Duplicate Logic

Repeated:

```python
pd.read_excel(...)
```

Validation logic.

File existence checks.

Error handling.

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/excel_utils.py
```

Functions:

```python
read_excel()
write_excel()
append_excel()
validate_excel()
backup_excel()
```

Priority: Critical

---

# Candidate 3 — Excel Export Operations

## Location

Multiple modules generating:

```text
.xlsx
.csv
```

files.

## Usage Count

High

## Dependencies

* pandas
* openpyxl

## Duplicate Logic

* Export generation
* Sheet creation
* Dataframe persistence
* Backup creation

## Migration Complexity

Low

## Consolidation Recommendation

Merge into:

```text
shared/excel_utils.py
```

Priority: High

---

# Candidate 4 — Progress Tracking

## Location

```text
link_scraper.py
spec_scraper.py
Image_Downloader.py
```

Status: NEXT - Unit 5 discovery/design pending.

## Usage Count

Medium

## Dependencies

* json

## Duplicate Logic

* Save progress
* Load progress
* Resume processing
* State recovery

Files:

```text
scraper_progress.json
link_scraper_progress.json
download_state.json
```

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/progress_manager.py
```

Functions:

```python
load_state()
save_state()
reset_state()
```

Priority: High

---

# Candidate 5 — File Existence Validation

## Location

Many modules.

Status: COMPLETE within Unit 4 approved product_extraction scope.

## Usage Count

Very High

## Dependencies

* pathlib
* os

## Duplicate Logic

Repeated:

```python
os.path.exists()
Path.exists()
```

plus validation wrappers.

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/file_utils.py
```

Functions:

```python
ensure_exists()
ensure_directory()
safe_delete()
safe_move()
```

Implemented:

```text
product_extraction/common/file_utils.py
```

Unit 4 added ensure_exists(), ensure_directory(), safe_copy(), safe_delete(), and migrated approved product_extraction consumers.

Priority: High

---

# Candidate 6 — Path Construction

## Location

Throughout repository.

Status: PARTIAL - Unit 4 added dated file lookup only; broader path construction remains deferred.

## Usage Count

Very High

## Dependencies

* pathlib
* os

## Duplicate Logic

* Relative path construction
* Directory discovery
* Upload path generation

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/path_utils.py
```

Functions:

```python
get_data_path()
get_report_path()
get_upload_path()
```

Priority: Critical

---

# Candidate 7 — Logging Helpers

## Location

Extraction modules
Import builder
Reporting

## Usage Count

Medium

## Dependencies

* logging

## Duplicate Logic

* Logger creation
* File logger setup
* Error logger setup

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/logging_utils.py
```

Functions:

```python
get_logger()
configure_logging()
```

Priority: Medium

---

# Candidate 8 — Image Download Helpers

## Location

```text
Image_Downloader.py
image processing modules
```

## Usage Count

Medium

## Dependencies

* requests
* PIL

## Duplicate Logic

* Download image
* Validate image
* Save image

## Migration Complexity

Medium

## Consolidation Recommendation

Create:

```text
shared/image_download_utils.py
```

Functions:

```python
download_image()
validate_image()
save_image()
```

Priority: Medium

---

# Candidate 9 — Image Naming Logic

## Location

```text
image_naming_v11_fixed.py
woocommerce_generator_v12.py
```

## Usage Count

Medium

## Dependencies

* color mapping
* product naming

## Duplicate Logic

* Image naming conventions
* Filename sanitization
* Variant naming

## Migration Complexity

Medium

## Consolidation Recommendation

Create:

```text
shared/image_naming.py
```

Priority: Medium

---

# Candidate 10 — DataFrame Validation

## Location

Multiple modules.

## Usage Count

High

## Dependencies

* pandas

## Duplicate Logic

Checking:

```python
required columns
missing values
empty dataframe
```

## Migration Complexity

Low

## Consolidation Recommendation

Create:

```text
shared/dataframe_utils.py
```

Functions:

```python
validate_columns()
validate_dataframe()
```

Priority: High

---

# Candidate 11 — Configuration Loading

## Location

```text
settings.py
history_config.py
config_v9.py
paths.py
```

## Usage Count

High

## Dependencies

Configuration files.

## Duplicate Logic

* Path loading
* Filename loading
* Mapping loading

## Migration Complexity

Medium

## Consolidation Recommendation

Create:

```text
shared/config_loader.py
```

Priority: Critical

---

# Candidate 12 — Report Generation Helpers

## Location

```text
dashboard_generator.py
compare_scans.py
```

## Usage Count

Medium

## Dependencies

* pandas
* templates

## Duplicate Logic

* Report creation
* Report export
* Summary generation

## Migration Complexity

Medium

## Consolidation Recommendation

Create:

```text
shared/report_utils.py
```

Priority: Medium

---

# Common File Operations Inventory

| Operation             | Usage Level | Consolidation Priority |
| --------------------- | ----------- | ---------------------- |
| File existence checks | Very High   | High                   |
| Directory creation    | High        | High                   |
| File copying          | Medium      | Medium                 |
| File moving           | Medium      | Medium                 |
| Backup creation       | High        | High                   |
| JSON persistence      | High        | High                   |

---

# Common Excel Operations Inventory

| Operation        | Usage Level | Consolidation Priority |
| ---------------- | ----------- | ---------------------- |
| Read workbook    | Very High   | Critical               |
| Write workbook   | Very High   | Critical               |
| Append rows      | High        | High                   |
| Validate columns | High        | High                   |
| Export CSV       | High        | Medium                 |
| Backup workbook  | Medium      | High                   |

---

# Common Image Operations Inventory

| Operation            | Usage Level | Consolidation Priority |
| -------------------- | ----------- | ---------------------- |
| Download image       | High        | Medium                 |
| Save image           | High        | Medium                 |
| Validate image       | Medium      | Medium                 |
| Rename image         | Medium      | Medium                 |
| Generate image paths | High        | High                   |

---

# Recommended Shared Package Structure

```text
shared/
│
├── excel_utils.py
├── file_utils.py
├── path_utils.py
├── progress_manager.py
├── logging_utils.py
├── dataframe_utils.py
├── config_loader.py
│
├── color_manager.py
├── image_download_utils.py
├── image_naming.py
│
└── report_utils.py
```

---

# Consolidation Priority Ranking

## Priority 1 (Highest Value)

1. color_manager
2. excel_utils
3. path_utils
4. config_loader

---

## Priority 2

5. progress_manager
6. dataframe_utils
7. file_utils

---

## Priority 3

8. image utilities
9. report utilities
10. logging utilities

---

# Migration Assessment

Estimated Risk: Medium

Reason:

Most candidates are utility-layer abstractions and can be introduced incrementally without changing business logic.

Recommended Strategy:

* Create shared utilities first.
* Add compatibility wrappers.
* Migrate consumers gradually.
* Remove duplicates only after validation.

This approach supports a low-risk, reversible migration path consistent with the overall migration strategy.

---

# Unit 7 Phase 3 Implementation Results

Status: COMPLETE

Implemented shared utility modules:

```text
product_extraction/common/date_utils.py
product_extraction/common/price_utils.py
product_extraction/common/text_utils.py
```

Compatibility wrappers updated:

```text
product_extraction/trackers/helpers.py
```

Consumer updated:

```text
product_extraction/trackers/price_tracker.py
```

Behavior preserved:

```python
gregorian_to_jalali()
get_persian_date()
extract_price_from_text()
extract_product_name()
extract_product_code()
format_number()
```

Validation completed:

* Compile validation
* Shared helper regression checks
* Import validation
* Diff whitespace validation

Remaining risk:

* `product_extraction/reports/dashboard_generator.py` price display formatting remains intentionally local because its `"N/A"` and currency-label behavior differs from the shared generic formatter.

---

# Unit 7 Phase 4 Implementation Results

Status: COMPLETE

Implemented dashboard helper consolidation:

```text
product_extraction/reports/dashboard_generator.py
```

Behavior preserved:

```python
DashboardGenerator._get_persian_date()
```

Validation completed:

* Compile validation for `dashboard_generator.py`
* Targeted dashboard shared date helper behavior check
* Import validation
* Diff whitespace validation

---

# Unit 7 Phase 5 Implementation Results

Status: COMPLETE

Implemented tracker report helper consolidation:

```text
product_extraction/trackers/report_generator.py
```

Behavior preserved:

```python
generate_new_products_excel()
generate_price_changes_excel()
generate_html_report()
generate_excel_report()
```

Validation completed:

* Compile validation for `report_generator.py`
* Import validation
* Targeted report output checks
* Diff whitespace validation

---

# Unit 8 Implementation Results

Status: COMPLETE

Implemented shared helpers:

```text
product_extraction/common/file_utils.py
product_extraction/common/price_utils.py
```

Shared helper additions:

```python
find_first_glob_match()
select_effective_price()
parse_numeric_price()
```

Tracked consumer updates:

```text
product_extraction/trackers/compare_scans.py
product_extraction/trackers/price_tracker.py
```

Behavior preserved:

```python
compare_scans.py helper compatibility wrappers
price_tracker.py helper compatibility wrappers
package imports
direct imports
direct-script execution
```

Validation completed:

* Compile validation for changed Python modules
* Package import validation
* Direct import validation
* Direct-script smoke validation for compare_scans and price_tracker
* Diff whitespace validation
