# Migration 2 Architecture

## Purpose

This document defines the target repository architecture for Migration 2.

It reflects the current repository findings and provides the target structure for later implementation work.

---

## Current State

The repository is partially standardized but still fragmented.

Key current-state findings:

- `product_extraction/` contains the most complete operational runtime state, logs, and outputs.
- `import_builder/` contains its own configuration files, mapping spreadsheets, and versioned scripts.
- `image_processing/` contains standalone scripts and runtime assumptions that are not aligned with the other workflows.
- `data_standardization/` stores reference datasets separately from the active workflows.
- `baseline/` stores sample input and output artifacts separately from live data and runtime output.
- Root-level `data/`, `logs/`, and `reports/` exist but are not yet the common home for all workflows.

The current state has these architectural issues:

- multiple file registries
- multiple path registries
- module-local runtime folders
- duplicated mapping files
- cwd-dependent path assumptions
- versioned implementation scripts with overlapping responsibility

---

## Target State

The target state is a repository with one canonical workspace layout and one canonical configuration layer.

Target goals:

- code lives in module folders
- data lives in canonical data folders
- runtime output lives in canonical runtime folders
- shared assets live in canonical asset folders
- documentation lives in a predictable docs hierarchy
- all paths resolve from the repository root
- module code reads file and path definitions from a shared registry

---

## Repository Layout Strategy

Proposed target layout:

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
    paths.py
    files.py
    environment.py
  product_extraction/
  image_processing/
  import_builder/
  data_standardization/
  baseline/
```

Architecture intent:

- keep source code and runtime output separate
- keep reference datasets separate from generated outputs
- keep shared configuration in one location
- keep module-specific behavior inside the module that owns it

---

## Configuration Strategy

Target configuration model:

- one shared environment loader
- one shared file registry
- one shared path registry
- module-local configuration only for workflow-specific options that cannot be generalized

Rules:

- no workflow should infer the repository layout from cwd
- no workflow should hardcode parent traversals for shared folders
- no workflow should own a duplicate copy of a canonical shared mapping file
- environment values should be documented and validated in one place

Current repo evidence that supports this strategy:

- `product_extraction/common/file_registry.py` already centralizes some filenames.
- `product_extraction/common/path_registry.py` already centralizes some paths.
- `product_extraction/config/settings.py` already defines directory and file defaults.
- `import_builder/paths.py` and `import_builder/config_v9.py` still duplicate related concerns.

---

## Path Management Strategy

Target path strategy:

- resolve the repository root once
- derive every canonical path from that root
- use path helpers for all file reads and writes
- use compatibility adapters while migrating legacy code

Rules:

- paths must be deterministic
- no module should depend on the current working directory for core inputs or outputs
- no module should traverse legacy parent directories such as `../../4_Product_import/uploads`
- all report and log destinations should be rooted in the shared runtime layout

---

## Runtime Strategy

Target runtime layout:

- `runtime/logs/` for application and workflow logs
- `runtime/reports/` for generated HTML, CSV, and Excel deliverables that are not user inputs
- `runtime/state/` for progress files, checkpoints, and recovery data
- `runtime/cache/` for transient working files

Runtime rules:

- generated state should not live beside source code
- temporary files should not be treated as canonical inputs
- runtime artifacts should be ignored by normal source review unless they are intentional samples

---

## Data Strategy

Target data layout:

- `data/inputs/` for user-provided source files
- `data/intermediate/` for pipeline handoff artifacts
- `data/outputs/` for canonical final outputs that should persist between runs
- `data/mappings/` for shared spreadsheets such as color and naming tables
- `data/reference/` for curated samples, standard lists, and benchmark material
- `data/archives/` for historical snapshots and preserved outputs

Current evidence for this strategy:

- `product_extraction/archive_urls.xlsx`, `extracted_products.XLSX`, and `product_details_complete.xlsx` are pipeline handoff artifacts.
- `import_builder/color_mapping.xlsx` and `import_builder/product_names.xlsx` are shared mapping assets.
- `data_standardization/standard_categories.xlsx`, `standar_colors.xlsx`, `pricing_sample.xlsx`, and `word index.xlsx` are reference material.
- `baseline/sample_input/` and `baseline/sample_output/` are sample and archive material.

---

## Documentation Strategy

Target documentation layout:

- `docs/migration2/` for migration planning and status
- `docs/architecture/` for long-lived architecture references
- `docs/operational/` for runbooks and workflow instructions
- module-local docs only when they describe module-specific behavior that is not useful at the repository level

Rules:

- one authoritative doc for each repository-wide policy
- legacy docs may remain as historical context, but they should not be treated as primary standards if they conflict with the canonical docs
- migration docs should describe actual repository findings and approved target behavior

---

## Asset Strategy

Target asset layout:

- `assets/images/` for reusable image assets
- `assets/templates/` for reusable HTML or UI templates
- `assets/help/` for user-facing help files and guides when they are not module-specific
- `data/reference/` for spreadsheets that act as reference datasets rather than runtime assets

Current asset issues:

- image workflow assumptions are scattered across multiple scripts
- `import_builder/help/` stores help artifacts inside the code tree
- module-local templates and generated output currently coexist
- mapping spreadsheets are duplicated across modules

---

## Migration Rules

1. No business logic changes.
2. No algorithm changes.
3. No feature additions.
4. Structural changes only.
5. All changes must be documented.
6. Every structural change must have validation.
7. Every structural change must have rollback capability.
8. Compatibility comes before cleanup.
9. Shared registries must exist before module code is migrated to them.
10. Legacy locations must remain available until verification is complete.

---

## Validation Requirements

Validation for later implementation phases should confirm:

- every active workflow resolves paths from the repository root or shared registry
- every canonical file exists in only one primary location
- runtime outputs are written to the runtime layout
- report generation still works from the canonical report directory
- image workflows still resolve inputs and outputs correctly
- the repository still runs from the approved entry points
- legacy compatibility shims can be removed without breaking functionality

---

## Open Architectural Decisions

- Whether `shared/` becomes the canonical repository-wide configuration package or whether `product_extraction/common/` remains the migration anchor with root-level adapters.
- Whether `data_standardization/` remains a reference dataset area or becomes part of the canonical `data/reference/` tree during the implementation phase.
- Whether module-specific template folders are preserved or consolidated into `assets/templates/`.
- Which legacy versioned scripts will be retained as compatibility entry points and which will be retired.

---

## Status

Complete

