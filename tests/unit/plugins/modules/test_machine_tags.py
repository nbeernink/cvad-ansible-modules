from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.machine_tags import run_module


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_tags_add.yaml")
def test_machine_tags_add(
    cvad_connection_args,
    cvad_test_machine1,
    cvad_test_tag1,
    cvad_test_tag2,
    run_ansible_module,
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "tags": [cvad_test_tag1, cvad_test_tag2],
            "state": "present",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert (
        f"attached tag(s) '{cvad_test_tag1}', '{cvad_test_tag2}'"
        in result.get("msg", "")
    )


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_tags_remove.yaml")
def test_machine_tags_remove(
    cvad_connection_args, cvad_test_machine1, cvad_test_tag2, run_ansible_module
):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_name": cvad_test_machine1,
            "tags": [cvad_test_tag2],
            "state": "absent",
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert result.get("changed")
    assert f"detached tag(s) '{cvad_test_tag2}'" in result.get("msg", "")
