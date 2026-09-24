---
name: premise-development
description: Develop, debug, and review the premise Python package, including IAM mappings, sector transformations, inventory data, exports, and validation. Use for repository changes or technical questions that require premise-specific architecture and test knowledge; do not use merely to explain prospective LCA concepts.
---

# Premise Development

Work from the repository's current implementation and tests. Treat mappings,
inventory data, transformation code, validation, and export behavior as one
pipeline: a change in one layer can require coordinated changes in the others.

## Route the Work

Read [references/repository-guide.md](references/repository-guide.md) before
changing code or data. Use its routing table to locate the relevant extension
surface and tests. For a narrow question, inspect only the listed sections and
files that bear on the request.

Classify the request before editing:

- Sector behavior: start at the sector wrapper called by
  `NewDatabase.update()`, then inspect its transformation class or mixins,
  mappings, packaged data, validator, and corresponding tests.
- IAM variable support: trace the alias from `premise/iam_variables_mapping/`
  through `IAMDataCollection` into the consuming transformation. Preserve model
  distinctions and xarray dimension/coordinate names.
- Inventory support: trace the packaged inventory through
  `inventory_imports.py`, its mapping rules, transformation/relinking, and
  export. Do not treat an inventory file as an isolated asset.
- Export, Brightway, or datapackage behavior: identify the backend and output
  format before changing shared preparation logic.
- Bug diagnosis: reproduce with the smallest fixture that preserves the
  dataset, exchange, geography, and IAM-data shape involved.

## Preserve Domain Invariants

- A database is a list of activity dictionaries; technosphere, production,
  and biosphere exchanges remain structurally valid and use the package's
  existing field conventions.
- Keep the transformation index and cache synchronized when activities are
  created, removed, renamed, or relinked. Prefer `BaseTransformation` helpers
  over parallel matching or geography logic.
- Preserve production-volume allocation, exchange units, reference products,
  locations, uncertainty fields, and non-target exchanges unless the requested
  behavior explicitly changes them.
- Use IAM regions and years explicitly. Handle `World`, `GLO`, and `RoW` only
  according to existing sector behavior; do not assume they are interchangeable.
- Fail visibly when a required transformation prerequisite is absent. Do not
  emit a partially transformed scenario that looks complete.
- Put distributable static inputs below `premise/data/` or
  `premise/iam_variables_mapping/` in formats already included by
  `pyproject.toml`. Do not add generated caches, logs, licensed ecoinvent data,
  or local scenario files to the package.
- Maintain compatibility with Python 3.10+ and both supported Brightway
  generations unless the task narrows that compatibility.

## Implement and Verify

Follow nearby code style and Black's 88-character line length. Add or update
focused pytest coverage alongside every behavior change. Prefer lightweight
dict, pandas, and xarray fixtures; mark tests requiring ecoinvent or serialized
execution consistently with the existing suite.

Run the narrowest relevant tests first, then tests for shared layers touched by
the change. Use `pytest -m "not slow"` for the broader suite when dependencies
and runtime permit. Report skipped or unrun integration coverage, especially
when ecoinvent data, IAM files, Brightway, or optional dependencies are absent.

For scientific or allocation changes, assert meaningful invariants such as
market-share sums, non-negative amounts, energy or mass consistency, expected
regional coverage, absence of duplicate suppliers, and correct relinking—not
only that execution succeeds.
