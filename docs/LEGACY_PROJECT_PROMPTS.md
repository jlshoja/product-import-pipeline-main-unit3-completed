# Legacy Project Prompt Library

This document contains all prompts required to analyze, document, redesign and migrate a legacy project.

-------------------------------------------------------------------------------------------------------

# Phase 1 — Initialize Session

Use at the beginning of every new Claude session.

Prompt:

Read the following project documentation before performing any work:

Core Project Documents

* README.md
* CLAUDE.md
* docs/DOCUMENTATION_MAP.md
* docs/SESSION_HANDOFF.md

Project Analysis Documents

* docs/PROJECT_DISCOVERY.md
* docs/ARCHITECTURE.md
* docs/PIPELINE_INTEGRATION.md
* docs/DATA_FLOW.md
* docs/FILE_DEPENDENCIES.md
* docs/TECHNICAL_DEBT.md

Migration Documents

* docs/LEGACY_PROJECT_MIGRATION_GUIDE.md
* docs/LEGACY_PROJECT_WORKFLOW.md
* docs/MIGRATION_PLAN.md
* docs/MIGRATION_READINESS.md

Audit & Governance Documents

* docs/FINAL_AUDIT.md
* docs/CONFIG_INVENTORY.md

Then provide:

1. Current project phase
2. Current migration phase
3. Completed work
4. Remaining work
5. Active risks and blockers
6. Recommended next step
7. Recommended documentation updates (if any)

Rules:

* Do not modify code.
* Do not modify documentation.
* Do not make assumptions.
* Identify any missing documents referenced by DOCUMENTATION_MAP.md.
* Identify any inconsistencies between SESSION_HANDOFF.md and other documentation.
* If documentation appears outdated, list the files requiring review.
* Provide a concise executive summary followed by detailed findings.


--------------------------------------------------------------------------------------------------------------------

# Phase 2 — Analyze Product Extraction

Prompt:

Analyze only:

product_extraction/

Do not analyze other modules.

Identify:

* Responsibilities
* Inputs
* Outputs
* Generated files
* Dependencies
* External services

Update:

docs/PROJECT_DISCOVERY.md

If the session may end:

Update docs/SESSION_HANDOFF.md

------------------------------------------------------------------------------------------------------------------

# Phase 3 — Analyze Data Standardization

Prompt:

Analyze only:

data/reference/

Do not analyze other modules.

Identify:

* Responsibilities
* Inputs
* Outputs
* Generated files
* Dependencies

Update:

docs/PROJECT_DISCOVERY.md

If the session may end:

Update docs/SESSION_HANDOFF.md

---------------------------------------------------------------------------------------------------------------

# Phase 4 — Analyze Image Processing

Prompt:

Analyze only:

image_processing/

Do not analyze other modules.

Identify:

* Responsibilities
* Inputs
* Outputs
* Generated files
* Dependencies

Update:

docs/PROJECT_DISCOVERY.md

If the session may end:

Update docs/SESSION_HANDOFF.md

------------------------------------------------------------------------------------------------------------

# Phase 5 — Analyze Import Builder

Prompt:

Analyze only:

import_builder/

Do not analyze other modules.

Identify:

* Responsibilities
* Inputs
* Outputs
* Generated files
* Dependencies

Update:

docs/PROJECT_DISCOVERY.md

If the session may end:

Update docs/SESSION_HANDOFF.md

-----------------------------------------------------------------------------------------------------------

# Phase 6 — Module Integration Analysis

Prompt:

Read:

docs/PROJECT_DISCOVERY.md

Analyze relationships between modules.

Identify:

* Shared files
* Shared folders
* Data handoffs
* Upstream modules
* Downstream modules
* Integration points
* Hidden dependencies

Update:

docs/PIPELINE_INTEGRATION.md

If the session may end:

Update docs/SESSION_HANDOFF.md

-----------------------------------------------------------------------------------------------------------

# Phase 7 — Input / Output Mapping

Prompt:

Read:

docs/PROJECT_DISCOVERY.md

docs/PIPELINE_INTEGRATION.md

Create a complete data flow map.

Identify:

* Source files
* Intermediate files
* Output files
* Transformation steps

Update:

docs/DATA_FLOW.md

If the session may end:

Update docs/SESSION_HANDOFF.md

---------------------------------------------------------------------------------------------------------------

# Phase 8 — File Dependency Analysis

Prompt:

Analyze documented modules.

For every important file determine:

* Producer
* Consumer
* Modifier
* Dependency chain

Update:

docs/FILE_DEPENDENCIES.md

If the session may end:

Update docs/SESSION_HANDOFF.md

---------------------------------------------------------------------------------------------------------------

# Phase 9 — Hardcoded Paths Analysis

Prompt:

Search for:

* Hardcoded paths
* Hardcoded folders
* Hardcoded filenames
* Hardcoded configuration values

Update:

docs/FILE_DEPENDENCIES.md

docs/TECHNICAL_DEBT.md

If the session may end:

Update docs/SESSION_HANDOFF.md

-------------------------------------------------------------------------------------------------------------------

# Phase 10 — Architecture Analysis

Prompt:

Read:

docs/PROJECT_DISCOVERY.md

docs/PIPELINE_INTEGRATION.md

docs/DATA_FLOW.md

Create a high-level architecture analysis.

Identify:

* System boundaries
* Module relationships
* Architectural risks
* Coupling issues

Update:

docs/ARCHITECTURE.md

If the session may end:

Update docs/SESSION_HANDOFF.md

---------------------------------------------------------------------------------------------------------------------

# Phase 11 — Technical Debt Analysis

Prompt:

Analyze:

* Duplicate code
* Dead code
* Obsolete scripts
* Legacy structures
* Architectural weaknesses

Update:

docs/TECHNICAL_DEBT.md

If the session may end:

Update docs/SESSION_HANDOFF.md

-----------------------------------------------------------------------------------------------------------

# Phase 12 — Future Architecture Design

Prompt:

Based on:

docs/PROJECT_DISCOVERY.md

docs/PIPELINE_INTEGRATION.md

docs/ARCHITECTURE.md

docs/DATA_FLOW.md

docs/FILE_DEPENDENCIES.md

docs/TECHNICAL_DEBT.md

Design a future architecture.

Do not modify code.

Update:

docs/ARCHITECTURE.md

docs/MIGRATION_PLAN.md

If the session may end:

Update docs/SESSION_HANDOFF.md

-------------------------------------------------------------------------------------------------------------------------

# Phase 13 — Migration Plan

Prompt:

Create an incremental migration plan.

Requirements:

* Small steps
* Testable
* Reversible
* Low risk

Update:

docs/MIGRATION_PLAN.md

If the session may end:

Update docs/SESSION_HANDOFF.md

------------------------------------------------------------------------------------------------------------

# Phase 14 — GitIgnore Analysis

Prompt:

Identify:

* Generated files
* Temporary files
* Downloaded files
* Large files
* Cache files

Create a recommended .gitignore specification.

Do not modify code.

If the session may end:

Update docs/SESSION_HANDOFF.md

---------------------------------------------------------------------------------------------------------------------------

# Phase 15 — Final Audit

Prompt:

Review:

docs/PROJECT_DISCOVERY.md

docs/PIPELINE_INTEGRATION.md

docs/ARCHITECTURE.md

docs/DATA_FLOW.md

docs/FILE_DEPENDENCIES.md

docs/TECHNICAL_DEBT.md

docs/MIGRATION_PLAN.md

Identify:

* Missing information
* Contradictions
* Architectural risks
* Documentation gaps

Update existing documentation only.

Update docs/SESSION_HANDOFF.md

------------------------------------------------------------------------------------------------------------------------------

# Emergency Handoff Prompt

Use when the session is almost finished.

Prompt:

Create a detailed handoff summary.

Include:

* Current project phase
* Completed tasks
* Updated files
* Remaining tasks
* Open questions
* Risks
* Recommended next step

Update:

docs/SESSION_HANDOFF.md

Do not modify source code.

=======================================================================

Since you're following a structured migration process, here are the exact prompts you can use at each remaining phase.

---

# Phase 1 — Documentation Validation

Use this prompt:

# Phase 1 — Documentation Validation

Read:

* README.md
* CLAUDE.md
* docs/PROJECT_DISCOVERY.md
* docs/ARCHITECTURE.md
* docs/PIPELINE_INTEGRATION.md
* docs/DATA_FLOW.md
* docs/FILE_DEPENDENCIES.md
* docs/TECHNICAL_DEBT.md
* docs/MIGRATION_PLAN.md
* docs/MIGRATION_READINESS.md
* docs/CONFIG_INVENTORY.md
* docs/FINAL_AUDIT.md
* docs/SESSION_HANDOFF.md

Objective:

Validate documentation against the actual repository.

Tasks:

1. Identify outdated information.
2. Identify missing information.
3. Identify inconsistencies between documents.
4. Verify documented architecture matches code.
5. Verify documented data flow matches code.
6. Verify documented dependencies match code.
7. Verify migration plan assumptions remain valid.

Do not modify code.

Produce:

# Documentation Validation Report

For each document provide:

* Status: Accurate / Needs Update
* Findings
* Recommended Changes

Also provide:

* Documentation Gaps
* Cross-Document Inconsistencies
* Priority Updates
* Go/No-Go Recommendation for Phase 2

---

# Phase 2 — Configuration Inventory

Use this prompt:

# Phase 2 — Configuration Inventory

Analyze the entire repository.

Identify every:

* xlsx configuration file
* csv configuration file
* mapping file
* category file
* pricing file
* color file
* settings file
* hardcoded configuration value

Update:

docs/CONFIG_INVENTORY.md

For every configuration source document:

* Location
* Type
* Owning Module
* Consumers
* Purpose
* Migration Priority
* Risk Level

Do not modify application behavior.

Produce:

# Configuration Inventory Report

Include:

* Missing Configurations
* Duplicate Configurations
* High-Risk Configurations
* Recommended Consolidation Candidates

---

# Phase 3 — Central Configuration Design

Use this prompt:

# Phase 3 — Central Configuration Design

Read:

* docs/CONFIG_INVENTORY.md
* docs/ARCHITECTURE.md
* docs/MIGRATION_PLAN.md

Design a centralized configuration architecture.

Requirements:

* Backward compatible
* Incremental migration
* Reversible
* Low risk

Produce:

# Central Configuration Design

Include:

* Proposed Structure
* Directory Layout
* Migration Sequence
* Rollback Strategy
* Risks
* Required Code Changes

Do not implement.

---

# Phase 4 — Hardcoded Path Inventory

Use this prompt:

# Phase 4 — Hardcoded Path Inventory

Analyze all source code.

Identify:

* Hardcoded paths
* Hardcoded folders
* Hardcoded filenames
* Environment assumptions

Produce:

# Hardcoded Path Inventory

For each finding:

* File
* Line
* Current Value
* Usage
* Migration Risk
* Recommended Replacement

Do not modify code.

---

# Phase 5 — Shared Utility Inventory

Use this prompt:

# Phase 5 — Shared Utility Inventory

Analyze the repository.

Identify:

* Duplicate functions
* Duplicate logic
* Reusable helpers
* Common file operations
* Common Excel operations
* Common image operations

Produce:

# Shared Utility Inventory

For each candidate:

* Location
* Usage Count
* Dependencies
* Migration Complexity
* Consolidation Recommendation

Do not modify code.

---

# Phase 6 — Migration Implementation Planning

Use this prompt:

# Phase 6 — Migration Implementation Planning

Read:

* docs/MIGRATION_PLAN.md
* docs/CONFIG_INVENTORY.md
* docs/TECHNICAL_DEBT.md
* docs/ARCHITECTURE.md

Create a detailed implementation sequence.

Requirements:

* Small steps
* Testable steps
* Reversible steps
* Low-risk execution

For each step include:

* Objective
* Files Affected
* Validation Method
* Rollback Method
* Dependencies

Produce:

# Detailed Migration Execution Plan

---

# Before Every New Chat

To continue safely in a fresh chat, use:

Read before performing any work:

Core Documents

* README.md
* CLAUDE.md
* docs/DOCUMENTATION_MAP.md
* docs/SESSION_HANDOFF.md

Analysis Documents

* docs/PROJECT_DISCOVERY.md
* docs/ARCHITECTURE.md
* docs/PIPELINE_INTEGRATION.md
* docs/DATA_FLOW.md
* docs/FILE_DEPENDENCIES.md
* docs/TECHNICAL_DEBT.md

Migration Documents

* docs/MIGRATION_PLAN.md
* docs/MIGRATION_READINESS.md
* docs/CONFIG_INVENTORY.md

Audit Documents

* docs/FINAL_AUDIT.md

Then provide:

1. Current project phase
2. Current migration phase
3. Completed work
4. Remaining work
5. Active risks
6. Recommended next step

Do not modify code unless explicitly instructed.

These prompts will take you from the end of **Phase 0 (Migration Readiness)** through planning and into implementation preparation in a controlled, low-risk way.


=========================================================

git commit -m "baseline established"
git commit -m "phase 1 documentation validation"
git commit -m "phase 2 configuration inventory"
git commit -m "phase 3 config migration"
