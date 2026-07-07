# Next Session Prompt

You are continuing Migration 2 in the repository at:
`E:\Luxbaz\All Codes\Projects\product-import-pipeline`

## Project Context

Migration 2 standardized repository structure and asset organization without changing business logic. The canonical data, runtime, and asset layout is now established, the shared registry layer is active, and the migration is complete.

## Migration Objectives

- Keep source code separate from runtime artifacts.
- Keep data in canonical `data/` subfolders.
- Keep runtime output in canonical `runtime/` subfolders.
- Keep reusable templates and help assets in `assets/`.
- Preserve compatibility until validation proves legacy paths are safe to retire.

## Current Phase

Phase 8 - Finalization and Handoff complete.

## Current Status

- Phase 0 complete.
- Phase 1 complete.
- Phase 2 complete.
- Phase 3 complete.
- Phase 4 complete.
- Phase 5 complete.
- Phase 6 complete.
- Phase 7 complete.
- Phase 8 complete.

## Completed Work

- Shared registries implemented and wired into the main consumers.
- Shared mappings moved to `data/mappings/`.
- Pipeline spreadsheets moved to `data/inputs/`, `data/intermediate/`, and `data/outputs/`.
- Legacy color mapping archived in `data/archives/`.
- Runtime artifacts moved to `runtime/state/`, `runtime/cache/`, `runtime/logs/`, and `runtime/reports/`.
- Reusable templates moved to `assets/templates/`.
- Help assets moved to `assets/help/import_builder/`.
- Source-tree duplicates retired after verification.
- Generated caches and empty migration debris directories removed.
- Smoke tests for the migrated entry points passed.
- The dashboard generator regression that blocked default output generation was fixed.
- Alternate-working-directory regression checks passed.

## Pending Work

None.

## Open Decisions

None.

## Known Risks

- Historical documentation may still reference retired paths for context.
- Future runs can recreate caches unless ignored.

## Mandatory Documents To Review

- `docs/migration2/MIGRATION2_STATUS.md`
- `docs/migration2/MIGRATION2_ROADMAP.md`
- `docs/migration2/MIGRATION2_PHASE2_LAYOUT_MAP.md`
- `docs/migration2/MIGRATION2_DECISION_LOG.md`
- `docs/migration2/MIGRATION2_CONTINUATION_HANDOFF.md`
- `docs/migration2/SESSION_HANDOFF.md`

## Files Modified During Previous Session

- `docs/migration2/MIGRATION2_STATUS.md`
- `docs/migration2/MIGRATION2_ROADMAP.md`
- `docs/migration2/MIGRATION2_PHASE2_LAYOUT_MAP.md`
- `docs/migration2/MIGRATION2_CONTINUATION_HANDOFF.md`
- `docs/migration2/MIGRATION2_DECISION_LOG.md`
- `docs/migration2/SESSION_HANDOFF.md`
- `docs/migration2/NEXT_SESSION_PROMPT.md`

## Validation Status

- Passed: syntax parsing of the edited Python files.
- Passed: filesystem verification for canonical `data/`, `runtime/`, `assets/`, and `data/archives/` locations.
- Passed: removal verification for retired source-tree duplicates and empty migration debris directories.
- Passed: smoke tests for `product_extraction.main`, `DashboardGenerator`, `product_extraction.web_panel_interactive`, `import_builder.web_panel_v12`, and `image_processing.menu`.
- Passed: regression checks from an alternate working directory.

## Next Recommended Task

No further migration work is required.

## Stop Conditions

None.

## Migration Rules

- Do not change business logic.
- Do not change algorithm behavior.
- Do not delete legacy files unless the new location is verified.
- Prefer small, reviewable moves.
- Keep the repository functional after every step.
- Preserve compatibility until validation is complete.

These rules are retained for historical reference only.

## Short Prompt For The Next Model

Migration 2 is complete. No further migration actions are required.
