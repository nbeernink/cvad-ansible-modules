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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: machine_user_assignment
author: "Niek Beernink (@nbeernink)"
short_description: Manage user assignments for a specific machine
description:
  - This module assigns or removes user mappings for individual dedicated machines.
extends_documentation_fragment: nbeernink.cvad.common_cvad
options:
  machine_name:
    description:
      - The name (SAMName or DnsName) of the machine to configure.
    type: str
    required: true
  users:
    description:
      - A list of user identities to assign or remove. In the form of DOMAIN\samaccountname or User Principal Name (j.doe@example.org).
      - Required when V(state=present).
      - Optional when V(state=absent). If omitted or empty when V(state=absent), all assigned users will be unassigned from the machine.
    type: list
    elements: str
    required: false
  state:
    description:
      - V(present) will ensure the specified user(s) are assigned to the machine without removing existing users.
      - V(absent) will ensure the specified user(s) are unassigned from the machine, or all users if O(users) is omitted.
    choices: ['absent', 'present']
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Assign a single user to a machine
  nbeernink.cvad.machine_user_assignment:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    users:
      - j.doe@example.org
    state: present

- name: Assign multiple users to a machine
  nbeernink.cvad.machine_user_assignment:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    users:
      - j.doe@example.org
      - m.smith@example.org
    state: present

- name: Unassign a specific user from a machine
  nbeernink.cvad.machine_user_assignment:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    users:
      - j.doe@example.org
    state: absent

- name: Unassign all users from a machine
  nbeernink.cvad.machine_user_assignment:
    ddc_server: my-ddc.example.com
    username: admin
    password: hunter2
    machine_name: hostname.example.com
    state: absent
"""

RETURN = r"""
msg:
  description: Status message showing the action taken.
  returned: success
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
            required=True
        ),
        users=dict(
            type='list',
            elements='str',
            required=False,
            default=None
        ),
        state=dict(
            type='str',
            required=True,
            choices=['absent', 'present']
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['users'])
        ]
    )

    try:
        cvad_client = CVADClient(**module.params)
        cvad_client.login()

        machine_name = module.params['machine_name']
        raw_users = module.params['users']
        state = module.params['state']

        # Parse target users
        target_users = []
        if raw_users is not None:
            target_users = [u.strip() for u in raw_users if isinstance(u, str) and u.strip()]

        # Look up target machine unique id
        machine_id = cvad_client.find_machine_id(machine_name)

        # Get existing details
        machine_details = cvad_client.get(f"/Machines/{machine_id}")
        assigned_user_objs = machine_details.get('AssignedUsers') or []

        if state == 'present':
            # Identify missing target users
            users_to_add = [
                tu for tu in target_users
                if not any(CVADClient.matches_user(tu, existing) for existing in assigned_user_objs)
            ]

            if not users_to_add:
                changed = False
                msg = f"All specified user(s) ({', '.join(target_users)}) are already assigned to machine '{machine_name}'"
            else:
                changed = True
                updated_assigned_users = [
                    CVADClient.get_user_identity_string(existing) for existing in assigned_user_objs
                ]
                for tu in users_to_add:
                    if not any(tu.lower() == existing_str.lower() for existing_str in updated_assigned_users):
                        updated_assigned_users.append(tu)

                if not module.check_mode:
                    cvad_client.patch(
                        f"/Machines/{machine_id}",
                        data={"AssignedUsers": updated_assigned_users}
                    )
                    msg = f"Assigned user(s) ({', '.join(users_to_add)}) to machine '{machine_name}'"
                else:
                    msg = f"Would assign user(s) ({', '.join(users_to_add)}) to machine '{machine_name}'"

        elif state == 'absent':
            if not target_users:
                # Bulk removal: remove all assigned users
                if assigned_user_objs:
                    changed = True
                    if not module.check_mode:
                        cvad_client.patch(
                            f"/Machines/{machine_id}",
                            data={"AssignedUsers": []}
                        )
                        msg = f"Removed all user assignments from machine '{machine_name}'"
                    else:
                        msg = f"Would remove all user assignments from machine '{machine_name}'"
                else:
                    changed = False
                    msg = f"Machine '{machine_name}' has no assigned users"
            else:
                # Targeted removal
                users_to_remove = []
                remaining_assigned_objs = []
                for existing in assigned_user_objs:
                    matched_target = None
                    for tu in target_users:
                        if CVADClient.matches_user(tu, existing):
                            matched_target = tu
                            break
                    if matched_target:
                        users_to_remove.append(CVADClient.get_user_identity_string(existing))
                    else:
                        remaining_assigned_objs.append(existing)

                if not users_to_remove:
                    changed = False
                    msg = f"None of the specified user(s) ({', '.join(target_users)}) are assigned to machine '{machine_name}'"
                else:
                    changed = True
                    updated_assigned_users = [
                        CVADClient.get_user_identity_string(existing) for existing in remaining_assigned_objs
                    ]

                    if not module.check_mode:
                        cvad_client.patch(
                            f"/Machines/{machine_id}",
                            data={"AssignedUsers": updated_assigned_users}
                        )
                        msg = f"Removed assignment for user(s) ({', '.join(users_to_remove)}) from machine '{machine_name}'"
                    else:
                        msg = f"Would remove assignment for user(s) ({', '.join(users_to_remove)}) from machine '{machine_name}'"

        module.exit_json(changed=changed, msg=msg)

    except Exception as error:
        module.fail_json(msg=str(error))


if __name__ == '__main__':
    run_module()
