#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_modules.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_modules.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec

def run_module():
    module_args = base_argument_spec()
    module_args.update(
        machine_name=dict(
            type='str',
            required=True,
        )
    )

    result = dict(changed=False, message='')

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        cvad_client=CVADClient(**module.params)
        cvad_client.login()

        machine_info=cvad_client.get(f"/Machines/{module.params['machine_name']}")

        result['machine_info'] = machine_info

        module.exit_json(**result)

    except AssertionError as error:
        module.fail_json(msg=str(error))

if __name__ == '__main__':
    run_module()
