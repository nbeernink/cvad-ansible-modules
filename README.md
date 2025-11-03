# CVAD Ansible Modules

Ansible modules for interacting with the [Citrix Virtual Apps and Desktops
API](https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/overview)

### CVADClient

This Ansible collection includes a custom REST API helper (CVADClient) which abstracts "the technical
stuff" allowing re-use of code and easier module development.

### Why this collection?

Citrix provides a [terraform
provider](https://github.com/citrix/terraform-provider-citrix), however that doesn't allow us to
orchestrate things in a certain order, which is where hopefully this collection
can fill a gap.

### Modules included
Currently only `machine_info` is included and serves as a template for future
modules.

# Installation
You can install the collection from [Ansible
Galaxy](https://galaxy.ansible.com/nbeernink/cvad) by running `ansible-galaxy
collection install nbeernink.cvad`.

### TODO
* Add additional modules to allow:
  - Turning maintenance mode on/off for a machine
  - Assigning/removing users for a given machine
  - Controlling a machine's power state (if available)
  - Creating new Delivery & Machine catalogs
  - Adding machines to a specific machine catalog
  - Adding machines to a specific delivery catalog
  - Your great idea here?
* Set up automated linting/ansible-testing
* Since Citrix publishes an [OpenAPI specification](https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/apis/citrix-cvad-rest-apis.json), hopefully this collection can be tested against a mock API provided via [prism](https://github.com/stoplightio/prism)
