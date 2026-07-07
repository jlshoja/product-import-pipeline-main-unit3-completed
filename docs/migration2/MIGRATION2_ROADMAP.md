# Migration 2 Roadmap

## Project Goal

Standardize repository structure and project assets while preserving existing functionality.

---

## Roadmap Summary

The original roadmap is still directionally correct, but the discovery findings indicate a different order of operations:

- configuration and path strategy must be defined before data or runtime moves
- documentation is part of discovery, not a separate implementation stream
- asset organization should be separated from data layout because images, templates, and help files have different lifecycles
- validation should remain the final gate before cleanup

The revised roadmap below reflects that order.

---

## Phase 0 - Discovery and Scope Confirmation

Status: Complete

Objectives:

- inventory the repository
- identify scattered data, runtime artifacts, assets, and docs
- document the target architecture
- document migration risks and open decisions

Why this phase exists:

- the repository already contains enough evidence to define the target structure
- later migration work should not begin until the current layout is documented

---

## Phase 1 - Shared Configuration and Path Design

Status: Complete

Objectives:

- define the canonical repository root resolution strategy
- define the shared file registry
- define the shared path registry
- define compatibility expectations for legacy modules

Why this phase is now earlier than the original roadmap:

- the discovery findings show that almost every major migration risk is path or filename related
- data and runtime moves should not happen before a shared registry exists

---

## Phase 2 - Data Classification and Canonical Data Layout

Status: Complete

Objectives:

- classify inputs, intermediates, outputs, mappings, archives, and reference datasets
- decide where each current spreadsheet belongs in the target layout
- identify duplicate or overlapping mapping files

Why this phase matters:

- the repository currently stores data in `product_extraction/`, `import_builder/`, `data_standardization/`, and `baseline/`
- classification prevents accidental moves of files that are actually reference material

Current progress:

- canonical layout defined in `MIGRATION2_PHASE2_LAYOUT_MAP.md`
- shared mapping spreadsheets moved into `data/mappings/`
- pipeline spreadsheets moved into `data/inputs/`, `data/intermediate/`, and `data/outputs/`
- legacy color mapping fallback archived under `data/archives/`

---

## Phase 3 - Runtime Layout Standardization

Status: Complete

Objectives:

- consolidate logs into the target runtime log directory
- consolidate generated reports into the target runtime report directory
- consolidate checkpoints and progress files into the target runtime state directory
- separate generated artifacts from source files

Why this phase matters:

- runtime artifacts are currently mixed into source trees
- this is one of the highest-value structural improvements with the lowest conceptual risk

---

## Phase 4 - Asset Layout Standardization

Status: Complete

Objectives:

- standardize image asset locations
- standardize template locations
- standardize help and support asset locations
- decide which assets are canonical and which are examples

Why this phase matters:

- image workflows, templates, and help files have different lifecycles from pipeline data
- grouping them too early with data would blur their purpose

---

## Phase 5 - Module Migration to Shared Registries

Status: Complete

Objectives:

- update modules to consume the shared registries
- remove cwd-dependent path assumptions
- replace duplicated filename literals with registry lookups
- preserve compatibility with temporary adapters where needed

Why this phase comes after the registry design:

- module updates should follow the approved registry model instead of defining their own local layout

---

## Phase 6 - Legacy Cleanup and Consolidation

Status: Complete

Objectives:

- retire duplicate configuration where it is no longer needed
- retire duplicate mapping sources where approved
- remove obsolete compatibility layers only after validation

Why this phase was deferred:

- cleanup before verification would increase the chance of breakage
- some legacy scripts may still be used as operational entry points

---

## Phase 7 - Validation and Regression Review

Status: Complete

Objectives:

- confirm all entry points still work
- confirm file and path resolution is stable from different execution contexts
- confirm report generation and artifact creation still work
- confirm legacy compatibility paths can be removed or archived safely

Why this phase was final:

- structural migration should not be considered complete until the repository still behaves as expected

---

## Phase 8 - Finalization and Handoff

Status: Complete

Objectives:

- finalize repository standards
- finalize the migration summary
- record any remaining exceptions as explicit legacy decisions
- prepare the implementation handoff

Why this phase remained last:

- finalization should only happen after validation proves that the target structure is stable

---

## Justification for Roadmap Changes

The original roadmap used separate phases for documentation organization, configuration centralization, data layout, runtime layout, asset organization, path refactoring, validation, and finalization.

Discovery findings support a more dependency-aware order:

- documentation work belongs in discovery because it is part of understanding the current state
- configuration and path work must happen first because every other phase depends on it
- data and runtime layout can then be standardized safely
- asset standardization can follow once the core workspace structure is known
- validation should remain the final gate

This ordering reduces migration risk and avoids rework.

---

## Status

Complete
