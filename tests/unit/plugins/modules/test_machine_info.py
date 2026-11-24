from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.modules.machine_info import run_module


@pytest.mark.vcr
@pytest.mark.default_cassette("machine_info.yaml")
def test_machine_info(cvad_connection_args, cvad_test_machine1, run_ansible_module):
    args = dict(cvad_connection_args)
    args["machine_name"] = cvad_test_machine1
    result = run_ansible_module(run_module, args)

    assert not result.get("failed")
    assert not result.get("changed")
    assert "machine_info" in result
    assert result["machine_info"]["DnsName"] == cvad_test_machine1
    assert result["machine_info"]["Id"] == "00000000-0000-0000-0000-000000000001"
