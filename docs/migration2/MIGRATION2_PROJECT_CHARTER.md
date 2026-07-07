# Migration 2 Project Charter

## Project Name

Migration 2 - Repository Standardization and Asset Organization

---

## Background

The repository completed an earlier modularization effort and now functions across several workflows:

- `product_extraction/` for scraping, tracking, and reporting
- `import_builder/` for WooCommerce export and image preparation
- `image_processing/` for image download and rename workflows
- `data_standardization/` for reference datasets

The codebase is usable, but repository structure, file naming, runtime layout, and asset placement are inconsistent. Several modules still depend on cwd-relative paths, duplicated mapping files, and module-local runtime folders.

Migration 2 is a repository organization effort. It does not change business logic.

---

## Business Motivation

The current repository layout increases maintenance cost and migration risk.

- Developers must know where each module stores its inputs, outputs, and runtime state.
- Small renames can break workflows because filenames are hardcoded in multiple places.
- Shared mapping files are duplicated across modules.
- Legacy scripts and versioned scripts reduce discoverability.
- Runtime artifacts are mixed with source files, which makes the repository harder to audit and support.

The business value of this migration is lower maintenance effort, fewer path-related breakages, and a clearer structure for future work.

---

## Current Problems

- Configuration is scattered across several modules and partially duplicated.
- Path handling is inconsistent and sometimes cwd-dependent.
- Runtime artifacts are mixed with source code.
- Reference datasets and sample outputs are stored in more than one location.
- Image assets and upload assumptions are fragmented across workflows.
- Documentation exists at both root and module level with overlapping intent.

---

## Objectives

- Establish a single repository layout standard.
- Define one authoritative path and file management strategy.
- Separate runtime artifacts from source code.
- Consolidate reference data, mappings, and sample assets into predictable locations.
- Reduce the number of hardcoded filenames and directory assumptions.
- Preserve current functionality throughout the migration.
- Document the target architecture and the phased migration path before implementation starts.

---

## Scope

Included in scope:

- Repository discovery and inventory
- Target repository layout definition
- Target configuration and path strategy definition
- Runtime, data, documentation, and asset layout definition
- Migration roadmap refinement
- Validation and rollback planning for later implementation work

---

## Out Of Scope

- Business logic changes
- Algorithm changes
- Feature additions
- Performance optimization
- UI redesign
- Database introduction or schema changes
- Implementation of the structural migration itself

---

## Success Criteria

- The discovery report accurately reflects current repository findings.
- The charter, architecture, roadmap, and status documents are completed and aligned.
- The target repository layout is clearly defined.
- The path and file strategy is unambiguous.
- The migration phases are ordered to minimize breakage risk.
- Known risks and open decisions are explicitly captured.
- The phase 0 work is ready for approval before implementation planning begins.

---

## Risks

- Hidden file dependencies may not be visible from static scans alone.
- Duplicate mapping files may not contain identical data.
- Legacy scripts may continue to assume module-local folders.
- Versioned scripts may be difficult to retire in later phases.
- Some workflows may depend on environment-specific paths that are not yet documented.

---

## Deliverables

- `docs/migration2/MIGRATION2_DISCOVERY_REPORT.md`
- `docs/migration2/MIGRATION2_PROJECT_CHARTER.md`
- `docs/migration2/MIGRATION2_ARCHITECTURE.md`
- `docs/migration2/MIGRATION2_ROADMAP.md`
- `docs/migration2/MIGRATION2_STATUS.md`

---

## Migration Principles

- Compatibility first: preserve current behavior until a replacement is explicitly approved.
- Single source of truth: one registry for paths, files, and environment definitions.
- Incremental change: migrate in small, reviewable steps.
- Reversible change: every structural change must have a rollback path.
- No silent relocation: file or path moves must be documented.
- Validation before cleanup: do not remove legacy locations until replacements are verified.
- Keep runtime separate from source: generated artifacts should not live beside code unless intentionally preserved as samples.

---

## Status

Complete

