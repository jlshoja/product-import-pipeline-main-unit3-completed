# Migration 2 Phase 2 Layout Map

## Purpose

This document classifies the repository's current data, runtime, and asset files against the target layout defined in Migration 2.

No files are moved in this phase. The goal is to define the canonical home for each artifact so later migration steps can move them in a controlled way.

---

## Canonical Targets

Target layout:

- `data/inputs/` for source spreadsheets that start a workflow
- `data/intermediate/` for handoff spreadsheets between pipeline stages
- `data/outputs/` for durable workflow outputs
- `data/mappings/` for shared mapping spreadsheets
- `data/reference/` for sample and reference datasets
- `runtime/logs/` for logs
- `runtime/reports/` for generated reports
- `runtime/state/` for progress, checkpoints, and recovery state
- `runtime/cache/` for transient working files
- `assets/images/` for reusable image assets
- `assets/templates/` for reusable HTML or UI templates
- `assets/help/` for user-facing help material

---

## Data Classification

| Current location | Artifact type | Canonical home | Notes |
| --- | --- | --- | --- |
| `product_extraction/archive_urls.xlsx` | Input spreadsheet | `data/inputs/archive_urls.xlsx` | Primary scraper seed file. |
| `product_extraction/extracted_products.XLSX` | Handoff spreadsheet | `data/intermediate/extracted_products.xlsx` | Link scraper output and spec-scraper input. |
| `product_extraction/product_details_complete.xlsx` | Output spreadsheet | `data/outputs/product_details_complete.xlsx` | Final enriched product detail export. |
| `product_extraction/color_mapping.xlsx` | Mapping spreadsheet | `data/mappings/color_mapping.xlsx` | Shared color mapping. |
| `import_builder/color_mapping.xlsx` | Mapping spreadsheet | `data/mappings/color_mapping.xlsx` | Duplicate of the shared mapping. |
| `import_builder/product_names.xlsx` | Mapping spreadsheet | `data/mappings/product_names.xlsx` | Shared product-name translation table. |
| `image_processing/extracted_products.XLSX` | Input spreadsheet | `data/inputs/extracted_products.xlsx` or `data/intermediate/extracted_products.xlsx` | Workflow-specific consumer of the same handoff sheet. |
| `data_standardization/standard_categories.xlsx` | Reference dataset | `data/reference/standard_categories.xlsx` | Curated standard list. |
| `data_standardization/standar_colors.xlsx` | Reference dataset | `data/reference/standar_colors.xlsx` | Curated standard list. |
| `data_standardization/pricing_sample.xlsx` | Reference dataset | `data/reference/pricing_sample.xlsx` | Sample/reference workbook. |
| `data_standardization/word index.xlsx` | Reference dataset | `data/reference/word index.xlsx` | Reference lookup material. |
| `baseline/sample_input/archive_urls.xlsx` | Sample input | `data/reference/sample_input/archive_urls.xlsx` | Baseline fixture. |
| `baseline/sample_output/*.xlsx` and `.csv` | Sample output | `data/reference/sample_output/` | Baseline fixture outputs. |

---

## Runtime Classification

| Current location | Artifact type | Canonical home | Notes |
| --- | --- | --- | --- |
| `product_extraction/logs/main.log` | Log file | `runtime/logs/main.log` | Main pipeline log. |
| `product_extraction/logs/tracker.log` | Log file | `runtime/logs/tracker.log` | Price tracker log. |
| `product_extraction/logs/error.log` | Log file | `runtime/logs/error.log` | Shared error log. |
| `product_extraction/reports/outputs/dashboard_2026-07-07.html` | Generated report | `runtime/reports/dashboard_2026-07-07.html` | Generated dashboard output. |
| `product_extraction/checkpoint.xlsx` | Checkpoint | `runtime/state/checkpoint.xlsx` | Link scraper incremental checkpoint. |
| `product_extraction/link_scraper_progress.json` | Progress state | `runtime/state/link_scraper_progress.json` | Link scraper resume state. |
| `image_processing/downloaded_images/download_state.json` | Progress state | `runtime/state/download_state.json` | Image downloader resume state. |
| `image_processing/downloaded_images/<timestamp>/...` | Download cache | `runtime/cache/` or `runtime/state/` subfolders | Transient download work area. |
| `product_extraction/page_source.html` | Captured runtime artifact | `runtime/cache/page_source.html` | Snapshot of retrieved HTML. |

---

## Asset Classification

| Current location | Artifact type | Canonical home | Notes |
| --- | --- | --- | --- |
| `product_extraction/reports/templates/dashboard_template.html` | HTML template | `assets/templates/dashboard_template.html` | Reusable dashboard template. |
| `import_builder/templates/index.html` | HTML template | `assets/templates/import_builder/index.html` | Module-specific UI template, if promoted. |
| `import_builder/help/*.docx` and `*.pdf` | Help content | `assets/help/import_builder/` | User-facing support material. |
| `image_processing/downloaded_images/` | Image output workspace | `assets/images/` or `runtime/cache/` | Generated images are transient unless promoted. |
| `import_builder/config_v9.py` image source assumptions | External asset dependency | `assets/images/` | This is an assumption to be replaced, not a file move. |

---

## Compatibility Decisions

- Keep legacy file locations readable during migration.
- Prefer canonical targets for all new writes.
- Treat duplicate module-local spreadsheets as compatibility copies until later cleanup.
- Keep runtime artifacts out of source folders once the move is approved.

---

## Recommended Phase 2 Outcomes

1. Approve the canonical homes listed above.
2. Decide which module-local spreadsheets become shared mappings and which remain module-private.
3. Decide whether `image_processing/downloaded_images/` should become a runtime cache or a preserved asset area.
4. Move only the lowest-risk shared mappings first, after the directory targets are approved.

---

## Physical Moves Completed

- `import_builder/color_mapping.xlsx` -> `data/mappings/color_mapping.xlsx`
- `import_builder/product_names.xlsx` -> `data/mappings/product_names.xlsx`

Notes:

- `product_extraction/color_mapping.xlsx` remains in place as a legacy fallback copy for now.
- The canonical mapping readers now point to `data/mappings/`.
