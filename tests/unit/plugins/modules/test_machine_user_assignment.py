from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.machine_user_assignment import (
    run_module,
)


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_user_assignment_present.yaml")
def test_machine_user_assignment_present(
    cvad_connection_args,
    cvad_test_machine1,
    cvad_test_user1,
    cvad_test_user2,
    run_ansible_module,
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "users": [cvad_test_user1, cvad_test_user2],
            "state": "present",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert (
        f"Assigned user(s) ({cvad_test_user2}) to machine '{cvad_test_machine1}'"
        in result.get("msg", "")
    )


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_user_assignment_absent.yaml")
def test_machine_user_assignment_absent(
    cvad_connection_args, cvad_test_machine1, run_ansible_module
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "state": "absent",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert (
        f"Removed all user assignments from machine '{cvad_test_machine1}'"
        in result.get("msg", "")
    )
