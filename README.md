# CVAD Ansible Modules

[![CI](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/ansible-test.yml/badge.svg)](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/ansible-test.yml)
[![CodeQL](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/nbeernink/cvad-ansible-modules/actions/workflows/github-code-scanning/codeql)

An Ansible collection for managing the lifecycle of machines in [Citrix Virtual Apps and Desktops (CVAD)](https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/overview) environments — specifically tailored for organizations **not using Machine Creation Services (MCS)**.

---

## Who is this for?

Citrix provides **Machine Creation Services (MCS)** as a way to provision and manage virtual machines automatically. However, many organizations rely on **physical machines** or **manually provisioned VMs** — for example, environments running **Citrix Remote PC Access**.

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

### Ansible Inventory Plugin

This collection includes an inventory plugin (`nbeernink.cvad.cvad`) that dynamically builds your Ansible inventory from your DDC (Desktop Delivery Controller) environment. Machines are automatically grouped by:

- Delivery Group
- Machine Catalog
- Maintenance mode status

Planned improvements:
- Host filters
- Grouping of unregistered machines (e.g., machines that should be registered but aren't)
- Keyed groups (custom query-based grouping)

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

---

## Roadmap

- [ ] Assign/remove users for a given machine
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
