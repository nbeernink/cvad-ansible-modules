from __future__ import absolute_import, division, print_function

__metaclass__ = type

import tempfile
import pytest
import yaml
from ansible.inventory.data import InventoryData
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.loader import inventory_loader


def test_verify_file():
    plugin = inventory_loader.get("nbeernink.cvad.cvad")
    with tempfile.NamedTemporaryFile("w+", suffix="cvad.yml") as tf_valid, \
         tempfile.NamedTemporaryFile("w+", suffix="hosts.ini") as tf_invalid:
        assert plugin.verify_file(tf_valid.name)
        assert not plugin.verify_file(tf_invalid.name)


@pytest.mark.vcr
@pytest.mark.default_cassette("inventory_cvad.yaml")
def test_inventory_parse(
    cvad_connection_args,
    cvad_test_machine1,
    cvad_test_machine2,
    cvad_test_delivery_group,
    cvad_test_machine_catalog,
    cvad_test_tag1,
):
    config_data = {
        "plugin": "nbeernink.cvad.cvad",
        "ddc_server": cvad_connection_args["ddc_server"],
        "username": cvad_connection_args["username"],
        "password": cvad_connection_args["password"],
        "validate_certs": cvad_connection_args["validate_certs"],
        "group_prefix": "cvad_",
        "want_tags": True,
        "keyed_groups": [
            {
                "prefix": "cvad",
                "key": "PowerState | lower",
            }
        ],
    }

    with tempfile.NamedTemporaryFile("w+", suffix="cvad.yml") as tf:
        yaml.dump(config_data, tf)
        tf.flush()

        inventory = InventoryData()
        loader = DataLoader()
        plugin = inventory_loader.get("nbeernink.cvad.cvad")
        plugin.parse(inventory, loader, tf.name, cache=False)

        # Assert hosts were added
        assert cvad_test_machine1 in inventory.hosts
        assert cvad_test_machine2 in inventory.hosts

        # Assert maintenance mode group
        assert "cvad_in_maintenancemode" in inventory.groups
        maintenance_hosts = inventory.groups["cvad_in_maintenancemode"].get_hosts()
        maintenance_host_names = [h.name for h in maintenance_hosts]
        assert cvad_test_machine2 in maintenance_host_names
        assert cvad_test_machine1 not in maintenance_host_names

        # Assert tag groups
        assert f"cvad_tag_{cvad_test_tag1.lower()}" in inventory.groups

        # Assert delivery group and catalog groups
        dg_group = f"cvad_deliverygroup_{cvad_test_delivery_group.replace('-', '_')}"
        mc_group = f"cvad_machinecatalog_{cvad_test_machine_catalog.replace('-', '_')}"
        assert dg_group in inventory.groups
        assert mc_group in inventory.groups

        # Assert keyed groups
        assert "cvad_unmanaged" in inventory.groups
