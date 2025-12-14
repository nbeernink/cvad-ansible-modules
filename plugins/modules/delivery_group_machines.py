#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# nbeernink.cvad
# Copyright (C) 2025  Niek Beernink
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
module: delivery_group_machines
author: "Niek Beernink (@nbeernink)"
short_description: Add or remove machine(s) in a delivery group
description:
  - This module adds or removes a machine from a delivery group
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  delivery_group:
    description:
      - The name of the delivery group to add the machine to
    type: str
    required: true
  machine:
    description:
      - The name of the machine to add or remove
    type: str
    required: true
  state:
    description:
      - V(present) will add a machine from the given delivery group
      - V(absent) will remove a machine from the given delivery group
    choices: ['absent','present']
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Add machine to delivery group
  nbeernink.cvad.delivery_group_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine: hostname.example.com
    delivery_group: my_awesome_group
    state: present

- name: Remove machine from delivery group
  nbeernink.cvad.delivery_group_machines:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine: hostname.example.com
    delivery_group: my_awesome_group
    state: absent
"""

RETURN = r"""
msg:
  description: Status message showing if the machine was added or removed from the delivery group
  returned: success
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec


def run_module():
    module_args = base_argument_spec()

    module_args.update(
        delivery_group=dict(
            type='str',
            required=True
        ),
        machine=dict(
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
        group_name = module.params['delivery_group']
        machine_name = module.params['machine']
        state = module.params['state']

        # Getting ID's
        delivery_group_id = cvad_client.find_delivery_group_by_id(group_name)

        machine_id = cvad_client.find_machine_id(machine_name)

        machine_catalog_id = cvad_client.find_machine_catalog_id_for_machine(machine_name)

        # Get list of machines in delivery group
        machines = cvad_client.get(f"/DeliveryGroups/{group_name}/Machines")

        # Check if machine is already in catalog
        machine_in_catalog = any(
            machine['DnsName'] == machine_name for machine in machines
        )

        if state == 'absent' and machine_in_catalog:
            if not module.check_mode:
                cvad_client.delete(
                    f"/DeliveryGroups/{delivery_group_id}/Machines/{machine_id}"
                )
                msg = f"Removed {machine_name} from {group_name}"
                changed = True
            else:
                msg = f"Would remove {machine_name} from {group_name}"
                changed = True

        elif state == 'present' and not machine_in_catalog:
            if not module.check_mode:
                cvad_client.post(
                    f"/DeliveryGroups/{delivery_group_id}/Machines",
                    data={
                        "MachineCatalog": machine_catalog_id,
                        "AssignMachinesToUsers": [
                            {"Machine": machine_id}
                        ]
                    }
                )
                msg = f"Added {machine_name} to {group_name}"
                changed = True
            else:
                msg = f"Would add {machine_name} to {group_name}"
                changed = True

        else:
            msg = f"Machine '{machine_name}' is already {state} in delivery-group '{group_name}'"
            changed = False

        module.exit_json(changed=changed, msg=msg)

    except AssertionError as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
