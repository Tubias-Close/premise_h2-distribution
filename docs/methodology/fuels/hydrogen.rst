Hydrogen
========

This chapter explains how Premise adapts hydrogen production and represents
delivery to different end uses. It follows the calculation from production
efficiency and regional demand to delivery choices, markets and consumer
links. Assumptions, worked examples and supporting sources follow the method.

.. contents:: On this page
   :local:
   :depth: 1

.. _key-outputs:

Scope and outputs
-----------------

Within the ``fuels`` update, Premise regionalizes hydrogen production and
builds markets supplying one kilogram of gaseous, low-pressure hydrogen.
Each market combines a production mix with delivery and conditioning services.
Sector markets distinguish transport, chemicals, steel, cement, heating and
other end uses where the scenario and consuming activities support them.

.. figure:: /_static/process-diagrams/fuels-hydrogen.svg
   :class: process-diagram
   :alt: Hydrogen update: estimate demand and delivery shares; prepare regional production and delivery activities; build general and eligible sector markets; link consumers and check the supply chain.
   :align: center

   Overview of the hydrogen update workflow.

.. _hydrogen-supply-chains:

Supply-chain overview
~~~~~~~~~~~~~~~~~~~~~

Production, delivery and conditioning are represented by separate activities
linked through a hydrogen market. Each kilogram of market output receives one
kilogram from the production mix, together with the required delivery services.
Those services include energy use, infrastructure and make-up hydrogen for
losses. A delivered-hydrogen result therefore includes more than production at
the plant gate.

The general market uses pipeline delivery. Sector markets can combine
pipeline, truck, ship and on-site supply. Their delivery shares depend on
regional demand and the assumed scale of individual consumers. The
:ref:`market construction <sector-specific-hydrogen-markets>` and
:ref:`delivery inputs <hydrogen-market-delivery-inputs>` sections explain how
these choices enter the inventory.

Inputs and applicability
------------------------

The hydrogen update uses three kinds of input:

* **IAM scenario data:** hydrogen production volumes, mapped efficiency
  changes, direct-hydrogen final-energy demand, and production or transport
  activity used to estimate consumer numbers.
* **Life-cycle inventories:** hydrogen production, transport, storage and
  conversion activities that provide the underlying materials and energy
  requirements.
* **Additional assumptions:** an external electrolysis efficiency trajectory,
  representative plant and station sizes, distribution shares and delivery
  distances. Their sources are documented under :ref:`hydrogen-production`
  and :ref:`hydrogen-distribution-references`.

The hydrogen entries in ``fuels.yaml`` connect production inventories to IAM
series. The hydrogen efficiency parameters select the feedstock exchanges to
adjust and provide the external electrolysis assumptions.

Use ``ndb.update("fuels")`` after upstream energy updates. The fuels update
runs when at least one petrol, diesel, natural-gas or hydrogen blend array is
available. Creation of a sector-specific hydrogen market additionally requires
usable sector demand and an eligible consumer, as described below.

Transformation
--------------

Production adjustments determine the burden of making hydrogen. The demand
and distribution calculations determine how it is delivered. The following
steps describe these two parts before they are combined into markets.

.. contents:: Calculation steps
   :local:
   :depth: 1
   :backlinks: none

.. _hydrogen-production-efficiency:

Production and efficiency
~~~~~~~~~~~~~~~~~~~~~~~~~

For a mapped IAM efficiency signal, the selected feedstock exchanges are
multiplied by the inverse efficiency change. Selection uses the configured
name substring and unit; other inputs are not automatically scaled.
Without an IAM signal, electrolysis uses the external electricity-requirement
trajectory. Other pathways keep their feedstock amount in this adjustment.
The :ref:`energy-floor limitation <implementation-limitation-energy-floors>`
qualifies the IAM branch.

.. _direct-hydrogen-demand:

Regional hydrogen demand
~~~~~~~~~~~~~~~~~~~~~~~~

Sector-specific hydrogen markets are considered only in IAM regions with
positive direct-hydrogen final-energy demand. Direct hydrogen is identified
from the normalized ``final_energy.yaml`` coordinates whose names end in
``- H2`` or ``- Hydrogen``. These coordinates are available in the normalized
``production_volumes`` xarray and are already expressed in EJ/year; no further
PJ-to-EJ conversion is applied. Annual hydrogen mass demand is calculated as:

.. math::

   Q_{H_2}\ [\mathrm{t/yr}] =
   FE_{H_2}\ [\mathrm{EJ/yr}] \times \frac{10^9}{120}

where 120 GJ/t is the lower heating value of hydrogen.

Hydrogen logistics and sector-market availability both select the database
target year. If it is not an explicit IAM coordinate, values are interpolated
between IAM years or clamped to the nearest boundary year. The IAM ``World``
aggregate is temporarily retained to compare the global value with the sum of
the regional values. It is then removed from the demand-node table and from
sector-market creation. Automatic creation of a ``World`` market is disabled;
global totals must therefore be calculated from the regional rows without
adding the IAM aggregate.

Differences between IAMs
^^^^^^^^^^^^^^^^^^^^^^^^

Steel, cement, and chemicals use model-specific coordinate hierarchies.
Candidate groups are ordered by preference, and only the first group represented
in the normalized IAM data is used. All candidates, including unused fallback
groups, are reserved from the ``Other`` category. This prevents aggregate and
detailed coordinates from being counted together. Custom IAM integrations
without an explicit rule retain structural grouping based on their normalized
coordinate names.

.. list-table:: Model-specific direct-hydrogen mapping
   :header-rows: 1
   :widths: 15 29 23 33

   * - IAM
     - Steel
     - Cement
     - Chemicals
   * - REMIND / REMIND-EU
     - All-steel aggregate
     - Cement aggregate
     - Chemicals aggregate
   * - IMAGE
     - All-steel aggregate; steel-route detail is the fallback
     - Cement aggregate
     - Fertilizer
   * - MESSAGE
     - All-steel hydrogen demand; preprocessed H-DRI production supplies the
       plant-count proxy
     - Cement aggregate
     - Resins, high-value chemicals, and methanol
   * - GCAM
     - BF/BOF plus DRI-EAF route detail
     - Cement aggregate
     - Chemicals aggregate
   * - TIAM-UCL
     - Derived H-DRI/EAF hydrogen demand from preprocessed production
     - Not currently mapped
     - Not currently mapped

Transport combines all mapped direct-hydrogen transport coordinates. All
mapped building coordinates are summed into one ``Heating`` subsector. Carbon
dioxide removal and all other remaining mapped direct-hydrogen coordinates are
assigned to ``Other``. For IMAGE,
``Industry - Non-Metallic Minerals - H2`` includes cement, so the amount
assigned to ``Other`` is calculated as non-metallic minerals minus the
already-assigned cement demand, clipped at zero.

.. note::

   Raw MESSAGE exports report finished DRI/EAF steel only as
   ``Production|Iron and Steel|Steel|Primary|EAF|Sponge Iron`` while reporting
   hydrogen-, gas-, and gas-with-CCS sponge-iron production separately. The
   MESSAGE preprocessing workflow converts the sponge-iron routes to finished
   steel with the model's annual World finished-DRI-to-sponge-iron ratio. It
   writes mutually exclusive ``H-DRI/EAF`` and ``NG-DRI/EAF + CCS`` series and
   assigns the remaining finished DRI/EAF production to ``NG-DRI/EAF``. The
   three derived routes close exactly to the original aggregate in every
   region and year, so the aggregate is retained only for auditing and is not
   mapped a second time by premise. The NG-DRI residual acts as the available
   non-H2/non-CCS DRI inventory proxy; it also contains MESSAGE's
   coal-without-CCS sponge-iron remainder because premise has no separate
   coal-DRI inventory category.

   MESSAGE does not report route-specific final energy for this split.
   Therefore premise keeps the baseline inventory efficiencies for all three
   routes instead of assigning aggregate DRI/EAF energy use to the residual
   NG-DRI route. Direct steel hydrogen demand continues to come from
   ``Final Energy|Industry|Iron and Steel|Hydrogen``.

.. note::

   Raw TIAM-UCL exports contain ``Production|Steel|Secondary|DRH2 and EAF`` in
   Mt steel/year but omit the corresponding hydrogen final-energy series. The
   TIAM-UCL preprocessing workflow derives
   ``Final Energy|Production|Steel|Secondary|DRH2 and EAF|Hydrogen`` with an
   explicit 66.52317888 kg H2/t-steel default intensity, equivalent to
   7.9827814656 PJ H2/Mt steel at the 120 GJ/t hydrogen lower heating value.
   This default follows the premise H2-DRI/EAF inventory: 1.061992 kg H2-DRI
   pig iron/kg steel multiplied by 0.06264 kg H2/kg H2-DRI pig iron.

   The processing report identifies this coordinate as an inventory-aligned
   derived proxy, not an original TIAM-UCL observation, and records any
   user-supplied intensity override. Premise uses it for steel hydrogen demand
   and distribution while retaining reported H-DRI/EAF production as the
   steel-plant-count proxy. This gives 66,523.17888 t H2/year and two assumed
   0.5 Mt/year plants per Mt of regional H-DRI/EAF production.

.. _demand-node-creation:

Demand per plant or refuelling station
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each positive regional demand row is assigned a demand-node type. The node
count represents the number of plants, refuelling stations, or generic demand
sites over which regional hydrogen demand is distributed.

.. list-table:: Demand-node assumptions
   :header-rows: 1
   :widths: 18 20 42 20

   * - End use
     - Node type
     - Node-count calculation
     - Operating days
   * - Steel
     - ``steel_plants``
     - IAM ``steel - primary - H-DRI`` production divided by 0.5 Mt
       steel/year per plant
     - 333 days/year
   * - Cement
     - ``cement_plants``
     - Sum of IAM variables beginning with ``cement,`` divided by
       2.4 Mt cement/year and a capacity factor of 0.55
     - ``365 * 0.55`` days/year
   * - Chemicals
     - ``chemical_plants``
     - Regional hydrogen demand divided by 60,300 t H2/year per plant
     - 365 days/year
   * - Other industrial uses
     - ``other_demand_nodes``
     - Regional hydrogen demand divided by 1,000 t H2/year per node
     - 333 days/year
   * - Transport
     - ``fueling_stations``
     - Passenger-car and road-freight service is converted to vehicle counts,
       daily refuellings, and finally station counts
     - 365 days/year
   * - Heating
     - No physical node proxy
     - The unconditional heating rule assigns pipeline distribution without
       requiring a per-node demand value
     - Not applicable

For transport, passenger-car service is divided by an occupancy of 1.5 and
10,900 km/vehicle/year. Each vehicle refuels every seven days, and a station
serves 1,500 vehicles/day. Road-freight service is divided by a 15 t load and
23,900 km/vehicle/year. Each freight vehicle refuels every 3.5 days, and a
station serves 400 vehicles/day. Passenger and freight stations are summed by
region and year.

See :ref:`hydrogen-distribution-references` for the literature behind these
assumptions and their applicability to different consumers and regions.

The calculated node count can be fractional. ``demand_nodes_rounded_up`` stores
its ceiling for reporting, but demand per node is calculated with the
unrounded value. The demand-node table also records annual and daily hydrogen
demand per node, source IAM variables, the calculation method, and the result
of the regional-versus-``World`` validation.

.. _hydrogen-distribution-rules:

Distribution decision tree
~~~~~~~~~~~~~~~~~~~~~~~~~~

The rules in
``premise/fuels/h2_decision_tree/hydrogen_distribution_shares.yaml`` are
evaluated for every demand row. A rule first matches exact row attributes such
as sector or node type, then evaluates its numeric ``basis``. Bounds use
``min_demand <= value < max_demand``. If several rules match, the lowest
numeric priority wins.

.. figure:: /_static/process-diagrams/hydrogen-distribution-decision-tree.svg
   :alt: Hydrogen distribution decision tree: heating uses pipeline delivery; large steel plants use pipeline and ammonia shipping; remaining rows follow annual demand-per-node thresholds, with missing estimates excluded.
   :align: center

   Current default distribution rules, evaluated for each regional demand row.
   Follow the first matching branch; demand thresholds are in tonnes of hydrogen
   per node per year. The heating rule applies even without a node estimate.
   Market creation additionally requires positive IAM demand and an eligible
   final consumer.

The current rules use annual hydrogen demand per node as their basis:

.. list-table:: Current hydrogen-distribution rules
   :header-rows: 1
   :widths: 20 19 43 18

   * - Match
     - Demand per node
     - Distribution shares
     - On-site share
   * - Heating
     - Any value
     - 100% compressed gaseous pipeline
     - 0%
   * - Steel plant
     - At least 50,000 t/year
     - 70% compressed gaseous pipeline, 30% liquid ammonia by ship
     - 0%
   * - Any node
     - 0 to <1,000 t/year
     - 80% compressed gaseous truck, 20% liquid hydrogen truck
     - 0%
   * - Any node
     - 1,000 to <5,000 t/year
     - 25% compressed gaseous truck, 25% liquid hydrogen truck,
       50% compressed gaseous pipeline
     - 0%
   * - Any node
     - 5,000 to <50,000 t/year
     - 20% liquid hydrogen truck, 80% compressed gaseous pipeline
     - 0%
   * - Any node
     - At least 50,000 t/year
     - 80% compressed gaseous pipeline
     - 20%

Transport shares plus an explicitly configured on-site share must sum to one.
Unknown modes, non-numeric shares, shares outside the interval from zero to one,
or an incomplete total raise an error. A finite positive per-node demand that
does not match a rule also raises an error. Rows without a usable node estimate
remain marked ``missing_demand_nodes`` and do not make a sector-region market
eligible, except where an unconditional rule such as the heating rule supplies
a complete distribution result.

.. warning::

   These shares and thresholds are provisional modelling assumptions.
   They do not represent observed distribution networks or IAM forecasts.
   No published calibration establishes these particular values;
   see :ref:`hydrogen-distribution-evidence-gaps`.

Markets and downstream links
----------------------------

Markets combine the production mix with the delivery services calculated
above. Production suppliers follow the mapped production volumes and the
common :doc:`system-model weighting <markets>`. General and sector-specific
markets differ in their delivery inputs and the consumers they serve.

.. contents:: Market construction and use
   :local:
   :depth: 1
   :backlinks: none

General hydrogen market
~~~~~~~~~~~~~~~~~~~~~~~

The general supply dataset is ``market for hydrogen, gaseous, low pressure``,
with reference product ``hydrogen, gaseous, low pressure`` and unit
``kilogram``. It adds one kilogram of the regional
``hydrogen supply, distributed by pipeline`` service per kilogram of market
output.

Consumers use this general market when the routing rules retain it or when a
suitable sector market is unavailable. Shared delivery and conversion
activities also use general markets for their make-up hydrogen.

.. _sector-specific-hydrogen-markets:

.. _sector-market-creation-and-transport-shares:

Sector-specific hydrogen markets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The transformation can create the following markets, each supplying one
kilogram of low-pressure gaseous hydrogen:

.. list-table:: Hydrogen end-use markets
   :header-rows: 1
   :widths: 20 80

   * - End use
     - Dataset name
   * - Transport
     - ``market for hydrogen, gaseous, low pressure, for transport``
   * - Chemicals
     - ``market for hydrogen, gaseous, low pressure, for chemicals``
   * - Steel
     - ``market for hydrogen, gaseous, low pressure, for steel``
   * - Cement
     - ``market for hydrogen, gaseous, low pressure, for cement``
   * - Heating
     - ``market for hydrogen, gaseous, low pressure, for heating``
   * - Other
     - ``market for hydrogen, gaseous, low pressure, for other end uses``

A sector-region is IAM/logistics-eligible only when it has positive
direct-hydrogen demand and at least one matching demand row with
``distribution_status = ok``. Steel and cement consequently also require their
plant-production proxies to produce valid logistics. A market is created only
for the intersection of those eligible regions and regions containing at least
one unambiguously classified final hydrogen consumer. Eligibility,
consumer-backing, successful construction, regions excluded for lack of a
consumer, and desired markets that could not be created are tracked separately.
Markets that lose their last consumer are removed during synchronization.

.. _hydrogen-market-delivery-inputs:

Delivery inputs and losses
~~~~~~~~~~~~~~~~~~~~~~~~~~

When several demand rows contribute to the same sector-region market, the share
of distribution mode :math:`m` is weighted by annual hydrogen demand:

.. math::

   s_m = \frac{\sum_i Q_i s_{i,m}}{\sum_i Q_i}

The weighted shares are converted to technosphere exchanges as follows:

.. list-table:: Distribution exchanges per kilogram of market output
   :header-rows: 1
   :widths: 20 35 20 25

   * - Mode
     - Transport activity
     - Exchange amount
     - Conversion activities
   * - Compressed gas by truck
     - ``transport, hydrogen, gaseous, lorry, unspecified``
     - ``share * 50 * 0.001`` tkm
     - ``share`` units of gaseous hydrogen production
   * - Liquid hydrogen by truck
     - ``transport, hydrogen, liquid, lorry, unspecified``
     - ``share * 100 * 0.001`` tkm
     - ``share`` units each of liquefaction and regasification
   * - Compressed gas by pipeline
     - ``hydrogen supply, distributed by pipeline``
     - ``share`` kg
     - None
   * - Liquid ammonia by ship
     - ``transport, freight, sea, tanker for liquefied ammonia, ammonia and
       mdo``
     - ``share * 2500 * 0.001`` tkm
     - ``share / 0.175`` units of ammonia production and ``share * 7.67``
       units of ammonia cracking
   * - Liquid hydrogen by ship
     - ``transport, freight, sea, tanker for liquefied hydrogen, heavy fuel
       oil``
     - ``share * 2500 * 0.001`` tkm
     - ``share`` units each of liquefaction and regasification

Conversion inputs are measured in service units and account for processing
the hydrogen or its carrier. They do not add hydrogen to the production mix.
For ammonia delivery, the relationship between transported mass, processing
requirements and hydrogen recovery remains unresolved; see
:ref:`hydrogen-distribution-evidence-gaps`. The distance assumptions and
process references are explained in :ref:`hydrogen-distribution-references`
and :ref:`hydrogen-distribution-inventory-sources`.

Liquid-hydrogen conversion amounts are based on the combined truck and ship
share. The on-site portion receives no transport or conversion exchange; it is
the explicitly documented remainder of the market's hydrogen supply. Transport
and conversion suppliers are selected first in the IAM region, then in mapped
ecoinvent locations, ``RoW``, and ``GLO``. If none of those locations is
available, the first matching supplier is used. The compressed-gas and liquid-
hydrogen truck inventories are regionalized to the non-World IAM regions before
this selection, while the ship inventories remain global.

Hydrogen lost in logistics and conversion is replenished inside those support
inventories through the geographically appropriate generic hydrogen market,
never through a sector market. In particular, positive hydrogen leakage from
regional regasification receives an equal make-up input; rerunning the operation
adds only any remaining deficit. These loss inputs do not change the market
invariant: production-mix suppliers still provide exactly one kilogram of
hydrogen per kilogram of generic or sector-market output.

.. _customer-relinking:

Linking hydrogen consumers
~~~~~~~~~~~~~~~~~~~~~~~~~~

After sector markets have been created, the transformation inspects activities
with a technosphere input to either the generic or an already sector-specific
low-pressure gaseous hydrogen market.
Generated hydrogen suppliers and sector markets are not candidates for
relinking. Shared transport and conversion activities are also kept
sector-neutral to prevent circular or cross-sector supply chains.

Routing is configured in
``premise/fuels/h2_decision_tree/hydrogen_consumer_routing.yaml``. Rules that
keep an activity on the general market are evaluated first. These cover
synthetic-fuel and syngas contexts, methanation, RWGS, selected methanol
synthesis and distillation activities, and electricity supply classified as
ISIC 3510.
Remaining consumers are matched by activity name before ISIC classification:

.. list-table:: Consumer-routing summary
   :header-rows: 1
   :widths: 18 44 38

   * - Target market
     - Name context
     - ISIC rev.4 ecoinvent classification
   * - Transport
     - Transport, stations, fuel-cell vehicles, and hydrogen vehicle use
     - Prefixes 49, 50, 51, and 52
   * - Chemicals
     - Chemicals, ammonia, methanol, chlor-alkali, and configured chemical
       processes
     - 2011--2013, 2021--2023, 2029, and 2030
   * - Steel
     - Steel, direct-reduced iron, and sponge iron
     - Prefix 241
   * - Cement
     - Cement and clinker
     - 2394 and 2395
   * - Heating
     - Heat production, boilers, and furnaces
     - 3530
   * - Other
     - No name-based catch-all
     - Prefix 17; prefix 23 except 2394/2395; prefix 24 except 241

Name matching is intentionally evaluated before ISIC matching. This allows
hydrogen vehicle-use activities classified as heat/ISIC 3530 to be routed to
transport from their activity context. ``Other`` is deliberately narrow and is
not a fallback for every unmatched activity.

A consumer is relinked only when exactly one sector matches and the
corresponding sector market was actually created for the activity location or
its mapped IAM region. Existing links to the wrong sector or IAM region are
corrected. Ambiguous, unclassified, configured general-market, synthetic-fuel,
and shared logistics consumers are restored to the geographically appropriate
generic market, as are consumers whose target sector market is unavailable.
Each correction records the old and new market names and locations and its
reason.

The synchronization is run once during fuel construction and again after all
selected transformations, immediately before scenario caching. The final pass
reconstructs the provider index from the current database, catches consumers
created by later heat or transport updates, prunes orphan markets, refreshes
diagnostics, and fails if a major hydrogen-integrity issue remains. It is
idempotent across repeated, reordered, and incremental updates.

Assumptions and limitations
---------------------------

Interpret results in light of both the supply boundary and the evidence
supporting the production and delivery assumptions.

Delivery boundary
~~~~~~~~~~~~~~~~~

Compare hydrogen at the same pressure, state and delivery boundary. Include
the linked transport and conversion services when assessing delivered supply.
The one-kilogram production mix at market level does not include all upstream
make-up hydrogen used to compensate for losses in those services.

.. _implementation-limitation-energy-floors:

Production energy floors
~~~~~~~~~~~~~~~~~~~~~~~~

External electrolysis assumptions are distinct from IAM projections. In the
IAM branch, feedstock exchanges use the inverse efficiency factor without
enforcing the configured minimum on their amounts. The reported energy value
can therefore differ from the sum of those exchanges. Use the actual exchange
sum when assessing energy demand.

.. _hydrogen-distribution-evidence-gaps:

Evidence gaps and interpretation limits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The distribution model represents a possible delivery system for each sector.
Its results depend on assumptions that remain only partly supported:

* **Mode shares are provisional.** The demand thresholds and truck,
  pipeline, ship and on-site shares have no published calibration. This
  includes the 70% pipeline/30% ammonia split for large steel plants.
  These shares should not be interpreted as observed or forecast market shares.
* **Typical consumers simplify a diverse population.** Plant sizes, vehicle
  use and station capacities are fixed across regions and years. Several
  exact values still lack a reproducible derivation from the literature.
  For chemicals and other uses, demand per site follows directly from the
  assumed site size, which therefore determines the distribution rule.
* **Distance and refuelling assumptions have limited geographic support.**
  European transport statistics and routes to Germany are applied more
  broadly. Weekly car refuelling represents conventional-fuel behaviour;
  the 3.5-day freight interval lacks clear support from its associated source.
* **Some delivery inventories remain unresolved.** Ammonia cargo mass,
  cracking energy and recovery losses need a consistent mass and energy
  balance. Truck loss calculations and ship-engine factors also need stronger
  justification. These uncertainties affect the burden added per kilogram
  of delivered hydrogen.

The :ref:`assumptions and sources <hydrogen-distribution-references>` below
identify the values involved. Robustness to plant sizes, station assumptions,
mode shares and thresholds has not been established. When using these results
to compare supply options, examine those assumptions as well as transport
distance; changing distance alone does not capture the full uncertainty.

Worked example and checks
-------------------------

These examples illustrate individual calculation steps. They do not describe
a complete IAM scenario or validate the assumptions used by the model.

Production efficiency example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the mapped efficiency improves by 10%, a selected electricity input of
55 kWh/kg becomes ``55 / 1.1 = 50 kWh/kg``. This calculation concerns the
production activity; delivery and conditioning add their own requirements.

Distribution example
~~~~~~~~~~~~~~~~~~~~

Consider an eligible demand row with **500 t of hydrogen per node per year**.
The distribution rule assigns 80% to compressed hydrogen by truck and 20% to
liquid hydrogen by truck. If this is the only demand row contributing to the
sector market, its shares become the market shares.

For one kilogram of market output, the direct inputs are:

.. list-table:: Illustrative market inputs
   :header-rows: 1
   :widths: 45 55

   * - Input
     - Amount
   * - Hydrogen production mix
     - 1 kg
   * - Compressed hydrogen trucking
     - ``0.8 * 50 km * 0.001 t/kg = 0.040 tkm``
   * - Liquid hydrogen trucking
     - ``0.2 * 100 km * 0.001 t/kg = 0.020 tkm``
   * - Compression service
     - 0.8 units
   * - Liquefaction service
     - 0.2 units
   * - Regasification service
     - 0.2 units

Make-up hydrogen for losses is accounted for within the supporting inventories.
It must be included when evaluating the full supply-chain result. With several
demand rows, first weight each row's delivery shares by its annual hydrogen
demand, as described under :ref:`hydrogen-market-delivery-inputs`.

.. _diagnostics:

Checking the generated database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow the same chain when inspecting a result:

#. Check regional hydrogen demand and the estimated demand per plant or station.
#. Identify the selected distribution rule and verify that transport and on-site
   shares sum to one.
#. Check which sector markets were created and inspect their production,
   transport and conversion inputs.
#. Follow the consumer's hydrogen exchange to confirm its sector and region.
#. Include support inventories when checking energy use and hydrogen losses.

The structured change report's ``Hydrogen`` sheet contains one row for every demand node and one row for
every successful sector-market relink. In addition, the transformed scenario
stores the demand-node table; eligible, consumer-backed, excluded-without-
consumers, generated, uncreated, and skipped sector markets; and matched,
unmatched, and skipped hydrogen consumers. These
records distinguish a legitimately absent market from a routing or construction
problem and make the full demand-to-consumer chain auditable.

Demand and logistics calculations must succeed before sector-market creation
and consumer linking. An error in logistics, its audit records or market
creation stops the fuels update rather than leaving a partial delivery system.

.. _source-inventories-hydrogen:

Sources and inventory details
-----------------------------

The sources below follow the same order as the method: production, demand
and distance assumptions, then delivery services. Turbine and vehicle-tank
inventories are grouped separately because they describe hydrogen end uses.

.. contents:: Source groups
   :local:
   :depth: 1
   :backlinks: none

.. _source-provenance-and-currency:

Sources and data dates
~~~~~~~~~~~~~~~~~~~~~~

.. include:: /reference/generated/source-hydrogen.inc

.. _hydrogen-production:

Hydrogen production inventories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*premise* imports inventories for hydrogen production. The table below
gives an overview of the different pathways and their assumed specific energy use
in 2020 and 2050.


.. list-table:: Hydrogen production inventories
   :header-rows: 1

   * - Dataset
     - Feedstock
     - U
     - 2020 avg
     - 2020 rng
     - 2050 avg
     - 2050 rng
     - Floor
     - Loc
     - Literature reference
   * - hydrogen production, steam methane reforming
     - natural gas
     - m^3
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.5
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_SMR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, steam methane reforming, with CCS
     - natural gas
     - m^3
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.5
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_SMR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, steam methane reforming, from biomethane
     - biomethane
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.2
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_SMR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, steam methane reforming, from biomethane, with CCS
     - biomethane
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.2
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_SMR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, auto-thermal reforming, from biomethane
     - biomethane
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.2
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_ATR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, auto-thermal reforming, from biomethane, with CCS
     - biomethane
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 3.2
     - CH
     - `Antonini <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00222d>`__ et al. 2021 [`LCI_ATR <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-smr-atr-natgas.xlsx>`__]
   * - hydrogen production, gaseous, 25 bar, from heatpipe reformer gasification of woody biomass with CCS
     - wood chips
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 7.0
     - CH
     - `Antonini2 <https://pubs.rsc.org/en/Content/ArticleLanding/2021/SE/D0SE01637C>`__ et al. 2021 [`LCI_woody <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-wood-gasification.xlsx>`__]
   * - hydrogen production, gaseous, 25 bar, from heatpipe reformer gasification of woody biomass
     - wood chips
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 7.0
     - CH
     - `Antonini2 <https://pubs.rsc.org/en/Content/ArticleLanding/2021/SE/D0SE01637C>`__ et al. 2021 [`LCI_woody <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-wood-gasification.xlsx>`__]
   * - hydrogen production, gaseous, 25 bar, from gasification of woody biomass in entrained flow gasifier, with CCS
     - wood chips
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 7.0
     - CH
     - `Antonini2 <https://pubs.rsc.org/en/Content/ArticleLanding/2021/SE/D0SE01637C>`__ et al. 2021 [`LCI_woody <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-wood-gasification.xlsx>`__]
   * - hydrogen production, gaseous, 25 bar, from gasification of woody biomass in entrained flow gasifier
     - wood chips
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 7.0
     - CH
     - `Antonini2 <https://pubs.rsc.org/en/Content/ArticleLanding/2021/SE/D0SE01637C>`__ et al. 2021 [`LCI_woody <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-wood-gasification.xlsx>`__]
   * - hydrogen production, coal gasification
     - hard coal
     - kg
     - N/A
     - N/A
     - N/A
     - N/A
     - 5.0
     - RER
     - `Wokaun <https://www.cambridge.org/core/books/transition-to-hydrogen/43144AF26ED80E7106B675A6E83B1579>`__, `Li <https://doi.org/10.1016/j.jclepro.2022.132514>`__ [`LCI_coal <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-coal-gasification.xlsx>`__]
   * - hydrogen production, gaseous, 30 bar, from PEM electrolysis, from grid electricity
     - electricity
     - kWh
     - 54.0
     - 52.9–55.1
     - 48.9
     - 45.3–52.5
     - 45.3
     - RER
     - `Gerloff <https://doi.org/10.1016/j.est.2021.102759>`__ 2021 [`LCI_electrolysis <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-electrolysis.xlsx>`__]
   * - hydrogen production, gaseous, 20 bar, from AEC electrolysis, from grid electricity
     - electricity
     - kWh
     - 51.8
     - 48.7–54.9
     - 48.5
     - 47.1–49.9
     - 47.1
     - RER
     - `Gerloff <https://doi.org/10.1016/j.est.2021.102759>`__ 2021 [`LCI_electrolysis <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-electrolysis.xlsx>`__]
   * - hydrogen production, gaseous, 1 bar, from SOEC electrolysis, from grid electricity
     - electricity
     - kWh
     - 42.3
     - 41.2–43.4
     - 40.6
     - 40.0–41.2
     - 40.0
     - RER
     - `Gerloff <https://doi.org/10.1016/j.est.2021.102759>`__ 2021 [`LCI_electrolysis <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-electrolysis.xlsx>`__]
   * - hydrogen production, gaseous, 1 bar, from SOEC electrolysis, with steam input, from grid electricity
     - electricity
     - kWh
     - 42.3*
     - 41.2–43.4
     - 40.6
     - 40.0–41.2
     - 40.0
     - RER
     - `Gerloff <https://doi.org/10.1016/j.est.2021.102759>`__ 2021 [`LCI_electrolysis <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-electrolysis.xlsx>`__]
   * - hydrogen production, gaseous, 25 bar, from thermochemical water splitting, at solar tower
     - solar
     - MJ
     - N/A
     - N/A
     - N/A
     - N/A
     - 180
     - RER
     - `Zhang2 <https://doi.org/10.1016/j.ijhydene.2022.02.150>`__ 2022
   * - hydrogen production, gaseous, 100 bar, from methane pyrolysis
     - natural gas
     - m^3
     - N/A
     - N/A
     - N/A
     - N/A
     - 6.5
     - RER
     - `Al-Qahtani <https://doi.org/10.1016/j.apenergy.2020.115958>`__, `Postels <https://doi.org/10.1016/j.ijhydene.2016.09.167>`__


Future efficiencies for electrolyzers are based on Studie `IndWEDe <https://www.now-gmbh.de/wp-content/uploads/2020/09/indwede-studie_v04.1.pdf>`__ (see p.176).
The SOEC inventory with a steam input uses the same performance assumptions as
the standard SOEC inventory because no separate performance data are available.

.. _hydrogen-distribution-references:

.. _hydrogen-distribution-assumptions-and-references:

Demand and distance assumptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hydrogen delivery depends on how much each consumer needs, how often it needs
it, and how far it is from the supplier. Premise estimates these quantities
using typical plant sizes, vehicle use and delivery distances. Hydrogen demand
changes with the IAM scenario; the defaults below are held constant across
regions and years.

Industrial consumers
^^^^^^^^^^^^^^^^^^^^

Regional production or hydrogen demand is divided
among representative plants. These plants describe a typical scale of demand;
they are not a map of actual facilities.

.. list-table:: Industrial demand assumptions
   :header-rows: 1
   :widths: 18 43 39

   * - Consumer
     - Default
     - Related literature
   * - Steel
     - 0.5 Mt steel/year per plant; 333 operating days/year
     - `Lei et al. (2023) <https://doi.org/10.1038/s41586-023-06486-7>`__,
       global iron and steel plant data.
   * - Cement
     - 2.4 Mt/year capacity per plant, used at 55% of capacity
     - `Tkachenko et al. (2023)
       <https://doi.org/10.1038/s41597-023-02599-w>`__, global cement assets.
   * - Chemicals
     - 60,300 t H2/year per plant
     - `Fuel Cells and Hydrogen Observatory, Market report 2022
       <https://observatory.clean-hydrogen.europa.eu/sites/default/files/2023-05/Chapter-2-FCHO-Market-2022-Final.pdf>`__,
       Chapter 2.
   * - Other industrial uses
     - 1,000 t H2/year per site; 333 operating days/year
     - Studies of hydrogen use in `glass production (Zier et al.)
       <https://doi.org/10.1016/j.ecmx.2022.100336>`__,
       `glass furnaces (Daurer et al.)
       <https://doi.org/10.1016/j.fuel.2024.133576>`__ and
       `paper production <https://doi.org/10.1016/j.gerr.2026.100174>`__.

These publications provide context for industrial plant sizes and hydrogen
use. The derivation of the exact representative values remains incomplete,
including the cement capacity factor and average chemical-plant demand.
The 333-day steel operating year is a modelling assumption without a specific
source. These defaults should therefore be treated as assumed plant
characteristics, rather than measured global averages. The ``Other`` category
also includes uses beyond the glass and paper industries represented by these
studies.

Refuelling stations
^^^^^^^^^^^^^^^^^^^

Passenger and freight transport demand is converted
into vehicle numbers and refuelling visits. Station numbers depend on the
following assumptions.

.. list-table:: Transport demand assumptions
   :header-rows: 1
   :widths: 27 38 35

   * - Parameter
     - Default
     - Literature or assumption
   * - Annual distance
     - Cars: 10,900 km; freight vehicles: 23,900 km
     - `ODYSSEE-MURE transport report
       <https://www.odyssee-mure.eu/publications/efficiency-by-sector/transport/transport-eu.pdf>`__
       (Europe).
   * - Vehicles served per station per day
     - 1,500 cars or 400 freight vehicles
     - `Reuss et al. (2019)
       <https://doi.org/10.1016/j.apenergy.2019.04.064>`__, hydrogen
       infrastructure in Germany; the throughput values require confirmation.
   * - Car refuelling interval
     - 7 days
     - `Zaleski et al. (2014) <https://doi.org/10.1038/jes.2012.128>`__,
       Table 5; conventional-fuel refuelling used as a proxy.
   * - Freight refuelling interval
     - 3.5 days
     - Modelling assumption; the `US DOE truck targets
       <https://www.hydrogen.energy.gov/docs/hydrogenprogramlibraries/pdfs/19006_hydrogen_class8_long_haul_truck_targets.pdf>`__
       do not establish this interval.
   * - Car occupancy
     - 1.5 people per vehicle
     - `Mobilitaet in Deutschland 2023
       <https://www.mobilitaet-in-deutschland.de/pdf/MiD2023_Ergebnisbericht.pdf>`__.
   * - Freight load
     - 15 t per vehicle
     - `ICCT assessment of EU heavy-duty vehicles
       <http://theicct.org/EU-HDV-fuel-efficiency-tech-2020-2030>`__.

Most of these sources concern European or German transport. Their use in
other regions and future years is an extrapolation. Weekly car refuelling is
a default from a conventional-fuel exposure study, not a measurement of
hydrogen-vehicle use. Freight refuelling remains less well supported: the DOE
report describes daily refuelling for maximum-range operation, with less
frequent visits at lower mileage. Station throughput also remains uncertain,
including the interpretation of capacity as vehicles served per day.

Delivery distances
^^^^^^^^^^^^^^^^^^

Each delivery mode uses a representative distance.
The model does not calculate routes between individual producers and consumers.

.. list-table:: Default delivery distances
   :header-rows: 1
   :widths: 29 24 47

   * - Delivery mode
     - Distance
     - Related literature
   * - Compressed hydrogen by truck
     - 50 km
     - `Parolin et al. (2024)
       <https://doi.org/10.1016/j.ijhydene.2024.06.049>`__, regional delivery
       infrastructure.
   * - Liquid hydrogen by truck
     - 100 km
     - Parolin et al. (2024).
   * - Ammonia or liquid hydrogen by ship
     - 2,500 km
     - `Hampp et al. (2023)
       <https://doi.org/10.1371/journal.pone.0281380>`__, energy-carrier
       imports to Germany.
   * - Pipeline
     - 250 km transmission plus 250 km distribution
     - Sacchi and Bauer (2023), *LCA of Power-to-X processes and applications
       in the residential sector*, Paul Scherrer Institut.

The literature examines particular delivery networks and import routes. It
does not establish these distances as global averages. For example, Hampp et
al. use different shipping distances for different exporting countries. The
choice of a single 2,500 km route is therefore a simplifying assumption.

Delivery inventories
~~~~~~~~~~~~~~~~~~~~

The delivery model uses transport and conditioning services together with
their supporting infrastructure. The catalogue below distinguishes the service
activities linked to markets from the underlying storage and infrastructure
inventories.

.. _hydrogen-supply-chain-names:

Detailed supply-chain names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :ref:`sector-specific-hydrogen-markets` section lists market names and
their creation conditions. To inspect the delivery and conditioning services
linked to those markets, look for the following activity names:

.. list-table:: Hydrogen delivery and conditioning activities
   :header-rows: 1
   :widths: 25 60 15

   * - Service
     - Activity name
     - Unit
   * - Pipeline distribution
     - ``hydrogen supply, distributed by pipeline``
     - kilogram
   * - Compressed hydrogen trucking
     - ``transport, hydrogen, gaseous, lorry, unspecified``
     - ton kilometer
   * - Liquid hydrogen trucking
     - ``transport, hydrogen, liquid, lorry, unspecified``
     - ton kilometer
   * - Ammonia shipping
     - ``transport, freight, sea, tanker for liquefied ammonia, ammonia and mdo``
     - ton kilometer
   * - Compression
     - ``gaseous hydrogen production``
     - unit
   * - Liquefaction
     - ``liquid hydrogen production``
     - unit
   * - Regasification
     - ``liquid hydrogen regasification``
     - unit
   * - Ammonia synthesis
     - ``liquid ammonia production``
     - unit
   * - Ammonia cracking
     - ``ammonia cracking``
     - unit

Pipeline, truck and conversion activities are regionalized from imported
inventories; the ammonia ship activity remains global. The conversion
activities provide processing services, despite the word "production" in
some of their names. Their service inputs are separate from the hydrogen
production mix.

A service's presence in the database does not mean that every hydrogen market
uses it. Check the market's exchanges for its actual delivery mix, and its
location for the region supplied.

.. _hydrogen-distribution-inventory-sources:

Transport and conversion inventory sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Delivery adds energy use, infrastructure and losses to hydrogen production.
Compressed hydrogen requires compression; liquid hydrogen requires
liquefaction and regasification; ammonia delivery requires synthesis followed
by cracking to recover hydrogen. The main inventory sources are:

* **Liquefaction and ammonia synthesis:** `Wei et al. (2026)
  <https://doi.org/10.1016/j.resconrec.2025.108671>`__, supplementary Tables
  S21-S22 and S28-S30. The study draws on Al Ghafri et al., Wulf and Zapp,
  and D'Angelo et al. for these processes.
* **Compression:** ecoinvent compression inputs, with a pipeline-compressor
  proxy for equipment. Equipment requirements at the 250-bar delivery
  pressure remain uncertain.
* **Regasification:** `Kolb et al. (2022)
  <https://doi.org/10.1016/j.jclepro.2022.133289>`__, an assessment of liquid
  hydrogen imports to Germany.
* **Truck transport, storage and refuelling infrastructure:**
  `Wulf et al. (2018)
  <https://www.sciencedirect.com/science/article/pii/S095965261832170X>`__
  and Reuss et al. (2019). Reassigned natural-gas pipelines also draw on
  `Cerniauskas et al. (2020)
  <https://doi.org/10.1016/j.ijhydene.2020.02.121>`__.
* **Ammonia cracking:** `Thyssenkrupp Uhde
  <https://www.thyssenkrupp-uhde.com/en/ammonia-cracking>`__ provides the
  plant-sizing reference. The energy requirement and hydrogen recovery
  assumptions do not yet have a sufficiently precise supporting source.
* **Ammonia shipping:** an ecoinvent liquefied-natural-gas tanker provides
  the vessel and auxiliary infrastructure. Fuel and emission assumptions
  draw on IMO reports, Sphera (2024), Wei et al. and author calculations.
  Some of these sources lack full bibliographic details, and the retained
  LNG infrastructure is an approximation of ammonia transport.

Support for an individual process does not validate the complete delivery
chain. In particular, the ammonia route still requires reconciliation of
cargo mass, conversion energy and hydrogen recovery. Truck loss assumptions
also need a consistent basis for relating the quantity lost to the distance
travelled. See :ref:`hydrogen-distribution-evidence-gaps` for the implications
when interpreting results.

Implementation locations and detailed source checks are available in the
:doc:`developer source review </development/hydrogen-distribution-review>`.

.. _hydrogen-storage-and-distribution:

Storage and distribution infrastructure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of datasets relating to hydrogen storage and distribution are also imported.

They are necessary to model the distribution of hydrogen:

* via re-assigned transmission and distribution CNG pipelines, in a gaseous state
* via dedicated transmission and distribution hydrogen pipelines, in a gaseous state
* as a liquid organic compound, by hydrogenation
* via truck, in a liquid state
* hydrogen refuelling station

Small and large storage solutions are also provided:

* high pressure hydrogen storage tank
* geological storage tank

These datasets originate from the work of `Wulf <https://www.sciencedirect.com/science/article/pii/S095965261832170X>`__ et al. 2018, and can be
consulted here: `LCI_H2_distr <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-distribution.xlsx>`__. For re-assigned CNG pipelines, which require the hydrogen
to be mixed together with oxygen to limit metal embrittlement,
some parameters are taken from the work of `Cerniauskas <https://doi.org/10.1016/j.ijhydene.2020.02.121>`__ et al. 2020.

The datasets introduced are listed in the table below.

 ================================================================== ===========
  Hydrogen distribution                                              location
 ================================================================== ===========
  hydrogen refuelling station                                        GLO
  high pressure hydrogen storage tank                                GLO
  pipeline, hydrogen, low pressure distribution network              RER
  compressor assembly for transmission hydrogen pipeline             RER
  pipeline, hydrogen, high pressure transmission network             RER
  zinc coating for hydrogen pipeline                                 RER
  hydrogenation of hydrogen                                          RER
  dehydrogenation of hydrogen                                        RER
  dibenzyltoluene production                                         RER
  solution mining for geological hydrogen storage                    RER
  geological hydrogen storage                                        RER
  hydrogen embrittlement inhibition                                  RER
  distribution pipeline for hydrogen, reassigned CNG pipeline        RER
  transmission pipeline for hydrogen, reassigned CNG pipeline        RER
 ================================================================== ===========

End-use inventories
~~~~~~~~~~~~~~~~~~~

These inventories describe the use or onboard storage of hydrogen. Their
boundaries are separate from the delivery services supplied by hydrogen
markets.

Hydrogen turbine
^^^^^^^^^^^^^^^^

A dataset for a hydrogen turbine is also imported, to model the production of electricity
from hydrogen, with an efficiency of 51%. The efficiency of the H2-fed gas turbine is based
on the parameters of `Ozawa <https://doi.org/10.1016/j.ijhydene.2019.02.230>`__ et al. (2019), accessible here: `LCI_H2_turbine <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-turbine.xlsx>`__.

Vehicle hydrogen tank inventories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The HDPE- and aluminium-lined 700-bar tank activities in ``lci-trucks.xlsx``
produce one kg of dry tank assembly, including tank balance of plant and
excluding stored hydrogen. The quantities come from `Evangelisti et al. (2017)
<https://doi.org/10.1016/j.jclepro.2016.11.159>`_ and its
`supplementary inventory tables
<https://ars.els-cdn.com/content/image/1-s2.0-S0959652616320212-mmc1.docx>`_.
The supplement was checked on 10 October 2026 (SHA256
``ca9470c504f61ef58e2e5cc3cad8c06d6cecf17073074ac2ce19dca3678ac49d``).

The paper's main text, scenario labels and supplementary output masses are
inconsistent. Identify the recipes by their materials: the table headed S16
contains HDPE, while S17 contains an aluminium liner. Previously, their material
quantities were divided by 119 and 93 kg, respectively, producing 0.737059 and
1.216871 kg of material inputs per kg of tank.

The corrected denominators are the sums of the listed materials: **87.71 kg
for HDPE and 113.169 kg for aluminium**. Material proportions are retained and
now sum to one kg per kg of dry assembly. The differences from the supplement's
nominal 93 and 119 kg outputs are approximately stored hydrogen, but the paper
does not state that boundary unambiguously. Dry-mass normalization is an explicit
modelling choice; no unidentified missing material is added.

Manufacturing electricity is published as 12.87 and 16.422 **MJ per assembly**.
Dividing by 3.6 MJ/kWh and the respective dry mass gives 0.0407593 and
0.0403084 kWh/kg. Previously these MJ values had been treated as kWh.
Steel working and sheet rolling are processing services and do not add material
mass. Aluminium sheet and ingot both contribute to the aluminium purchase.

Dataset and exchange comments record the source, formulas and boundary. Existing
supplier proxies, including AlLi for aluminium, are retained; this correction
does not establish current vehicle composition, sizing or manufacturing yields.
The separate generic carbon-fibre assembly and HDPE liner activities use other
source recipes and are outside this correction.

``tests/test_hydrogen_tank_inventories.py`` checks material closure and energy
units after Brightway Excel import and its preparation strategies, without
writing a database, plus quantity preservation through migrations to ecoinvent
3.9--3.12. The supplementary-inventory cache key includes the tank workbook
content, so rebuilding cannot reuse the old recipes. Existing generated
databases must still be rebuilt before their tank inventories change.
