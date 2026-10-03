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
      machine_filter:
        description:
          - A search filter dict passed to the C(/Machines/$search) API endpoint.
          - Exactly one of C(BasicSearchString), C(SearchFilters), or
            C(SearchFilterGroups) must be provided. These modes are mutually
            exclusive because each triggers a different type of search.
        type: dict
        suboptions:
          BasicSearchString:
            description: Free-text string matched against machine properties.
            type: str
          SearchFilters:
            description: List of property filters combined with AND logic.
            type: list
            elements: dict
            suboptions:
              Property:
                description: The machine property to filter on (e.g. V(OSType)).
                type: str
                required: true
                choices: [
                  AgentVersion,
                  AllocationType,
                  AppState,
                  AppsInUse,
                  AzureAdJoinedMode,
                  ControllerDnsName,
                  ClientIP,
                  ClientName,
                  CloudPCProvisioningType,
                  ConnectedViaHostName,
                  ConnectedViaIP,
                  HypervisorConnection,
                  ConnectionProtocol,
                  CurrentUser,
                  DeliveryGroup,
                  FaultState,
                  IsAssigned,
                  LastConnectionUser,
                  LastConnectionTime,
                  LastDeregistrationReason,
                  LastDeregistrationTime,
                  LaunchedViaHostName,
                  LaunchedViaIP,
                  PublishedName,
                  LoadIndex,
                  StartTime,
                  MachineCatalog,
                  MachineUnavailableReason,
                  InMaintenanceMode,
                  MaintenanceModeReason,
                  DrainingUntilShutdown,
                  MachineName,
                  OSType,
                  OSVersion,
                  ImageOutOfDate,
                  PowerActionPending,
                  ClientVersion,
                  PowerState,
                  SupportedPowerActions,
                  RegistrationState,
                  SecureIcaActive,
                  HostingServerName,
                  SessionCount,
                  SessionStateChangeTime,
                  SessionState,
                  SessionSupport,
                  SmartAccessFilters,
                  SummaryState,
                  Tags,
                  UserPrincipalName,
                  UserName,
                  UserDisplayName,
                  HostedMachineName,
                  WindowsConnectionSetting,
                  FunctionalLevel,
                  DnsName,
                  Uid,
                  Id,
                  VdaUpgrade,
                  VdaUpgradeState,
                  ProvisioningType,
                  ZoneName,
                  CriticalIssues,
                  NonCriticalIssues,
                  ProvisioningMaintenanceMode,
                  ConnectorId,
                ]
              Value:
                description: The value to compare against.
                type: str
                required: true
              Operator:
                description: Comparison operator.
                type: str
                required: true
                choices: [
                  Equals,
                  NotEquals,
                  LessThan,
                  GreaterThan,
                  LessThanOrEquals,
                  GreaterThanOrEquals,
                  Like,
                  NotLike,
                  EndsWith,
                  NotEndsWith,
                  StartsWith,
                  NotStartsWith,
                  Any,
                  None,
                  Contains,
                  NotContains,
                  ContainsLike,
                  NotContainsLike,
                  ContainsEndsWith,
                  NotContainsEndsWith,
                  ContainsStartsWith,
                  NotContainsStartsWith,
                  In,
                  NotIn,
                  IsWithin,
                  IsNotWithin,
                ]
          SearchFilterGroups:
            description: >
              List of filter group objects. Each group may contain its own
              C(SearchFilters), a C(SearchFilterGroupType) C(And)|C(Or),
              and nested SearchFilterGroups for arbitrary depth.
            type: list
            elements: dict
'''

EXAMPLES = '''
  # my-example-ddc.cvad.yml
  plugin: nbeernink.cvad.cvad
  ddc_server: my-example-ddc.example.com
  username: my-api-user
  password: changeme

  # Only return machines matching a free-text search
  machine_filter:
    BasicSearchString: "example.com"

  # Filter by a specific property
  machine_filter:
    SearchFilters:
      - Property: OSType
        Operator: ContainsLike
        Value: "linux"

  # Combine filter groups with OR logic
  machine_filter:
    SearchFilterGroups:
      - SearchFilterGroupType: Or
        SearchFilters:
          - Property: RegistrationState
            Operator: Contains
            Value: Unregistered
          - Property: RegistrationState
            Operator: Contains
            Value: AgentError
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
        machine_filter = self.get_option('machine_filter')

        try:
            cvad_client = CVADClient(
                ddc_server=ddc_server,
                username=username,
                password=password,
                validate_certs=validate_certs
            )
            cvad_client.login()

            if machine_filter is not None:
                all_machines = cvad_client.post(
                    "/Machines/$search",
                    machine_filter
                )
            else:
                all_machines = cvad_client.get('/Machines')

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
