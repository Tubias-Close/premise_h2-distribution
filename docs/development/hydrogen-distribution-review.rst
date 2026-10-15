Hydrogen distribution: source review
====================================

This developer reference preserves the source checks performed on 13 October
2026 for the hydrogen distribution model. It identifies implementation
locations, workbook cells, incomplete derivations and follow-up work for
maintainers. The user-facing explanation is in
:ref:`hydrogen-distribution-references` and
:ref:`hydrogen-distribution-evidence-gaps`.

The review distinguishes the presence of a citation from verification of the
exact numerical value. Its findings do not change the model's defaults.

.. _hydrogen-distribution-review-references:

Hydrogen distribution assumptions and references
------------------------------------------------

The register below consolidates references previously recorded in Python
comments and workbook metadata for the sector-specific distribution model.
It complements the production and delivery references in the
:doc:`Hydrogen methodology </methodology/fuels/hydrogen>`. A reference
recorded beside a parameter establishes traceability; it does not
by itself demonstrate that the publication reports that exact value or
supports its use in every IAM region and year.

Unless stated otherwise, these are fixed defaults used across regions and
years. The demand-node parameters are defined in ``premise/fuels/hydrogen.py``
between ``STEEL_PLANT_SIZE_MT_PER_YEAR`` and ``FREIGHT_LOAD``. Distances are
defined in ``HYDROGEN_TRANSPORT_DISTANCES_KM``. The evidence notes distinguish
metadata transcribed from the repository from the source checks described
below; this is not a complete revalidation of every publication or supplement.

.. list-table:: Demand-node parameters and their recorded references
   :header-rows: 1
   :widths: 25 32 43

   * - Parameter and implemented value
     - Reference recorded in the code
     - Evidence and applicability
   * - Steel plant output: 0.5 Mt steel/year
     - `Lei et al. (2023), Global iron and steel plant CO2 emissions and
       carbon-neutrality pathways <https://doi.org/10.1038/s41586-023-06486-7>`__
     - Citation present. No table, selected plant population, or calculation
       deriving the representative 0.5 Mt/year value is recorded.
   * - Steel operation: 333 days/year
     - No adjacent citation in ``_add_steel_demand_nodes``.
     - Hard-coded operating assumption. The separate citation for 333 days
       in the ``Other`` category is not evidence for steel operation.
   * - Cement plant capacity: 2.4 Mt/year; capacity factor: 0.55
     - `Tkachenko et al. (2023), Global database of cement production assets
       and upstream suppliers <https://doi.org/10.1038/s41597-023-02599-w>`__
     - Citation present for both constants. The extraction, averaging method,
       and derivation of 0.55 are not recorded. The same factor is also used
       to calculate operating days as ``365 * 0.55``.
   * - Chemical plant demand: 60,300 t H2/year
     - `Fuel Cells and Hydrogen Observatory, Market report 2022, Chapter 2
       <https://observatory.clean-hydrogen.europa.eu/sites/default/files/2023-05/Chapter-2-FCHO-Market-2022-Final.pdf>`__
     - Report cited, but no page, plant count, demand total, or averaging
       calculation is recorded. Applying one value to all mapped chemical
       uses is a modelling assumption.
   * - Other industrial node demand: 1,000 t H2/year
     - `Zier et al., German glass industry
       <https://doi.org/10.1016/j.ecmx.2022.100336>`__; also
       `10.1016/j.gerr.2026.100174
       <https://doi.org/10.1016/j.gerr.2026.100174>`__ and
       `10.1016/j.fuel.2024.133576
       <https://doi.org/10.1016/j.fuel.2024.133576>`__.
     - The comment explicitly calls this a representative node for uses
       such as glass and pulp and paper. It does not identify which source
       supplies 1,000 t/year or how the value represents the full IAM
       residual ``Other`` category, which can also include carbon removal.
   * - Other industrial operation: 333 days/year
     - `Zier et al. <https://doi.org/10.1016/j.ecmx.2022.100336>`__
     - Citation present; source location and transfer beyond the studied
       industrial context are not documented.
   * - Passenger and freight annual distance: 10,900 and 23,900 km/vehicle/year
     - `ODYSSEE-MURE, transport sector report
       <https://www.odyssee-mure.eu/publications/efficiency-by-sector/transport/transport-eu.pdf>`__
     - The linked report concerns Europe. The code comment does not specify
       a report edition, page, observation year, or the freight vehicle
       population used to derive the value.
   * - Station throughput: 1,500 passenger cars/day; 400 freight vehicles/day
     - `Reuss et al. (2019), A hydrogen supply chain with spatial resolution:
       Comparative analysis of infrastructure technologies in Germany
       <https://doi.org/10.1016/j.apenergy.2019.04.064>`__
     - Citation present. The exact figures and their interpretation as
       vehicles/day, rather than hydrogen mass/day, still require a source
       table or explicit derivation. This register does not verify them.
   * - Passenger-car refuelling interval: 7 days
     - `Zaleski et al. (2014), European solvent industry group generic
       exposure scenario risk and exposure tool
       <https://doi.org/10.1038/jes.2012.128>`__, Table 5.
     - The source does contain a once-weekly default for conventional
       automotive refuelling in an exposure model. Its survey mean is
       3.1 times/month. Use for hydrogen vehicles is an additional proxy
       assumption, not an observation of hydrogen refuelling behaviour.
   * - Freight refuelling interval: 3.5 days
     - `US DOE, Hydrogen Class 8 Long Haul Truck Targets, Record 19006
       <https://www.hydrogen.energy.gov/docs/hydrogenprogramlibraries/pdfs/19006_hydrogen_class8_long_haul_truck_targets.pdf>`__
     - No derivation of 3.5 days is recorded. Sections 4.2 and 5.5 discuss
       once-daily refuelling for the maximum-range use case and less frequent
       fills for lower mileage; these statements do not establish a general
       3.5-day interval.
   * - Passenger occupancy: 1.5 people/vehicle
     - `Mobilitaet in Deutschland 2023, Ergebnisbericht
       <https://www.mobilitaet-in-deutschland.de/pdf/MiD2023_Ergebnisbericht.pdf>`__
     - German survey cited. The selected table and justification for applying
       this value to other regions and future years are not recorded.
   * - Freight load: 15 t/vehicle
     - `ICCT, EU heavy-duty vehicle fuel-efficiency technology assessment
       <http://theicct.org/EU-HDV-fuel-efficiency-tech-2020-2030>`__
     - Citation present. The selected vehicle class, loading convention and
       treatment of empty journeys need to accompany the value.
   * - Chemicals and transport operation: 365 days/year
     - Calendar convention in the implementation; no publication cited.
     - Used to express average daily demand, rather than a measured plant
       or station availability factor.

For chemicals and ``Other``, the node count is calculated as regional demand
divided by the assumed annual demand per node. Dividing demand by that
unrounded count therefore returns the assumed node demand. A citation for
plant size alone does not independently validate the resulting distribution
rule selection.

.. list-table:: Distribution distances and ammonia conversion factors
   :header-rows: 1
   :widths: 25 32 43

   * - Parameter and implemented value
     - Recorded source
     - Evidence and applicability
   * - Gaseous truck: 50 km; liquid-hydrogen truck: 100 km
     - `Parolin et al. (2024), Optimal design of hydrogen delivery
       infrastructure for multi-sector end uses at regional scale
       <https://doi.org/10.1016/j.ijhydene.2024.06.049>`__
     - Citation present beside both distances. No page, route-selection
       calculation, or basis for treating them as global defaults is given.
   * - Ammonia and liquid-hydrogen shipping: 2,500 km each
     - `Hampp et al. (2023), Import options for chemical energy carriers
       from renewable sources to Germany
       <https://doi.org/10.1371/journal.pone.0281380>`__
     - The source uses origin-specific distances to Germany (Table 2).
       The code does not record how 2,500 km was selected from that context.
       This default does not represent an explicit origin-destination route.
   * - Pipeline service: 250 km transmission plus 250 km distribution
     - Sacchi and Bauer (2023), *LCA of Power-to-X processes and applications
       in the residential sector*, Paul Scherrer Institut.
     - Recorded in ``lci-hydrogen-heating.xlsx``, sheet ``hydrogen boiler``,
       cells B5-B6. Distance is embedded in the service inventory, not the
       Python distance dictionary. The source field supplies no URL or page.
   * - Ammonia production factor: ``1 / 0.175``; cracking factor: ``7.67``
     - No adjacent citation for either Python constant.
     - The former uses an assumed hydrogen mass fraction of 0.175; the latter
       is repeated in the cracking electricity comment. The repository does
       not provide a common derivation reconciling the two service bases,
       recovery losses, and transported ammonia mass.

.. _hydrogen-distribution-review-inventory-sources:

Transport and conversion inventory sources
----------------------------------------------

The following source fields and exchange comments are in
``premise/data/additional_inventories/lci-hydrogen-transport.xlsx``. Cell
locations refer to sheet ``hydrogen-transport`` unless another sheet is named.
Values below are the stored inventory inputs; the source attribution is not
a claim that every exchange or adaptation has been checked against the paper.
The auxiliary conversion activities have reference unit ``unit``; the truck
and ammonia-ship transport activities have reference unit ``ton kilometer``.

.. list-table:: Inventory provenance and remaining qualifications
   :header-rows: 1
   :widths: 25 35 40

   * - Inventory or parameter
     - Source and workbook location
     - Interpretation and remaining qualification
   * - Hydrogen liquefaction: 10.5 kWh and 0.0162 kg H2 loss per service unit;
       liquefaction plant construction
     - B93 and B108 cite `Wei et al., supplementary Tables S21 and S22
       <https://doi.org/10.1016/j.resconrec.2025.108671>`__, attributing
       underlying data to Al Ghafri et al. and Wulf and Zapp.
     - Explicit supplementary-table references are available. Workbook
       metadata calls this Wei et al. (2025); the paper appeared online in
       2025 and in the 2026 journal volume. Electricity and loss inputs are
       in B103-B104.
   * - Compression to 250 bar: 1.25 kWh and 0.003 kg H2 loss per service unit
     - B139 cites Wei et al., Table S21. H149-H150 instead attribute the
       electricity and loss values to ecoinvent low-to-medium compression.
     - Dataset-level and exchange-level attribution differ. H148 identifies
       a pipeline compressor proxy and notes that its size may be too small
       for the required pressure. The ecoinvent activity identifier and
       adaptation should be specified.
   * - Regasification to 30 bar: ``0.88 + 0.47`` kWh and 0.005 kg H2 loss
       per service unit
     - B124 cites `Kolb et al. (2022), Renewable hydrogen imports for the
       German energy transition: A comparative life cycle assessment
       <https://doi.org/10.1016/j.jclepro.2022.133289>`__.
     - Electricity is recorded in B132 and leakage in B135. A publication
       table or calculation linking the individual values remains to be
       specified; H133 separately identifies a pipeline compressor proxy.
   * - Ammonia synthesis: 1.44 kWh per service unit; nitrogen and catalyst
       production
     - B171, B193 and B207 cite Wei et al., supplementary Tables S28, S29
       and S30, with underlying data attributed to D'Angelo et al.
     - Table-level attribution is present. The auxiliary synthesis service
       excludes the main hydrogen feed; the Python conversion factor and
       full supply-chain balance therefore need separate justification.
   * - Ammonia cracking: ``(3.086 / 7.67) + 0.6`` kWh per service unit
     - B157 cites the `Thyssenkrupp Uhde ammonia-cracking website
       <https://www.thyssenkrupp-uhde.com/en/ammonia-cracking>`__ for cracker
       and storage size. B167 and H167 contain the energy formula and comment.
     - The vendor reference is expressly for plant sizing. No specific
       publication or table is attached to the 7.67 kg NH3/kg H2, 3.086 kWh,
       or additional 0.6 kWh values. Their mass and energy bases need to be
       reconciled before treating the formula as validated.
   * - Gaseous- and liquid-hydrogen truck losses and tanks
     - B9 and B24 attribute loss assumptions to Reuss et al. (2019).
       I14 and I29 cite `Wulf et al. (2018), Journal of Cleaner Production
       199, 431-443 <https://www.sciencedirect.com/science/article/pii/S095965261832170X>`__
       for tank inputs.
     - Loss comments use percentages, whereas B15-B16 and B30-B31 contain
       0.005 and 0.01625 kg H2 per tkm. Their conversion from the quoted
       percentages and the route-distance basis are not documented.
   * - Ammonia shipping: 50,000 m3 tanker, stated 95% ammonia/5% marine fuel,
       and 0.25%/day boil-off with reliquefaction
     - B37-B38 identify an ecoinvent 3.12 LNG-tanker proxy with additional
       assumptions and cite ``IMO 2018``. Exchange comments G46 and G48-G50
       also name Spielmann et al. (2007), *Transport services*, ecoinvent
       Report 14, and ``IMO 2014`` / ``IMO 2015``.
     - The workbook explicitly retains unadapted LNG auxiliary processes.
       Exact IMO report titles/pages and the derivation of vessel, fuel and
       reliquefaction assumptions are incomplete.
   * - Ship-engine fuel use, emissions and urea
     - Sheet ``parameters``, column G: ``IMO 2018``, ``Sphera 2024``,
       ``Wei et al 2025``, and ``own calculations``.
     - For example, D10 specifies 5.9 g urea solution/kWh, D12-D13 specify
       0.2/0.5 g N2O/kWh, and D15-D16 specify 0.1/2 g NH3/kWh. The Sphera
       report title, version and pages are missing. The main-fuel mass,
       heating value and energy entries also require a consistent unit
       derivation; attribution alone does not resolve that check.

The pipeline service is documented separately in
``lci-hydrogen-heating.xlsx`` as described above. The existing storage and
refuelling infrastructure in ``lci-hydrogen-distribution.xlsx`` retains the
Wulf and Cerniauskas references in the storage-and-distribution section.
Those infrastructure sources do not establish the sector-specific mode
shares or the station-throughput constants used to count demand nodes.

.. _hydrogen-distribution-review-evidence-gaps:

Evidence gaps and interpretation limits
----------------------------------------------

The source register and targeted source checks were reviewed on 13 October
2026. The principal gaps are:

* **Uncited distribution rules.** The 1,000, 5,000 and 50,000 t/year
  thresholds, associated mode shares, the large-steel 70% pipeline/30%
  ammonia split, the 20% on-site remainder for other very large nodes, and
  the all-pipeline heating rule are provisional choices in
  ``hydrogen_distribution_shares.yaml``. No cited publication or calibration
  establishes these particular numbers.
* **Citations without reproducible derivations.** Plant sizes, chemical
  demand, station capacities and distances need a source page or table,
  original units, and any averaging or conversion calculation. An unverified
  extraction is not proof that the cited publication lacks the value.
* **Transfer beyond the source context.** European or German transport
  statistics, individual industrial case studies, and import routes to
  Germany are applied broadly. The seven-day passenger refuelling default
  can be located in the cited paper, but its use for hydrogen vehicles is a
  proxy. The cited DOE text does not establish the 3.5-day freight default.
* **Incomplete inventory provenance and physical bases.** Ammonia cracking
  factors lack a precise source; ship parameters include abbreviated reports
  and author calculations. Cargo mass, auxiliary service units, energy
  conversions and loss denominators need reconciliation. Publishing a
  citation does not resolve the associated mass- or energy-balance questions.
* **Insufficient justification of representativeness.** Fixed node demands
  and distances do not describe plant-size distributions or geographic
  routes. For chemicals and ``Other``, demand per node follows directly from
  the assumed node size. The consequences for rule selection should be
  assessed alongside the choice of that size.
* **Missing uncertainty evidence.** The register provides point defaults;
  it does not provide justified ranges or a sensitivity assessment covering
  node sizes, refuelling assumptions, mode shares and thresholds. A distance
  sensitivity alone cannot establish robustness to those other choices.

To close a gap, record the exact source location and calculation, its original
geographic and technological scope, and why it is applicable to the modelled
case. Where a value remains an author assumption, label it as such and provide
a rationale and sensitivity range. These qualifications describe the current
defaults; they do not change their numerical values or the executable method.
