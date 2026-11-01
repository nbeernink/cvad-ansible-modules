#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# nbeernink.cvad
# Copyright (C) 2026  Niek Beernink
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
module: machine_tags
author: "Niek Beernink (@nbeernink)"
short_description: Manage tags on a machine
description:
  - Attach or detach tags on a machine.
  - Remove unmanaged tags when O(remove_extra_tags) is specified.
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_name:
    description:
      - The name of the machine to manage tags for (usually fqdn).
    type: str
    required: true
  tags:
    description:
      - List of tag names to attach or detach. Matching is case-sensitive.
      - Required when V(state=present), ensures all listed tags are attached.
      - When V(state=absent), detaches the listed tags. If omitted, all attached tags are removed.
    type: list
    elements: str
    required: false
    default: null
  state:
    description:
      - V(present) ensures the listed tags are attached to the machine.
      - V(absent) ensures the listed tags are detached, or all tags if O(tags) is omitted.
    choices: ['absent', 'present']
    default: present
    type: str
  remove_extra_tags:
    description:
      - When V(true) and V(state=present), removes any tag directly attached to the machine that is not in O(tags).
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: Attach tags to a machine
  nbeernink.cvad.machine_tags:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    tags:
      - Production
      - GPU
    state: present

- name: Ensure only specified tags are attached (remove all others)
  nbeernink.cvad.machine_tags:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    tags:
      - Production
    state: present
    remove_extra_tags: true

- name: Detach a specific tag from a machine
  nbeernink.cvad.machine_tags:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    tags:
      - GPU
    state: absent

- name: Detach all tags from a machine
  nbeernink.cvad.machine_tags:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    state: absent
"""

RETURN = r"""
msg:
  description: Status message describing the action taken.
  returned: always
  type: str
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
        ),
        tags=dict(
            type='list',
            elements='str',
            required=False,
            default=None
        ),
        state=dict(
            type='str',
            default='present',
            choices=['absent', 'present']
        ),
        remove_extra_tags=dict(
            type='bool',
            default=False,
        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['tags'])
        ]
    )

    try:
        cvad_client = CVADClient(**module.params)
        cvad_client.login()

        machine_name = module.params['machine_name']
        tags = module.params['tags'] or []
        state = module.params['state']
        remove_extra_tags = module.params['remove_extra_tags']

        machine_id = cvad_client.find_machine_id(machine_name)

        all_site_tags = cvad_client.get('/Tags?fields=Name,Id')
        site_tags_by_name = {tag['Name']: tag for tag in all_site_tags}

        # Match requested tags by name with tags available in the site (case-sensitive)
        desired_tags = []
        for tag_name in tags:
            tag = site_tags_by_name.get(tag_name)
            if not tag:
                raise AssertionError(f"Tag '{tag_name}' does not exist on the CVAD site")
            desired_tags.append(tag)

        current_tags = cvad_client.get(f"/Machines/{machine_id}/Tags")
        current_tag_ids = {t['Id'] for t in current_tags}
        desired_tag_ids = {t['Id'] for t in desired_tags}

        tags_to_add = []
        tags_to_remove = []

        if state == 'present':
            tags_to_add = [
                tag for tag in desired_tags
                if tag['Id'] not in current_tag_ids
            ]
            if remove_extra_tags:
                tags_to_remove = [
                    tag for tag in current_tags
                    if tag['Id'] not in desired_tag_ids
                ]
        elif state == 'absent':
            if tags:
                tags_to_remove = [
                    tag for tag in desired_tags
                    if tag['Id'] in current_tag_ids
                ]
            else:
                tags_to_remove = list(current_tags)

        if not tags_to_add and not tags_to_remove:
            module.exit_json(
                changed=False,
                msg=f"Tags on machine '{machine_name}' are already in the desired state"
            )

        if not module.check_mode:
            for tag in tags_to_add:
                cvad_client.post(f"/Machines/{machine_id}/Tags/{tag['Id']}")
            for tag in tags_to_remove:
                cvad_client.delete(f"/Machines/{machine_id}/Tags/{tag['Id']}")

        def format_action(action, tag_list):
            tag_names = [f"'{t['Name']}'" for t in tag_list]
            return f"{action} tag(s) {', '.join(tag_names)}"

        msg_parts = []
        if tags_to_add:
            msg_parts.append(format_action("attached", tags_to_add))
        if tags_to_remove:
            msg_parts.append(format_action("detached", tags_to_remove))

        prefix = "Would have" if module.check_mode else "Successfully"
        msg = f"{prefix} {' and '.join(msg_parts)} on machine '{machine_name}'"

        module.exit_json(changed=True, msg=msg)

    except Exception as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
