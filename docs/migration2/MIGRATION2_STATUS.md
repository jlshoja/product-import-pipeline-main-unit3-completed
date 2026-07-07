# Migration 2 Status

## Project

Repository Standardization and Asset Organization

---

## Current Phase

Phase 2 - Data Classification and Canonical Data Layout in progress; shared mapping move completed.

---

## Overall Status

Phase 1 foundation complete; Phase 2 layout mapping in progress and partially executed.

---

## Phase Progress

| Phase | Name | Status |
| --- | --- | --- |
| 0 | Discovery and Scope Confirmation | Complete |
| 1 | Shared Configuration and Path Design | Complete |
| 2 | Data Classification and Canonical Data Layout | In Progress |
| 3 | Runtime Layout Standardization | Pending |
| 4 | Asset Layout Standardization | Pending |
| 5 | Module Migration to Shared Registries | Pending |
| 6 | Legacy Cleanup and Consolidation | Pending |
| 7 | Validation and Regression Review | Pending |
| 8 | Finalization and Handoff | Pending |

---

## Completed Work

- Completed repository scan and inventory
- Identified scattered data, runtime artifacts, assets, and documentation
- Confirmed current module structure across `product_extraction/`, `import_builder/`, `image_processing/`, `data_standardization/`, and `baseline/`
- Identified current path and file management hotspots
- Drafted the target architecture
- Refined the roadmap based on actual repository findings
- Completed the project charter for Migration 2
- Implemented the shared path and file registries
- Wired the primary consumers to the shared registries
- Corrected repo-root resolution for the shared registry layer
- Added the Phase 2 canonical layout map
- Moved shared mapping spreadsheets into `data/mappings/`
- Added compatibility fallbacks for the remaining legacy mapping locations

---

## Pending Work

- Approve the Phase 2 canonical layout map
- Decide which module-local spreadsheets become shared mappings
- Confirm the canonical homes for runtime downloads and image-processing workspaces
- Plan the next physical file moves for runtime state and report artifacts
- Define the move order for runtime artifacts and reusable templates
- Decide when to retire the remaining legacy fallback copy of `product_extraction/color_mapping.xlsx`

---

## Known Risks

- Hardcoded filenames remain in multiple scripts
- Some workflows still depend on cwd-sensitive or legacy relative paths
- Mapping spreadsheets are duplicated across module folders
- Legacy versioned scripts may preserve outdated assumptions
- Runtime artifacts are still mixed into source trees

---

## Open Decisions

- Whether `shared/` becomes the canonical repository-wide config package or whether `product_extraction/common/` remains the migration anchor
- Whether `data_standardization/` becomes part of the canonical `data/reference/` hierarchy or remains a separate reference area
- Which module-local assets should remain module-specific and which should be promoted to shared asset storage
- Which legacy versioned scripts should remain as compatibility entry points

---

## Recommended Next Actions

1. Review and approve [Migration 2 Phase 2 Layout Map](./MIGRATION2_PHASE2_LAYOUT_MAP.md).
2. Confirm which mapping spreadsheets are truly shared versus module-private.
3. Approve the runtime split between `runtime/cache/` and `runtime/state/` for image workflows.
4. Decide whether `assets/templates/` or module-local templates are the long-term home for each UI template.
5. Choose the first low-risk runtime move once the target homes are locked.

---

## Repository Health Assessment

Overall health is functional but fragmented.

- Functionality appears present across all major workflows.
- Structural consistency is moderate at best.
- Path and file coupling is still high.
- Runtime artifact scattering is material.
- Long-term maintainability risk is moderate to high until a shared layout is enforced.

The repository is suitable for a phased migration, but it is not yet standardized.

---

## Last Updated

2026-07-07
