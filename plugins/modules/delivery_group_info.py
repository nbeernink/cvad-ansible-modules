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
    elements: str
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
  type: list
  elements: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient
from ansible_collections.nbeernink.cvad.plugins.module_utils.base_argument_spec import base_argument_spec


def run_module():
    module_args = base_argument_spec()

    module_args.update(
        delivery_group=dict(
            type='str',
        ),
        fields=dict(
            type='list',
            elements='str'
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        cvad_client = CVADClient(**module.params)
        cvad_client.login()

        group_name = module.params['delivery_group']

        group_id = cvad_client.find_delivery_group_by_id(group_name)

        # Return field handling
        return_fields = ''
        if module.params['fields']:
            delimiter = ','
            return_fields = delimiter.join(module.params['fields'])

        if group_name:
            delivery_group_info = cvad_client.get(
                f"/DeliveryGroups/{group_id}?fields={return_fields}"
            )
        else:
            delivery_group_info = cvad_client.get(
                f"/DeliveryGroups?fields={return_fields}"
            )

        module.exit_json(changed=False, delivery_group_info=delivery_group_info)

    except AssertionError as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
