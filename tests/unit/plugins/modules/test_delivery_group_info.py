from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.delivery_group_info import (
    run_module,
)


@pytest.mark.vcr
@pytest.mark.default_cassette("delivery_group_info.yaml")
def test_delivery_group_info_all(cvad_connection_args, run_ansible_module):
    args = dict(cvad_connection_args)
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert not result.get("changed")
    assert "delivery_group_info" in result
    assert len(result["delivery_group_info"]) >= 1


@pytest.mark.vcr
@pytest.mark.default_cassette("delivery_group_info.yaml")
def test_delivery_group_info_specific(
    cvad_connection_args, cvad_test_delivery_group, run_ansible_module
):
    args = dict(cvad_connection_args)
    args["delivery_group"] = cvad_test_delivery_group
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert not result.get("changed")
    assert "delivery_group_info" in result
    assert result["delivery_group_info"]["Name"] == cvad_test_delivery_group
