#!/usr/bin/python
# -*- coding: utf-8 -*-
DOCUMENTATION = r"""
---
module: machine_catalog_info
author: "Niek Beernink (@nbeernink)"
short_description: Get information for machine catalog(s)
description:
  - This module gets machine catalog info for one or more catalogs
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_catalog:
    description:
      - The name of the catalog to get info for
    type: str
    required: false
  fields:
    description:
      - A list of fields to return. If not specified returns all fields
    type: list
"""

EXAMPLES = r"""
- name: Get machine catalog info
  nbeernink.cvad.machine_catalog_info:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    machine_catalog: my_machine_catalog
  register: machine_catalog_info

- name: Get count of unassigned machines for all machine catalogs
  nbeernink.cvad.machine_catalog_info:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    fields:
      - UnassignedMachines
  register: machine_catalog_info
"""

RETURN = r"""
machine_catalog_info:
 description: Machine catalog info
 returned: success
 type: dict
 elements: dict
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec

def run_module():
    module_args = base_argument_spec()
    module_args.update(
        machine_catalog=dict(
            type='str',
        ),
        fields=dict(
            type='list',
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        cvad_client=CVADClient(**module.params)
        cvad_client.login()

        catalog_name = module.params['machine_catalog']
        catalog_id = cvad_client.find_machine_catalog_by_id(catalog_name)

        # Return field handling
        return_fields = ''
        if module.params['fields']:
            delimiter = ','
            return_fields = delimiter.join(module.params['fields'])

        if catalog_name:
            machine_catalog_info=cvad_client.get(
                f"/MachineCatalogs/{catalog_id}?fields={return_fields}"
            )
        else:
            machine_catalog_info=cvad_client.get(
                f"/MachineCatalogs?fields={return_fields}"
            )['Items']

        module.exit_json(changed=False,machine_catalog_info=machine_catalog_info)

    except AssertionError as error:
        module.fail_json(msg=str(error))

if __name__ == '__main__':
    run_module()
