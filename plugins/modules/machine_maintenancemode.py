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
module: machine_maintenancemode
author: "Niek Beernink (@nbeernink)"
short_description: Manage the maintenance mode for a machine
description:
  - This module can be used to manage maintenance mode for a machine
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_name:
    description:
      - The name of the machine to fetch info for (usually fqdn)
    type: str
    required: true
    aliases: ['name', 'machine']
  state:
    description:
      - If set to 'on', then place machine in maintenance mode.
      - If set to 'on' and machine is already in maintenance, no action is taken.
      - If set to 'off' and machine is in maintenance mode, exit maintenance mode
      - If set to 'off' and machine is not in maintenance mode, then no action is taken.
    choices: [ 'on', 'off' ]
    default: 'off'
    type: str
"""

EXAMPLES = r"""
- name: Put machine in maintenance mode
  nbeernink.cvad.machine_maintenancemode:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    state: on
"""

RETURN = r"""
machine_status:
  description: Action taken for machine
  returned: success
  type: dict
  sample: {
    "machine_status": "Machine 'hostname.example.com' entered maintenance mode"
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec


def run_module():
    module_args = base_argument_spec()
    module_args.update(
        machine_name=dict(
            type='str',
            required=True,
            aliases=['name', 'machine']
        ),
        state=dict(
            type='str',
            default='off',
            choices=['on', 'off'],
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        cvad_client = CVADClient(**module.params)

        machine_name = module.params['machine_name']
        machine_id = cvad_client.find_machine_id(machine_name)
        state = module.params['state']

        machine_info = cvad_client.get(f"/Machines/{machine_id}")

        if machine_info['InMaintenanceMode'] and state == 'off':
            if not module.check_mode:
                cvad_client.patch(
                    f"/Machines/{machine_id}",
                    data={'InMaintenanceMode': 'False'}
                )
            msg = f"Machine '{machine_name}' entered maintenance mode."
            changed = True

        elif state == 'on' and not machine_info['InMaintenanceMode']:
            if not module.check_mode:
                cvad_client.patch(
                    f"/Machines/{machine_id}",
                    data={'InMaintenanceMode': 'true'}
                )
            msg = f"Machine '{machine_name}' exited maintenance mode."
            changed = True

        else:
            msg = f"Machine '{machine_name}' maintenance mode is already {state}."
            changed = False

        module.exit_json(changed=changed, machine_status=msg)

    except AssertionError as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
