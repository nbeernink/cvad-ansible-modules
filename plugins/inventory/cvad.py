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
      - constructed
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
      want_tags:
        description:
          - Group hosts by tags
        type: boolean
        default: True
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
                  ClientIP,
                  ClientName,
                  ClientVersion,
                  CloudPCProvisioningType,
                  ConnectedViaHostName,
                  ConnectedViaIP,
                  ConnectionProtocol,
                  ConnectorId,
                  ControllerDnsName,
                  CriticalIssues,
                  CurrentUser,
                  DeliveryGroup,
                  DnsName,
                  DrainingUntilShutdown,
                  FaultState,
                  FunctionalLevel,
                  HostedMachineName,
                  HostingServerName,
                  HypervisorConnection,
                  Id,
                  ImageOutOfDate,
                  InMaintenanceMode,
                  IsAssigned,
                  LastConnectionTime,
                  LastConnectionUser,
                  LastDeregistrationReason,
                  LastDeregistrationTime,
                  LaunchedViaHostName,
                  LaunchedViaIP,
                  LoadIndex,
                  MachineCatalog,
                  MachineName,
                  MachineUnavailableReason,
                  MaintenanceModeReason,
                  NonCriticalIssues,
                  OSType,
                  OSVersion,
                  PowerActionPending,
                  PowerState,
                  ProvisioningMaintenanceMode,
                  ProvisioningType,
                  PublishedName,
                  RegistrationState,
                  SecureIcaActive,
                  SessionCount,
                  SessionState,
                  SessionStateChangeTime,
                  SessionSupport,
                  SmartAccessFilters,
                  StartTime,
                  SummaryState,
                  SupportedPowerActions,
                  Tags,
                  Uid,
                  UserDisplayName,
                  UserName,
                  UserPrincipalName,
                  VdaUpgrade,
                  VdaUpgradeState,
                  WindowsConnectionSetting,
                  ZoneName,
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
                  Any,
                  Contains,
                  ContainsEndsWith,
                  ContainsLike,
                  ContainsStartsWith,
                  EndsWith,
                  Equals,
                  GreaterThan,
                  GreaterThanOrEquals,
                  In,
                  IsNotWithin,
                  IsWithin,
                  LessThan,
                  LessThanOrEquals,
                  Like,
                  None,
                  NotContains,
                  NotContainsEndsWith,
                  NotContainsLike,
                  NotContainsStartsWith,
                  NotEndsWith,
                  NotEquals,
                  NotIn,
                  NotLike,
                  NotStartsWith,
                  StartsWith,
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

  keyed_groups:
    - prefix: cvad
      key: AgentVersion

    # group by RegistrationState and lowercase the groupname
    - prefix: cvad
      key: RegistrationState | lower

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

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import (
    BaseInventoryPlugin,
    Cacheable,
    Constructable,
    to_safe_group_name
)
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient


class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
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
        strict = self.get_option('strict')
        group_prefix = self.get_option('group_prefix')
        want_tags = self.get_option('want_tags')
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
                host_name = machine['DnsName'].lower()
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

                # tags
                if want_tags:
                    for tag_name in machine.get('Tags', []):
                        tag_group = to_safe_group_name(
                            f"{group_prefix}tag_{tag_name}"
                        ).lower()
                        self.inventory.add_group(tag_group)
                        self.inventory.add_child(tag_group, host_name)

                # keyed groups
                keyed_groups_config = self.get_option('keyed_groups')

                if keyed_groups_config:
                    # FIXME: Probably not the best idea to directly map this
                    # but it seems to work
                    hostvars = machine

                    for key, val in hostvars.items():
                        self.inventory.set_variable(host_name, key, val)

                    self._add_host_to_keyed_groups(
                        keys=keyed_groups_config,
                        variables=hostvars,
                        host=host_name,
                        strict=strict
                    )

        except Exception as error:
            raise AnsibleParserError from error
