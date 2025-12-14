============================
nbeernink.cvad Release Notes
============================

.. contents:: Topics

v0.0.7
======

Release Summary
---------------

ContinuationToken and inventory upgrade

Major Changes
-------------

- Add inventory group_prefix
- Add inventory groups for MaintenanceMode, PowerState, MachineType, DeliveryGroup, MachineCatalog
- Add support for paging through the REST API (ContinuationToken) https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/how-to-use-paging-to-query-many-objects-through-multiple-api-calls

v0.0.6
======

Release Summary
---------------

Add the first basic Citrix inventory plugin

New Plugins
-----------

Inventory
~~~~~~~~~

- nbeernink.cvad.cvad - Citrix Virtual Apps and Desktops inventory plugin

v0.0.5
======

Release Summary
---------------

Add antsibull for changelog tracking

v0.0.4
======

Release Summary
---------------

Bugfix + coding style update

Bugfixes
--------

- Ensure ansible-sanity test completes succesfully
- Fix machine_info's python import
