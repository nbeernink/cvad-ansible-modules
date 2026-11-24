from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.machine_catalog_info import (
    run_module,
)


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_catalog_info.yaml")
def test_machine_catalog_info_specific(cvad_connection_args, run_ansible_module):
    args = dict(cvad_connection_args)
    args["machine_catalog"] = "ansible_testing"
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert not result.get("changed")
    assert "machine_catalog_info" in result
    assert result["machine_catalog_info"]["Name"] == "ansible_testing"
    assert result["machine_catalog_info"]["AllocationType"]


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_catalog_info.yaml")
def test_machine_catalog_info_with_fields(cvad_connection_args, run_ansible_module):
    args = dict(cvad_connection_args)
    args.update(
        {
            "machine_catalog": "ansible_testing",
            "fields": ["Name", "Id"],
        }
    )
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert not result.get("changed")
    assert "machine_catalog_info" in result
    assert result["machine_catalog_info"]["Name"] == "ansible_testing"
    assert "IsBroken" not in result["machine_catalog_info"]
