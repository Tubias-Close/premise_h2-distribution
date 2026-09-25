Hydrogen
==========


.. contents:: On this page
   :local:
   :depth: 1

.. raw:: html

   <span id="key-outputs"></span>

Scope and outputs
-------------------

Within the ``fuels`` update, Premise regionalizes hydrogen production and
builds regional gaseous low-pressure hydrogen markets per kilogram. Imported
supply-route variants describe conditioning and delivery options; their
availability is distinct from the route used by a generated market.

.. figure:: /_static/process-diagrams/fuels-hydrogen.svg
   :class: process-diagram
   :alt: Hydrogen production and delivery: Regionalize hydrogen production; Adjust selected feedstock inputs; Build regional hydrogen markets; Add pipeline delivery service and relink.
   :align: center

Inputs and applicability
--------------------------

The hydrogen entries of ``fuels.yaml`` map inventories and IAM production
and efficiency series. ``premise/data/fuels/hydrogen_efficiency_parameters.yml`` supplies
feedstock selectors and external electrolysis assumptions. The fuels branch
runs when at least one petrol, diesel, natural-gas or hydrogen blend array is
available. Use ``ndb.update("fuels")`` after upstream energy updates.

Transformation
----------------

For a mapped IAM efficiency signal, the selected feedstock exchanges are
multiplied by the inverse efficiency change. Selection uses the configured
name substring and unit; other inputs are not automatically scaled.
Without an IAM signal, electrolysis uses the external electricity-requirement
trajectory. Other pathways keep their feedstock amount in this adjustment.
The energy-floor limitation below qualifies the IAM branch.

Hydrogen supply chains
~~~~~~~~~~~~~~~~~~~~~~~~

The imported hydrogen supply-route catalogue contains variants that differ by:

* the transport mode: truck, hydrogen pipeline, re-assigned CNG pipeline, ship,
* the distance: 500 km, 2000 km
* the state of the hydrogen: gaseous, liquid, liquid organic compound,
* the hydrogen production route: electrolysis, SMR, biomass gasifier (coal, woody biomass)

The supply chain is built in stages::

    Production -> conditioning -> transport and storage -> delivered hydrogen
                      |                  |
                   energy use        losses and energy use

Compare routes at the same delivery state and pressure. Transport losses
increase upstream hydrogen production per kilogram delivered; compression and
liquefaction add their own energy requirements. A plant-gate production score
therefore cannot validate the delivered route by itself.

Boil-off loss values during shipping are from `Hank <https://pubs.rsc.org/en/content/articlelanding/2020/se/d0se00067a>`__ et al, 2020.
Losses when transporting H2 via re-assigned CNG pipelines are from `Cerniauskas <https://doi.org/10.1016/j.ijhydene.2020.02.121>`__ et al, 2020.
Losses along the pipeline are from `Schori <https://treeze.ch/fileadmin/user_upload/downloads/PublicLCI/Schori_2012_NaturalGas.pdf>`__ et al, 2012., but to be considered conservative, as those
are initially for natural gas (and hydrogen has a higher potential for leaking).

 ========================== ================= ======== ======= ============== =============== ====================
  _                          _                 truck    ship    H2 pipeline    CNG pipeline    reference flow
 ========================== ================= ======== ======= ============== =============== ====================
  gaseous                    compression       0.5%             0.5%           0.5%            per kg H2
  _                          storage buffer                     2.3%           2.3%            per kg H2
  _                          storage leak                       1.0%           1.0%            per kg H2
  _                          pipeline leak                      0.004%         0.004%          per kg H2, per km
  _                          purification                                      7.0%            per kg H2
  liquid                     liquefaction      1.3%     1.3%                                   per kg H2
  _                          vaporization      2.0%     2.0%                                   per kg H2
  _                          boil-off          0.2%     0.2%                                   per kg H2, per day
  liquid organic compound    hydrogenation     0.5%                                            per kg H2
 ========================== ================= ======== ======= ============== =============== ====================

Losses accumulate along the supply chain and depend on route and distance.
Use a consistent production or delivery basis when combining loss fractions.
The table below shows the example of 1 kg of hydrogen transport via re-assigned CNG pipelines,
as a gas, over 500 km.
The supplier input is 1.133 kg per kg delivered: 0.133 kg is lost per kg
delivered, approximately 11.7% of the hydrogen produced:


 =============================================================================== ============== ================ ===========
  Output                                                                          _              _                _
 =============================================================================== ============== ================ ===========
  producer                                                                        amount         unit             location
  hydrogen supply, from electrolysis, by CNG pipeline, as gaseous, over 500 km    1              kilogram         OCE
  Input
  supplier                                                                        amount         unit             location
  hydrogen production, gaseous, 25 bar, from electrolysis                         1.133          kilogram         OCE
  market group for electricity, low voltage                                       3.091          kilowatt hour    OCE
  market group for electricity, low voltage                                       0.516          kilowatt hour    OCE
  hydrogen embrittlement inhibition                                               1              kilogram         OCE
  geological hydrogen storage                                                     1              kilogram         OCE
  Hydrogen refuelling station                                                     1.14E-07       unit             OCE
  distribution pipeline for hydrogen, reassigned CNG pipeline                     1.56E-08       kilometer        RER
  transmission pipeline for hydrogen, reassigned CNG pipeline                     1.56E-08       kilometer        RER
 =============================================================================== ============== ================ ===========


The two direct electricity exchanges in this route illustration sum to
3.607 kWh per kg delivered. Additional requirements must be checked in the
linked distribution and storage activities. The illustration is not an
independent validation of the active scenario's delivery route.

.. _sector-specific-hydrogen-markets:

Sector-specific hydrogen markets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fuel transformation creates end-use-specific hydrogen markets so that the
logistics burden of supplying hydrogen can differ between steel, cement,
chemicals, transport, heating, and other uses. The calculation is performed in
the following order:

.. code-block:: text

   normalized direct-hydrogen final energy
                 |
                 v
   regional sector demand and demand-node estimates
                 |
                 v
   distribution decision tree for every demand row
                 |
                 v
   demand-weighted transport shares in each sector market
                 |
                 v
   relinking of eligible hydrogen consumers

This order is mandatory. Demand-node calculation and its audit log run before
hydrogen activities are generated. Sector markets are then created, and only
markets that were actually added to the database can receive consumers. An
exception in logistics calculation, audit logging, or market creation stops the
fuel transformation before consumer relinking.

Direct-hydrogen demand
^^^^^^^^^^^^^^^^^^^^^^

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

Demand-node creation
^^^^^^^^^^^^^^^^^^^^

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

The calculated node count can be fractional. ``demand_nodes_rounded_up`` stores
its ceiling for reporting, but demand per node is calculated with the
unrounded value. The demand-node table also records annual and daily hydrogen
demand per node, source IAM variables, the calculation method, and the result
of the regional-versus-``World`` validation.

Distribution decision tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

   The shares and thresholds in the current decision tree are indicative
   assumptions. The YAML file identifies them as placeholders until
   sector-specific threshold assumptions are finalized.

Sector-market creation and transport shares
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
     - ``share`` kg gaseous hydrogen production
   * - Liquid hydrogen by truck
     - ``transport, hydrogen, liquid, lorry, unspecified``
     - ``share * 100 * 0.001`` tkm
     - ``share`` kg liquefaction and ``share`` kg regasification
   * - Compressed gas by pipeline
     - ``hydrogen supply, distributed by pipeline``
     - ``share`` kg
     - None
   * - Liquid ammonia by ship
     - ``transport, freight, sea, tanker for liquefied ammonia, ammonia and
       mdo``
     - ``share * 2500 * 0.001`` tkm
     - ``share / 0.175`` kg ammonia production and ``share * 7.67`` kg
       ammonia cracking
   * - Liquid hydrogen by ship
     - ``transport, freight, sea, tanker for liquefied hydrogen, heavy fuel
       oil``
     - ``share * 2500 * 0.001`` tkm
     - ``share`` kg liquefaction and ``share`` kg regasification

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

Customer relinking
^^^^^^^^^^^^^^^^^^

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

Diagnostics
^^^^^^^^^^^

The structured change report's ``Hydrogen`` sheet contains one row for every demand node and one row for
every successful sector-market relink. In addition, the transformed scenario
stores the demand-node table; eligible, consumer-backed, excluded-without-
consumers, generated, uncreated, and skipped sector markets; and matched,
unmatched, and skipped hydrogen consumers. These
records distinguish a legitimately absent market from a routing or construction
problem and make the full demand-to-consumer chain auditable.

Markets and downstream links
------------------------------

Generated hydrogen markets use mapped production volumes and the common
system-model supplier weighting. A regionalized
``hydrogen supply, distributed by pipeline`` service is added at 1 kg per kg
of market output. This does not mean all truck, ship and pipeline variants
listed in the inventory catalogue are deployed in every scenario.
Relinking connects the resulting suppliers to consuming activities.

Assumptions and limitations
-----------------------------

Compare hydrogen at the same pressure, state and delivery boundary.
External electrolysis assumptions are distinct from IAM projections. When
checking energy floors, inspect actual exchanges as well as logged totals;
the exchange behavior described below applies.

Implementation limitation: energy floors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the IAM branch, feedstock exchanges use the inverse efficiency factor
without enforcing the configured minimum on their amounts. The reported
energy value can therefore differ from the sum of those exchanges. Use the
actual exchange sum when assessing energy demand.

Worked example and checks
---------------------------

If the mapped efficiency improves by 10%, a selected 55 kWh/kg electricity
input becomes 55/1.1 = 50 kWh/kg before any separate delivery requirements.
For a delivery route requiring 1.133 kg produced per kg delivered, the excess
is 0.133 kg per kg delivered, or about 11.7% of production. Check the loss
basis, transport electricity and the route actually linked to the consumer.

Sources and inventory details
-------------------------------

Source inventories: hydrogen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hydrogen production
^^^^^^^^^^^^^^^^^^^^^

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

Hydrogen storage and distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Hydrogen turbine
^^^^^^^^^^^^^^^^^^

A dataset for a hydrogen turbine is also imported, to model the production of electricity
from hydrogen, with an efficiency of 51%. The efficiency of the H2-fed gas turbine is based
on the parameters of `Ozawa <https://doi.org/10.1016/j.ijhydene.2019.02.230>`__ et al. (2019), accessible here: `LCI_H2_turbine <https://github.com/polca/premise/blob/76dbf845ef73bb765024dda1143960a24964a5fe/premise/data/additional_inventories/lci-hydrogen-turbine.xlsx>`__.

.. raw:: html

   <span id="source-provenance-and-currency"></span>

Sources and data dates
~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /reference/generated/source-hydrogen.inc

Detailed supply-chain names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /reference/generated/hydrogen-variants.inc
