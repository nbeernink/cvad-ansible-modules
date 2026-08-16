============================
nbeernink.cvad Release Notes
============================

.. contents:: Topics

v0.0.10
=======

Minor Changes
-------------

- Add support for module_defaults
- Allow specifying a message as reason for maintenance mode

v0.0.9
======

Minor Changes
-------------

- Add machine user assignment module

v0.0.8
======

Release Summary
---------------

This 0.0.8 release adds a new module `machine_catalog_machines` as well as a bugfix for the maintenance module

Minor Changes
-------------

- Added new module `machine_catalog_machines`
- Bugfix machine_maintenance_mode swapped info messages (it would say exiting maintenance when in reality it would enter and the other way around)

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
