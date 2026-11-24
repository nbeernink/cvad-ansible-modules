from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.nbeernink.cvad.plugins.module_utils.client import CVADClient


@pytest.mark.vcr
@pytest.mark.default_cassette("client_login.yaml")
def test_cvad_client_login(cvad_connection_args):
    client = CVADClient(**cvad_connection_args)
    client.login()

    assert client.cvad_header is not None
    assert "Authorization" in client.cvad_header
    assert client.cvad_header["Citrix-CustomerId"] == "CitrixOnPremises"
    assert client.cvad_header["Citrix-InstanceId"] == "00000000-0000-0000-0000-000000000001"


@pytest.mark.vcr
@pytest.mark.default_cassette("client_pagination.yaml")
def test_cvad_client_pagination(cvad_connection_args):
    client = CVADClient(**cvad_connection_args)
    client.login()

    items = client.get("Machines?limit=2")
    assert len(items) == 3
    assert items[0]["Id"] == "00000000-0000-0000-0000-000000000001"
    assert items[1]["Id"] == "00000000-0000-0000-0000-000000000002"
    assert items[2]["Id"] == "00000000-0000-0000-0000-000000000003"


@pytest.mark.vcr
@pytest.mark.default_cassette("client_rate_limit.yaml")
def test_cvad_client_rate_limit(cvad_connection_args):
    client = CVADClient(**cvad_connection_args)
    client.login()

    items = client.get("Machines")
    assert len(items) == 1
    assert items[0]["Id"] == "00000000-0000-0000-0000-000000000001"


def test_matches_user():
    assert CVADClient.matches_user("DOMAIN\\alice", {"SamName": "DOMAIN\\alice"})
    assert CVADClient.matches_user(
        "alice@corp.com", {"PrincipalName": "ALICE@CORP.COM"}
    )
    assert CVADClient.matches_user("alice", "ALICE")
    assert not CVADClient.matches_user("bob", {"SamName": "DOMAIN\\alice"})


def test_get_user_identity_string():
    assert (
        CVADClient.get_user_identity_string({"SamName": "DOMAIN\\alice"})
        == "DOMAIN\\alice"
    )
    assert (
        CVADClient.get_user_identity_string({"DisplayName": "Alice Smith"})
        == "Alice Smith"
    )
    assert CVADClient.get_user_identity_string("plain_username") == "plain_username"
