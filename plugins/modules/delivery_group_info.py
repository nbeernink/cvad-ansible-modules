#!/usr/bin/python
# -*- coding: utf-8 -*-
DOCUMENTATION = r"""
---
module: delivery_group_info
author: "Niek Beernink (@nbeernink)"
short_description: Get information for delivery group(s)
description:
  - This module gets delivery group info for one or more groups, if no group is specified, all groups are returned
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  delivery_group:
    description:
      - The name of the catalog to get info for
    type: str
    required: false
  fields:
    description:
      - A list of fields to return. If not specified, returns all fields
    type: list
"""

EXAMPLES = r"""
- name: Get all delivery groups
  nbeernink.cvad.delivery_group_info:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
  register: delivery_group_info

- name: Get specific fields for specific delivery group
  nbeernink.cvad.delivery_group_info:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    delivery_group: my_fancy_delivery_group
    fields:
      - FullName
      - Id
  register: my_fancy_delivery_group_info
"""

RETURN = r"""
delivery_groups:
  description: requested delivery group info
  returned: success
  type: list or dict
  elements: dict
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec

def run_module():
    module_args = base_argument_spec()

    module_args.update(
        delivery_group=dict(
            type='str',
            fallback=(env_fallback, ["CVAD_MACHINE_CATALOG_NAME"]),
        ),
        search=dict(
            type='str',
            fallback=(env_fallback, ["CVAD_MACHINE_CATALOG_SEARCH"]),
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

        group_name = module.params['delivery_group']

        group_id = cvad_client.find_delivery_group_by_id(group_name)

        # Return field handling
        return_fields = ''
        if module.params['fields']:
            delimiter = ','
            return_fields = delimiter.join(module.params['fields'])

        if group_name:
            delivery_group_info=cvad_client.get(
                f"/DeliveryGroups/{group_id}?fields={return_fields}"
            )
        else:
            delivery_group_info=cvad_client.get(
                f"/DeliveryGroups?fields={return_fields}"
            )['Items']

        module.exit_json(changed=False,delivery_group_info=delivery_group_info)

    except AssertionError as error:
        module.fail_json(msg=str(error))

if __name__ == '__main__':
    run_module()
