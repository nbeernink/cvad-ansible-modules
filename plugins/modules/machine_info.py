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
module: machine_info
author: "Niek Beernink (@nbeernink)"
short_description: Retrieve machine info for a Citrix machine
description:
  - This module gets machine info for a machine from Citrix REST API
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_name:
    description:
      - The name of the machine to fetch info for (usually fqdn)
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Get machineinfo
  nbeernink.cvad.machine_info:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
  register: machine_info

- debug:
    var: machine_info
"""

RETURN = r"""
machine_info:
  description: Machine info for the given machine
  returned: success
  type: dict
  elements: dict
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

        machine_info = cvad_client.get(f"/Machines/{machine_id}")

        module.exit_json(changed=False, machine_info=machine_info)

    except AssertionError as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
