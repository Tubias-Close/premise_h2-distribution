# Hydrogen-distribution LCIA example

## Configuration ownership

The LCIA workflow deliberately separates semantic mappings from operational
settings:

- `LCIA_mapping_h2.py` is the only canonical source for Brightway activity
  names, reporting names, scenario metadata, selected LCIA methods,
  contribution groups, and visual identities. Change method membership or a
  displayed process name there.
- `config.py` contains operational settings only: market-selection parameters,
  functional unit, reconciliation tolerance, output paths, filenames, and the
  generic accessibility palette used by the master notebook.
- `run_analysis.py` performs market selection, LCIA calculations, contribution
  analysis, and reconciliation. It imports all semantic classifications and
  method choices from `LCIA_mapping_h2.py`.
- `notebooks/lcia_stage_analysis.py` retains legacy calculation and plotting
  helpers for the European contribution notebook, but imports every semantic
  name and color family from `LCIA_mapping_h2.py`.

Both `LCIA_h2-distribution.ipynb` and the notebooks under `notebooks/` resolve
the shared modules through the `examples/h2-distribution_LCIA` directory. The
notebooks contain run controls such as the Brightway project, selected single
database, export switches, and plotting layout; they do not redefine methods or
activity mappings.

## Updating mappings

Keep the values emitted by `TRANSPORT_NAMES`, `CONVERSION_NAMES`, and
`RECONVERSION_NAMES` synchronized with the four route process sets. Unknown
direct market inputs and unknown distribution families raise errors instead of
falling back silently. The liquefied-hydrogen tanker is intentionally outside
the current LCIA mapping scope.

Production technologies use shades from the canonical `Greys` family. Route
families retain separate sequential palettes. Contribution charts also consume
`PROCESS_HATCH`: production is unhatched, distribution/conversion/reconversion
use their configured patterns, and direct hydrogen leakage explicitly uses the
existing `PROCESS_HATCH["Hydrogen leakage"]` pattern. This makes hydrogen
leakage distinguishable in both the hotspot and stage-analysis charts; no new
ammonia-leakage hatch is introduced.

After changing mappings or methods, restart the notebook kernel or reload the
module, rerun the calculation cells, and inspect the selection,
classification-audit, and reconciliation tables before interpreting plots.
