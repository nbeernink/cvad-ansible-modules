#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# nbeernink.cvad
# Copyright (C) 2026  Niek Beernink
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: machine_catalog_machines
author: "Niek Beernink (@nbeernink)"
short_description: Add or remove machine(s) in a machine catalog
description:
  - This module adds or removes a machine from a machine catalog
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_catalog:
    description:
      - The name of the machine catalog to add the machine to
    type: str
    required: true
  machine_name:
    description:
      - The Active Directory account name of the machine to add or remove (e.g., DOMAIN\NETBIOSNAME captialized)
    type: str
    required: true
  state:
    description:
      - V(present) will add a machine to the given machine catalog
      - V(absent) will remove a machine from the given machine catalog
    choices: ['absent','present']
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Add machine to machine catalog
  nbeernink.cvad.machine_catalog_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: DOMAIN\MACHINENAME
    machine_catalog: my_awesome_catalog
    state: present

- name: Remove machine from machine catalog
  nbeernink.cvad.machine_catalog_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: DOMAIN\MACHINENAME
    machine_catalog: my_awesome_catalog
    state: absent
"""

RETURN = r"""
msg:
  description: Status message showing if the machine was added or removed from the machine catalog
  returned: success
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec


def run_module():
    module_args = base_argument_spec()

    module_args.update(
        machine_catalog=dict(
            type='str',
            required=True
        ),
        machine_name=dict(
            type='str',
            required=True
        ),
        state=dict(
            type='str',
            required=True,
            choices=['absent', 'present']
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        cvad_client = CVADClient(**module.params)
        cvad_client.login()

        # variable re-assignment
        catalog_name = module.params['machine_catalog']
        machine_name = module.params['machine_name']
        state = module.params['state']

        # Getting Catalog ID
        catalog_id = cvad_client.find_machine_catalog_by_id(catalog_name)

        # Get list of machines in machine catalog
        machines = cvad_client.get(f"/MachineCatalogs/{catalog_id}/Machines")

        # Check if machine is already in catalog
        # The API typically returns Name (which is DOMAIN\MACHINENAME)
        machine_in_catalog = False
        machine_id = None

        for machine in machines:
            if machine.get('Name', '').lower() == machine_name.lower():
                machine_in_catalog = True
                machine_id = machine.get('Id')
                break

        if state == 'absent' and machine_in_catalog:
            if not module.check_mode:
                cvad_client.delete(
                    f"/MachineCatalogs/{catalog_id}/Machines/{machine_id}"
                )
                msg = f"Removed {machine_name} from {catalog_name}"
                changed = True
            else:
                msg = f"Would remove {machine_name} from {catalog_name}"
                changed = True

        elif state == 'present' and not machine_in_catalog:
            if not module.check_mode:
                cvad_client.post(
                    f"/MachineCatalogs/{catalog_id}/Machines",
                    data={
                        "MachineName": machine_name
                    }
                )
                msg = f"Added {machine_name} to {catalog_name}"
                changed = True
            else:
                msg = f"Would add {machine_name} to {catalog_name}"
                changed = True

        else:
            msg = f"Machine '{machine_name}' is already {state} in machine-catalog '{catalog_name}'"
            changed = False

        module.exit_json(changed=changed, msg=msg)

    except AssertionError as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
