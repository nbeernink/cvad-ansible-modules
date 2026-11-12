# CVAD Ansible Modules

[![CI](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/ansible-test.yml/badge.svg)](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/ansible-test.yml)
[![CodeQL](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/github-code-scanning/codeql)

An Ansible collection for managing the lifecycle of machines in [Citrix Virtual Apps and Desktops (CVAD)](https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/overview) environments — specifically tailored for organizations **not using Machine Creation Services (MCS)**.

---

## Who is this for?

Citrix provides **Machine Creation Services (MCS)** as a way to provision and manage virtual machines automatically. However some organizations rely on **physical machines** running **Citrix Remote PC** or **manually provisioned VMs**.

In these non-MCS environments, Citrix's first-party tooling (such as the [Terraform provider](https://github.com/citrix/terraform-provider-citrix)) may not fully cover operational needs like:

- Registering physical machines into Machine Catalogs and Delivery Groups
- Putting machines in/out of maintenance mode during patch cycles
- Orchestrating lifecycle events in a specific order (e.g., prepare for maintenance → patch → end maintenance)
- Building dynamic inventory from the Desktop Delivery Controller environment

This collection fills that gap by providing **idiomatic Ansible modules** that wrap the Citrix CVAD REST API (via CVADClient), allowing you to manage machine lifecycle operations with full Ansible orchestration capabilities.

---

## Why Ansible and not Terraform?

Citrix provides a [Terraform provider](https://github.com/citrix/terraform-provider-citrix), but Terraform's declarative model makes it difficult to orchestrate operations **in a specific order** — for example:

1. Query machines that need patching (ie. from Red Hat Satellite)
2. Place each machine in maintenance mode
3. Run patch tasks on the machine
4. Remove maintenance mode once patching is complete

Ansible's playbook model helps with these kinds of operational workflows.

---

## Features

### Ansible Modules

| Module | Description |
|---|---|
| `delivery_group_info` | Retrieve information about a Delivery Group |
| `delivery_group_machines` | Assign or remove machines from a Delivery Group |
| `machine_catalog_info` | Retrieve information about a Machine Catalog |
| `machine_catalog_machines` | Add or remove machines from a Machine Catalog |
| `machine_info` | Retrieve information about a specific machine |
| `machine_maintenancemode` | Enable or disable maintenance mode for a machine |
| `machine_tags` | Attach or detach tags to a machine |
| `machine_user_assignment` | Assign or Unassign a machine to a user |

### Ansible Inventory Plugin

This collection includes an inventory plugin (`nbeernink.cvad.cvad`) that dynamically builds your Ansible inventory from your DDC (Desktop Delivery Controller) environment. Machines are automatically grouped by:

- Delivery Group
- Machine Catalog
- Maintenance mode status

#### Keyed groups

Keyed groups allow you to dynamically group all retrieved machines by for example `AgentVersion` or `RegistrationState`:

```yaml
# inventory.cvad.yml
---
plugin: nbeernink.cvad.cvad
ddc_server: my-example-ddc.example.com
username: my-api-user
password: changeme

keyed_groups:
  - prefix: cvad
    key: AgentVersion

  # group by RegistrationState and lowercase the groupname
  - prefix: cvad
    key: RegistrationState | lower
```

This would produce groups like:

* `cvad_unregistered` which holds all unregistered machines
* `cvad_26_07_0_39` which holds machines with that AgentVersion

#### Machine filtering

You can filter out unwanted machines by applying a `machine_filter`. Some examples:

```yaml
# inventory.cvad.yml
---
ddc_server: my-example-ddc.example.com
username: my-api-user
password: !vault |
  your-encrypted-password

# Only return machines matching a free-text search
machine_filter:
  BasicSearchString: "example.com"

# Filter by a specific property
machine_filter:
  SearchFilters:
    - Property: OSType
      Operator: ContainsLike
      Value: "linux"

# Combine filter groups with OR logic
machine_filter:
  SearchFilterGroups:
    - SearchFilterGroupType: Or
      SearchFilters:
        - Property: RegistrationState
          Operator: Contains
          Value: Unregistered
        - Property: RegistrationState
          Operator: Contains
          Value: AgentError
```

##### Tips on how to put together a filter

1. Apply the search in CVAD's webstudio.
2. Find the logging pane and then switch to the API tab, dig around there to find the API call that performed your search.
3. Adapt what you see there to a yaml structure like in the example above. (no need to include everything that the webstudio is doing, which for some reason makes "over complicated" requests.)
4. Run the inventory to see the result. 
```
ansible-inventory -i inventory.cvad.yml --graph --ask-vault-pass
```

Look at the plugin's docs to see which filter options are supported:
```
ansible-doc -t inventory nbeernink.cvad.cvad
```

### CVADClient (Module Utility)

The collection also includes a shared REST API helper (`CVADClient`) that handles authentication, request management, and error handling — making it easy to develop new modules without repeating boilerplate code.

---

## Installation

Install the collection from [Ansible Galaxy](https://galaxy.ansible.com/nbeernink/cvad):

```bash
ansible-galaxy collection install nbeernink.cvad
```

---

## Example Usage

### Put a machine in maintenance mode before patching

```yaml
- name: Place machine in maintenance mode
  nbeernink.cvad.machine_maintenancemode:
    ddc_server: my-ddc.example.com
    username: admin
    password: "{{ vault_password }}"
    machine_name: hostname.example.com
    state: on
```

### Register a physical machine into a Machine Catalog

```yaml
- name: Add machine to Machine Catalog
  nbeernink.cvad.machine_catalog_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: "{{ vault_password }}"
    machine_name: DOMAIN\hostname
    machine_catalog: RemotePC_Catalog
    state: present
```

### Assign a machine to a Delivery Group

```yaml
- name: Assign machine to Delivery Group
  nbeernink.cvad.delivery_group_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: "{{ vault_password }}"
    machine_name: my-machine.example.org
    delivery_group: RemotePC_DeliveryGroup
    state: present
```

# Using module defaults groups

This collection supports using [module defaults groups](https://docs.ansible.com/ansible/latest/user_guide/playbooks_module_defaults.html#module-defaults-groups) to reduce repeated module parameters in playbooks.

Example usage:

```yaml
---
- name: On-board new Citrix Remote PC
  gather_facts: false
  hosts: localhost

  module_defaults:
    group/nbeernink.cvad.cvad:
      ddc_server: my-ddc.example.org
      username: admin
      password: "{{ vault_password }}"

  tasks:
    - name: Add machine to Machine Catalog
      nbeernink.cvad.machine_catalog_machines:
        machine_name: EXAMPLE.ORG\my-machine
        machine_catalog: RemotePC_Catalog
        state: present

    - name: Assign machine to Delivery Group
      nbeernink.cvad.delivery_group_machines:
        machine_name: my-machine.example.org
        delivery_group: RemotePC_DeliveryGroup
        state: present

    - name: Assign user to Remote PC machine
      nbeernink.cvad.machine_user_assignment:
        machine_name: my-machine.example.org
        users:
          - j.doe@example.org
        state: present
```

---

## Roadmap

- [x] Assign/remove users for a given machine
- [ ] Control machine power state
- [ ] Create new Delivery Groups and Machine Catalogs
- [x] Add/remove machines from a Machine Catalog
- [x] Add/remove machines from a Delivery Group
- [x] Maintenance mode management
- [x] Dynamic inventory plugin
- [x] Automated linting / ansible-test

For testing, the goal is to eventually add recorded HTTP interaction tests using [vcrpy](https://vcrpy.readthedocs.io/), allowing the collection to be tested without a live CVAD environment by replaying pre-recorded API cassettes.

---

## License

This collection is licensed under the [GPL-3.0-or-later](LICENSE) license.
