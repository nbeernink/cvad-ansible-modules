from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.delivery_group_machines import (
    run_module,
)


@pytest.mark.vcr
@pytest.mark.default_cassette("delivery_group_machines_present.yaml")
def test_delivery_group_machines_present(
    cvad_connection_args,
    cvad_test_delivery_group,
    cvad_test_machine1,
    run_ansible_module,
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "delivery_group": cvad_test_delivery_group,
            "machine": cvad_test_machine1,
            "state": "present",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert (
        f"Added {cvad_test_machine1} to {cvad_test_delivery_group}"
        in result.get("msg", "")
    )


@pytest.mark.vcr
@pytest.mark.default_cassette("delivery_group_machines_absent.yaml")
def test_delivery_group_machines_absent(
    cvad_connection_args,
    cvad_test_delivery_group,
    cvad_test_machine1,
    run_ansible_module,
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "delivery_group": cvad_test_delivery_group,
            "machine": cvad_test_machine1,
            "state": "absent",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert (
        f"Removed {cvad_test_machine1} from {cvad_test_delivery_group}"
        in result.get("msg", "")
    )
