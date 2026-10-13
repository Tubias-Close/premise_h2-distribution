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

The :ref:`hydrogen-distribution-references` register gives the references
recorded for these values and distinguishes cited defaults from assumptions
whose derivation or applicability still needs clarification.

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
   No publication is cited for these numerical thresholds or mode shares;
   see :ref:`hydrogen-distribution-evidence-gaps`.

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

The conversion activities have the reference unit ``unit`` in the transport
workbook. They represent auxiliary processing services, not additional
hydrogen product inputs. Their physical mass basis and the ammonia factors
require the qualifications in :ref:`hydrogen-distribution-inventory-sources`.
The table describes the implemented exchange amounts, not an independently
validated mass balance. Distance references are also listed in
:ref:`hydrogen-distribution-references`.

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

.. _hydrogen-distribution-references:

Hydrogen distribution assumptions and references
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The register below consolidates references previously recorded in Python
comments and workbook metadata for the sector-specific distribution model.
It supplements the production and legacy supply-route sources above. A
reference recorded beside a parameter establishes traceability; it does not
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

.. _hydrogen-distribution-inventory-sources:

Transport and conversion inventory sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. _hydrogen-distribution-evidence-gaps:

Evidence gaps and interpretation limits
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Detailed supply-chain names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /reference/generated/hydrogen-variants.inc


Vehicle hydrogen tank inventories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
