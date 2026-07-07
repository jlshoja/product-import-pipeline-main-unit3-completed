# Migration 2 Discovery Report

## Purpose

This document captures the current repository state before any Migration 2 implementation work begins.

The goal is to document actual repository findings, identify structural risks, and define the target architecture for later approval.

---

## Repository Overview

The repository is organized around three active application areas and several support areas:

- `product_extraction/` is the primary pipeline and contains the most complete runtime state, configuration, reports, and logs.
- `import_builder/` is a secondary export and WooCommerce generation workflow with its own configuration, assets, and versioned scripts.
- `image_processing/` is a separate image workflow with its own batch files, runtime expectations, and standalone configuration.
- `data_standardization/` contains shared reference datasets and sample materials.
- `baseline/` contains sample inputs and outputs used as reference material.
- `docs/` contains the migration and architecture documentation set.

The repository already shows partial centralization effort, but the implementation is inconsistent. There are both root-level workspace folders and module-local copies of data, logs, reports, and assets.

---

## Current Folder Structure

### Root level

- `baseline/`
- `data/`
- `data_standardization/`
- `docs/`
- `image_processing/`
- `import_builder/`
- `logs/`
- `product_extraction/`
- `Project_Prompts/`
- `reports/`

### Observations

- Root-level `data/`, `logs/`, and `reports/` exist, but they are currently empty in the checked-in repository.
- The live module state is still concentrated under `product_extraction/`.
- Several runtime and output folders are also nested inside application modules instead of using the root workspace folders.

---

## Current Module Structure

### `product_extraction/`

Primary subpackages:

- `common/`
- `config/`
- `reports/`
- `scrapers/`
- `trackers/`
- `templates/`
- `utils/`

Current state files and runtime artifacts:

- `.env`
- `.env.example`
- `archive_urls.xlsx`
- `checkpoint.xlsx`
- `color_mapping.xlsx`
- `extracted_products.XLSX`
- `link_scraper_progress.json`
- `page_source.html`
- `product_details_complete.xlsx`
- `logs/*.log`
- `reports/outputs/*.html`

### `import_builder/`

Primary files and folders:

- `color_manager.py`
- `color_mapping.xlsx`
- `config_v9.py`
- `image_naming_v11_fixed.py`
- `image_processor_v9_1_fixed.py`
- `paths.py`
- `product_name_manager.py`
- `product_names.xlsx`
- `templates/`
- `docs/`
- `help/`
- `web_panel_v12.py`
- `woocommerce_generator_v12.py`

### `image_processing/`

Primary files and folders:

- `Image_Downloader.py`
- `menu.py`
- `unified_image_processor.py`
- `extracted_products.XLSX`
- `COMMAND_REFERENCE.md`
- `download_advanced.bat`
- `run_menu.bat`

### `data_standardization/`

Reference assets:

- `pricing_sample.xlsx`
- `product_full_processor_fast.html`
- `standard_categories.xlsx`
- `standar_colors.xlsx`
- `word index.xlsx`

### `baseline/`

Reference samples:

- `sample_input/archive_urls.xlsx`
- `sample_output/product.csv`
- `sample_output/product_details_complete.xlsx`
- `sample_output/extracted_products.xlsx`
- `sample_output/woocommerce_import_20260701_225257.csv`

---

## Current Configuration Locations

Current configuration is scattered across several layers:

- `product_extraction/config/settings.py`
- `product_extraction/config/history_config.py`
- `product_extraction/common/file_registry.py`
- `product_extraction/common/path_registry.py`
- `product_extraction/common/configuration.py`
- `product_extraction/common/config_registry.py`
- `product_extraction/common/file_utils.py`
- `import_builder/paths.py`
- `import_builder/config_v9.py`
- `import_builder/web_panel_v12.py`
- `import_builder/woocommerce_generator_v12.py`
- `image_processing/menu.py`
- `image_processing/Image_Downloader.py`

Current configuration findings:

- `product_extraction` has a partial central config package, but the module still uses literal filenames in multiple places.
- `product_extraction/common/file_registry.py` and `product_extraction/common/path_registry.py` exist, but they are not yet the single source of truth for the repository.
- `import_builder` still keeps its own file and path assumptions.
- `image_processing` still reads file names and runtime folders directly from script-local defaults and environment variables.
- Several scripts assume a specific repository layout and do not resolve paths from a shared registry.

---

## Current Path Management Locations

Path handling currently appears in:

- `product_extraction/common/path_registry.py`
- `product_extraction/config/settings.py`
- `product_extraction/utils/logger.py`
- `product_extraction/reports/dashboard_generator.py`
- `product_extraction/scrapers/link_scraper.py`
- `product_extraction/scrapers/spec_scraper.py`
- `product_extraction/trackers/price_tracker.py`
- `product_extraction/trackers/compare_scans.py`
- `import_builder/paths.py`
- `import_builder/config_v9.py`
- `import_builder/web_panel_v12.py`
- `import_builder/woocommerce_generator_v12.py`
- `image_processing/menu.py`
- `image_processing/Image_Downloader.py`

Observed path issues:

- Some modules resolve the repository root relative to their own file.
- Some modules fall back to cwd-dependent relative paths.
- Some modules assume legacy parent folders such as `../uploads` or `../../4_Product_import/uploads`.
- Some runtime folders are created inside module directories while other modules expect root-level folders.

---

## Current Data Locations

Checked-in data and reference material currently live in multiple places:

- Root `data/` exists but is empty in the current checkout.
- `data_standardization/` contains shared reference spreadsheets and a reference HTML file.
- `baseline/sample_input/` and `baseline/sample_output/` contain reference IO artifacts.
- `product_extraction/` contains active operational spreadsheets and state files.
- `import_builder/` contains mapping spreadsheets used by its workflows.
- `image_processing/` contains a workflow input spreadsheet and command reference material.

Examples of current data assets:

- `product_extraction/archive_urls.xlsx`
- `product_extraction/extracted_products.XLSX`
- `product_extraction/product_details_complete.xlsx`
- `product_extraction/color_mapping.xlsx`
- `product_extraction/checkpoint.xlsx`
- `import_builder/color_mapping.xlsx`
- `import_builder/product_names.xlsx`
- `data_standardization/standard_categories.xlsx`
- `data_standardization/standar_colors.xlsx`
- `data_standardization/pricing_sample.xlsx`
- `data_standardization/word index.xlsx`

---

## Current Runtime Artifact Locations

Runtime artifacts are scattered across the repository:

- `product_extraction/logs/` contains `main.log`, `tracker.log`, and `error.log`.
- `product_extraction/reports/outputs/` contains generated HTML reports.
- `product_extraction/link_scraper_progress.json` persists scraping state.
- `product_extraction/checkpoint.xlsx` stores incremental checkpoint data.
- `product_extraction/page_source.html` is a captured runtime artifact.
- `product_extraction/__pycache__/` and nested `__pycache__/` directories are present across modules.
- `image_processing/` uses runtime state files such as `download_state.json` and generated download folders.
- `import_builder/` scripts produce uploads, named image outputs, and generated CSV files through hardcoded or inferred folders.

The main runtime problem is that generated artifacts are not consistently separated from source code or from reference datasets.

---

## Current Documentation Locations

Documentation is also scattered:

- Root-level operational and migration docs live in `docs/`.
- Module-specific docs live in `import_builder/docs/`, `image_processing/COMMAND_REFERENCE.md`, and `Project_Prompts/`.
- Some support documentation is embedded directly in scripts via large inline comments and strings.
- Several legacy or versioned scripts have their own embedded run instructions instead of referencing a shared operational guide.

This makes it harder to understand which documentation is authoritative and which is legacy guidance.

---

## Current Image Storage Locations

Image-related storage and assumptions appear in multiple places:

- `import_builder/config_v9.py` assumes a dated source image tree at a user-specific absolute path and a remote WordPress uploads path.
- `import_builder/web_panel_v12.py` and `woocommerce_generator_v12.py` assume `product-images` and `uploads` folders.
- `image_processing/` assumes downloadable images and a local download workspace.
- The repository does not currently show a committed canonical root-level `product-images/` asset folder.

---

## Current Reporting Locations

Reporting is split between module-local and root-level expectations:

- `product_extraction/reports/outputs/` stores generated dashboard HTML.
- `product_extraction/reports/templates/` stores dashboard templates.
- `product_extraction/trackers/price_tracker.py` and `compare_scans.py` generate or locate report artifacts.
- Root `reports/` exists, but the live report output currently remains under `product_extraction/reports/`.

---

## Current Logging Locations

Logging is not fully standardized:

- `product_extraction/logs/` is the active log destination used by the current module.
- Root `logs/` exists but is not yet the active logging home for all workflows.
- `import_builder/paths.py` also defines a `logs` directory relative to its own module.
- Some scripts still write logs in the current working directory or infer them from local execution context.

---

## Current Checkpoint Locations

Checkpoint and progress data is split across several files:

- `product_extraction/checkpoint.xlsx`
- `product_extraction/link_scraper_progress.json`
- `image_processing/download_state.json`
- `product_extraction/scrapers/spec_scraper.py` uses `scraper_progress.json` in the legacy implementation path

This creates confusion about which file is the authoritative recovery state for each workflow.

---

## Identified Problems

### Data scattering

- Core pipeline datasets are stored under `product_extraction/`.
- Reference datasets are stored under `data_standardization/`.
- Sample inputs and outputs are stored under `baseline/`.
- Mapping spreadsheets are duplicated between `product_extraction/` and `import_builder/`.
- The root `data/` directory is present but not yet used as the canonical data home.

### Runtime artifact scattering

- Logs are stored under `product_extraction/logs/`.
- Reports are stored under `product_extraction/reports/outputs/`.
- Recovery and progress files are stored next to the code that generates them.
- `__pycache__` directories and captured HTML files are mixed into source trees.

### Asset scattering

- Image workflow assumptions are spread between `image_processing/` and `import_builder/`.
- `help/` documents and PDFs are stored inside `import_builder/`.
- Template files live in module-local folders.
- Mapping spreadsheets live in more than one module folder.

### Repository discoverability issues

- There is no single visible workspace map for inputs, outputs, runtime state, assets, and reference data.
- Versioned scripts such as `v9`, `v11`, and `v12` make it harder to identify the active implementation.
- Some documentation describes a future structure that is not yet fully reflected in the repository.

### Maintenance risks

- Hardcoded filenames make renames risky.
- Legacy relative path traversal breaks when folders move.
- Duplicate mapping files can diverge.
- Module-local config files encourage each workflow to become its own source of truth.

### Long-term maintainability risks

- The repository will become harder to refactor if runtime and reference assets stay mixed.
- New workflows will likely copy the current pattern of local defaults unless a single repository standard is adopted.
- Debugging will remain slow as long as the active file home varies by module.
- Compatibility will be fragile until path resolution is centralized.

### Opportunities for standardization

- Introduce one shared path and file registry.
- Separate source code from runtime output and reference data.
- Distinguish between inputs, intermediates, outputs, mappings, templates, and logs.
- Preserve compatibility shims while moving module code to shared definitions.

### Potential migration risks

- Hidden consumers may still depend on the current module-local file locations.
- Changing file homes before registry adoption could break workflows.
- Duplicate mapping files may not have identical content.
- Versioned legacy scripts may not be maintained in parallel.

---

## Recommendations

### Target repository layout

Proposed long-term workspace layout:

```text
product-import-pipeline/
  docs/
    migration2/
    architecture/
    operational/
  data/
    inputs/
    intermediate/
    outputs/
    mappings/
    reference/
    archives/
  runtime/
    logs/
    reports/
    state/
    cache/
  assets/
    images/
    templates/
    help/
  shared/
    config/
    paths/
    files/
  product_extraction/
  image_processing/
  import_builder/
  data_standardization/
  baseline/
```

### Target configuration strategy

- Keep one authoritative shared registry for paths, files, and environment variables.
- Treat module-local config files as compatibility shims only.
- Centralize environment variables in a single loader and document defaults.
- Separate static file names from environment-specific values.

### Target path management strategy

- Resolve all repository paths from the repository root.
- Remove cwd-dependent fallbacks and legacy parent traversal.
- Use shared helpers for all input, output, and runtime locations.
- Keep path definitions data-driven instead of hardcoded inside workflows.

### Target runtime layout

- Put all generated logs in `runtime/logs/`.
- Put generated HTML and export reports in `runtime/reports/`.
- Put progress, checkpoint, and recovery state in `runtime/state/`.
- Put transient cache and working files in `runtime/cache/`.

### Target data layout

- Put canonical user-provided inputs in `data/inputs/`.
- Put workflow intermediates in `data/intermediate/`.
- Put final outputs in `data/outputs/`.
- Put shared mapping spreadsheets in `data/mappings/`.
- Put reference datasets and samples in `data/reference/`.
- Put archive or historical samples in `data/archives/`.

### Target documentation layout

- Keep migration material in `docs/migration2/`.
- Keep architecture and standards references in `docs/architecture/`.
- Keep operational runbooks and workflow notes in `docs/operational/`.
- Keep module-local README files for module-specific usage only.

### Target asset layout

- Put reusable image assets in `assets/images/`.
- Put reusable HTML and UI templates in `assets/templates/`.
- Put user-facing help documents in `assets/help/` or `docs/operational/` based on purpose.
- Avoid storing generated assets beside source files.

### Target naming conventions

- Use lowercase `snake_case` for files, folders, and modules.
- Avoid spaces in new file names.
- Avoid version suffixes in active source modules unless the suffix is part of a public release artifact.
- Use date stamps in outputs only when the artifact is intentionally time-based.
- Prefer stable canonical names such as `latest`, `state`, `template`, `reference`, `input`, and `output`.

### Target repository standards

- One authoritative source for every file name and path.
- No hidden cwd assumptions.
- No hardcoded parent directory traversal in production code.
- No checked-in generated runtime outputs unless they are intentional baselines or examples.
- Compatibility first, then consolidation.
- Structural changes must be validated before legacy locations are retired.

---

## Status

Complete

