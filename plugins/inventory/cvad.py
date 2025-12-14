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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: cvad
    short_description: Citrix Virtual Apps & Desktops inventory.
    description:
        - Get inventory hosts from the CItrix Delivery Controller.
        - Uses a YAML configuration file ending with ``cvad.(yaml|yml)``.
    extends_documentation_fragment:
      - inventory_cache
    options:
      plugin:
        description: Tells ansible to read this file as a C(CVAD) plugin.
        required: True
        choices: ['nbeernink.cvad.cvad']
      ddc_server:
        description:
          - The address of the Desktop Delivery Controller.
        required: True
      username:
        description:
          - Username that will be connecting to the API.
        required: True
      password:
        description:
          - Password of the user connecting to the API.
        required: True
      validate_certs:
        description:
          - Validate certificates or not.
        type: boolean
        default: True
      group_prefix:
        description:
          - prefix to apply to cvad groups
        default: cvad_
'''

EXAMPLES = '''
  # my-example-ddc.cvad.yml
  plugin: nbeernink.cvad.cvad
  ddc_server: my-example-ddc.example.com
  username: my-api-user
  password: changeme
'''

from ansible.errors import AnsibleError
from ansible.plugins.inventory import (
    BaseInventoryPlugin,
    Cacheable,
    to_safe_group_name
)
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient


class InventoryModule(BaseInventoryPlugin, Cacheable):
    """
    Host inventory parser for ansible using Citrix Delivery Controller as source.
    """

    NAME = 'nbeernink.cvad.cvad'

    def __init__(self):

        super().__init__()
        self.cache_key = None
        self.use_cache = None

    def verify_file(self, path):
        """
        return true/false if this is possibly a valid file for this plugin to consume
        Args:
            path: Path of YAML config file
        Returns: True if file extension is correct, else false
        """

        if super().verify_file(path):
            if path.endswith(('cvad.yaml', 'cvad.yml')):
                return True
            self.display.vvv(
                'Skipping due to inventory source not ending in right extension'
            )
        return False

    def parse(self, inventory, loader, path, cache=True):
        """
        Parse the inventory file
        """

        super().parse(inventory, loader, path)

        config = self._read_config_data(path)
        self._consume_options(config)

        ddc_server = self.get_option('ddc_server')
        password = self.get_option('password')
        username = self.get_option('username')
        validate_certs = self.get_option('validate_certs')
        group_prefix = self.get_option('group_prefix')

        try:
            cvad_client = CVADClient(
                ddc_server=ddc_server,
                username=username,
                password=password,
                validate_certs=validate_certs
            )

            cvad_client.login()

            all_machines = cvad_client.get(
                "/Machines/?fields="
                "DeliveryGroup,"
                "DnsName,"
                "InMaintenanceMode,"
                "MachineCatalog,"
                "MachineType,"
                "PowerState"
            )

            maintenance_group = f"{group_prefix}in_maintenancemode"
            self.inventory.add_group(maintenance_group)

            for machine in all_machines:
                host_name = machine['DnsName']
                self.inventory.add_host(host_name)

                if machine['InMaintenanceMode']:
                    self.inventory.add_child(maintenance_group, host_name)

                # value based groups
                for group in ['PowerState', 'MachineType']:
                    state = machine[group]
                    group_name = to_safe_group_name(f"{group_prefix}{group}_{state}").lower()
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, host_name)

                # nested group names
                for group in ['DeliveryGroup', 'MachineCatalog']:

                    if machine.get(f"{group}"):
                        group_name = machine.get(f"{group}", {}).get('Name')
                        group_name = to_safe_group_name(
                            f"{group_prefix}{group}_{group_name}"
                        ).lower()
                        self.inventory.add_group(group_name)
                        self.inventory.add_child(group_name, host_name)

        except Exception as error:
            raise AnsibleError from error
