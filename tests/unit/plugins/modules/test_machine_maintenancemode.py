from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.machine_maintenancemode import (
    run_module,
)


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_maintenancemode_on.yaml")
def test_machine_maintenancemode_on(
    cvad_connection_args, cvad_test_machine1, run_ansible_module
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "state": "on",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert "entered maintenance mode" in result.get("machine_status", "")


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_maintenancemode_off.yaml")
def test_machine_maintenancemode_off(
    cvad_connection_args, cvad_test_machine1, run_ansible_module
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "state": "off",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert "exited maintenance mode" in result.get("machine_status", "")
