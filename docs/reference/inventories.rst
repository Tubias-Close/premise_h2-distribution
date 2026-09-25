Inventory catalogue and sources
=================================

After the ecoinvent database is extracted and checked, a number of additional inventories
are imported, regardless of the year of scenario that is being considered.

All inventories can be found in the `premise/data/additional_inventories <https://github.com/polca/premise/tree/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories>`__ folder.

Inventory sources by sector
-----------------------------

* :doc:`/methodology/electricity/photovoltaics` — IEA PVPS inventories,
  country electricity mixes and separate emerging-technology supplements.
* :doc:`/methodology/electricity/generation` — other electricity technologies.
* :doc:`/methodology/fuels/index` — hydrogen, ammonia, biofuels and synthetic fuels.
* :doc:`/methodology/metals` and :doc:`/methodology/mining` — material production
  and mining inventories.
* :doc:`/methodology/cement` and :doc:`/methodology/steel` — industrial processes.
* :doc:`/methodology/batteries` — mobile and stationary batteries.
* :doc:`/methodology/transport/index` — vehicle inventories.
* :doc:`/methodology/cdr` — carbon capture and removal routes.

Import conditions depend on the ecoinvent version and system model; see each
sector page. For example, the 2026 PV core replaces the legacy core only for
ecoinvent 3.12 cut-off. See :doc:`inventory-migration` for background linking
between versions and :doc:`/user_guide/external-scenarios` for custom inventories.

Constructor workbook selection
--------------------------------

This table is generated from the constructor's inventory-selection statements.
It records selection before activity-level filtering, migration and linking.
Selection does not guarantee that every activity survives those steps or is
used by a scenario. Workbook source version is distinct from target version.

.. include:: generated/inventory-selection.inc

Hydrogen transport in sector-specific markets
*********************************************

The general ``market for hydrogen, gaseous, low pressure`` keeps its existing
pipeline transport exchange. In addition, the sector-specific hydrogen markets
(``market for hydrogen, gaseous, low pressure, for ...``) receive hydrogen
transport exchanges according to the distribution-mode shares calculated during
the hydrogen logistics step.

The logistics step creates a demand-node table for the model, scenario, year,
region and end-use sector. Distribution-mode shares are assigned from
``premise/fuels/h2_decision_tree/hydrogen_distribution_shares.yaml`` and are
weighted by annual hydrogen demand when several demand-node rows feed the same
sector market.

Sector-specific markets are only created for sector-region combinations where
the in-memory IAM ``production_volumes`` xarray contains positive hydrogen
final-energy use for the target year, logistics are complete, and an
unambiguously classified final consumer exists. This is the same xarray source
used by the hydrogen demand-node analysis; no raw IAM output files are read
during market creation. If an IAM model does not represent a sector in a region,
the sector has zero hydrogen final-energy consumption there, or no consumer is
present, the corresponding
``market for hydrogen, gaseous, low pressure, for ...`` dataset is skipped for
that region. Consumers that would otherwise be classified to that unavailable
sector-region market remain linked to the general hydrogen market, so no
sector-specific hydrogen transport is allocated and the hydrogen production mix
stays the general one.

The distribution technologies are linked to the following activities already
present in the database after the additional inventories are imported:

 ====================================================================== ============================
  Distribution technology                                                Linked activity
 ====================================================================== ============================
  ``compressed_gaseous_truck``                                           ``transport, hydrogen, gaseous, lorry, unspecified``
  ``liquid_hydrogen_truck``                                              ``transport, hydrogen, liquid, lorry, unspecified``
  ``compressed_gaseous_pipeline``                                        ``hydrogen supply, distributed by pipeline``
  ``liquid_hydrogen_ship``                                               ``transport, freight, sea, tanker for liquefied hydrogen, heavy fuel oil``
  ``liquid_ammonia_ship``                                                ``transport, freight, sea, tanker for liquefied ammonia, ammonia and mdo``
 ====================================================================== ============================

The truck and ship activities come from ``lci-hydrogen-transport.xlsx`` during
the normal additional-inventory import. The market-building code does not read
the spreadsheet directly; it resolves the activities from the imported database.
The two truck activities are cloned to each non-World IAM region and the
original global activities are emptied into those proxies. Ship activities
remain global.

Gaseous-truck transport also adds the regionalized ``gaseous hydrogen
production`` conversion activity according to its distribution share. Liquid
hydrogen transport by truck or ship similarly adds both ``liquid hydrogen
production`` and ``liquid hydrogen regasification`` according to the combined
share of those modes. The conversion datasets and their technosphere inputs are
relinked to the corresponding IAM region before the sector-specific markets are
created. Generic hydrogen inputs used to replenish logistics or conversion
losses are normalized to the exact IAM-region generic market where available.
Regasification leakage receives an equal regional generic-market make-up input,
without duplication on rerun. Liquid-ammonia transport adds ``1 / 0.175`` kilograms of ``liquid
ammonia production`` and ``7.67`` kilograms of ``ammonia cracking`` per
kilogram of hydrogen assigned to that distribution mode. These auxiliary loss
and conversion inputs leave the one-kilogram hydrogen production-mix input to
each market unchanged.

See :ref:`sector-specific-hydrogen-markets` for the complete workflow from IAM
demand and demand-node estimation through the decision tree, market construction,
and consumer relinking.
