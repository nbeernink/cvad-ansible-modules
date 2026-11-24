from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os
import re
import sys
from unittest.mock import patch
from urllib.parse import urlparse, urlunparse
import pytest

# Ensure collection namespace can be imported when running pytest outside ansible-test.
# ansible-test target runs (modules/module_utils) only expose ansible.module_utils, not ansible.utils.
collection_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
if collection_root not in sys.path:
    sys.path.insert(0, collection_root)

try:
    from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder

    if not any(isinstance(f, _AnsibleCollectionFinder) for f in sys.meta_path):
        _finder = _AnsibleCollectionFinder(paths=[collection_root])
        _finder._install()
except ImportError:
    pass

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

CASSETTE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

DEFAULT_TEST_TARGETS = {
    "CVAD_TEST_MACHINE1": "test-vm1.example.org",
    "CVAD_TEST_MACHINE2": "test-vm2.example.org",
    "CVAD_TEST_DELIVERY_GROUP": "test-group1",
    "CVAD_TEST_MACHINE_CATALOG": "test-catalog1",
    "CVAD_TEST_USER1": "CORP\\user1",
    "CVAD_TEST_USER2": "CORP\\user2",
    "CVAD_TEST_TAG1": "AnsibleTestTag1",
    "CVAD_TEST_TAG2": "AnsibleTestTag2",
}

SID_PATTERN = re.compile(r"S-1-5-21-\d+-\d+-\d+-\d+")
DUMMY_SID = "S-1-5-21-0000000000-0000000000-00000000-0000"
DUMMY_SITE_ID = "00000000-0000-0000-0000-000000000001"
DUMMY_SITE_NAME = "TESTSITE"


class AnsibleExitJson(BaseException):
    """Exception raised by module.exit_json in unit tests."""

    def __init__(self, data):
        self.data = data
        super().__init__(str(data))


class AnsibleFailJson(BaseException):
    """Exception raised by module.fail_json in unit tests."""

    def __init__(self, data):
        self.data = data
        super().__init__(str(data))


def _exit_json(self, **kwargs):
    if "failed" not in kwargs:
        kwargs["failed"] = False
    raise AnsibleExitJson(kwargs)


def _fail_json(self, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


def _normalize_test_targets(text):
    """Replace custom CVAD_TEST_* env values with mock defaults."""
    if not text:
        return text
    for env_var, default_val in DEFAULT_TEST_TARGETS.items():
        custom_val = os.environ.get(env_var)
        if custom_val and custom_val != default_val:
            text = text.replace(custom_val, default_val)
    return text


def scrub_request(request):
    """Normalize target hostname and custom test entity names before recording."""
    parsed = urlparse(request.uri)
    normalized_path = _normalize_test_targets(parsed.path)
    normalized_query = _normalize_test_targets(parsed.query)
    request.uri = urlunparse(
        parsed._replace(
            netloc="ddc.example.org",
            path=normalized_path,
            query=normalized_query,
        )
    )
    if request.body:
        if isinstance(request.body, bytes):
            body_text = request.body.decode("utf-8", errors="ignore")
            request.body = _normalize_test_targets(body_text).encode("utf-8")
        elif isinstance(request.body, str):
            request.body = _normalize_test_targets(request.body)
    return request


def scrub_response_tokens(response):
    """Scrub bearer tokens, SIDs, Site IDs, and volatile headers before writing cassette."""
    headers_to_remove = {
        "citrix-transactionid",
        "date",
        "server",
        "via",
        "x-request-id",
        "x-runtime",
    }
    for key in list(response.get("headers", {}).keys()):
        if key.lower() in headers_to_remove:
            del response["headers"][key]

    try:
        body = response["body"]["string"]
        is_bytes = isinstance(body, bytes)
        text = body.decode("utf-8") if is_bytes else body
        if not text:
            return response

        text = SID_PATTERN.sub(DUMMY_SID, text)
        text = _normalize_test_targets(text)

        data = json.loads(text)
        if isinstance(data, dict):
            if "UserId" in data:
                data["UserId"] = DUMMY_SID
            if "Principal" in data:
                data["Principal"] = "unit-tester"
            if "Token" in data:
                data["Token"] = "MOCKED_BEARER_TOKEN"
            if "Customers" in data and isinstance(data["Customers"], list):
                for customer in data["Customers"]:
                    if isinstance(customer, dict) and isinstance(customer.get("Sites"), list):
                        for site in customer["Sites"]:
                            if isinstance(site, dict) and "Id" in site:
                                site["Id"] = DUMMY_SITE_ID
                            if isinstance(site, dict) and "Name" in site:
                                site["Name"] = DUMMY_SITE_NAME
            serialized = json.dumps(data, indent=2)
            response["body"]["string"] = (
                serialized.encode("utf-8") if is_bytes else serialized
            )
            for hdr_key in list(response.get("headers", {}).keys()):
                if hdr_key.lower() == "content-length":
                    response["headers"][hdr_key] = [str(len(serialized.encode("utf-8")))]
    except Exception:
        pass
    return response


@pytest.fixture(scope="module")
def vcr_cassette_dir():
    """Store and load all pytest-recording cassettes in tests/unit/fixtures/."""
    return CASSETTE_DIR


@pytest.fixture(scope="session")
def vcr_config():
    """Shared VCR configuration for pytest-recording."""
    return {
        "match_on": ["method", "path", "query"],
        "filter_headers": [
            ("authorization", "CWSAuth Bearer=MOCKED_BEARER_TOKEN"),
            ("Citrix-CustomerId", "CitrixOnPremises"),
            ("Citrix-InstanceId", DUMMY_SITE_ID),
            ("Host", "ddc.example.org"),
        ],
        "filter_post_data_parameters": ["password", "username"],
        "before_record_request": scrub_request,
        "before_record_response": scrub_response_tokens,
        "decode_compressed_response": True,
    }


_ENV_FIXTURES = {
    "cvad_connection_args": {
        "ddc_server": ("CVAD_DDC_SERVER", "ddc.example.com"),
        "username": ("CVAD_USERNAME", "testuser"),
        "password": ("CVAD_PASSWORD", "testpass"),
        "validate_certs": False,
    },
    "cvad_test_machine1": "CVAD_TEST_MACHINE1",
    "cvad_test_machine2": "CVAD_TEST_MACHINE2",
    "cvad_test_delivery_group": "CVAD_TEST_DELIVERY_GROUP",
    "cvad_test_machine_catalog": "CVAD_TEST_MACHINE_CATALOG",
    "cvad_test_user1": "CVAD_TEST_USER1",
    "cvad_test_user2": "CVAD_TEST_USER2",
    "cvad_test_tag1": "CVAD_TEST_TAG1",
    "cvad_test_tag2": "CVAD_TEST_TAG2",
}


def _make_env_fixture(spec):
    """Build a pytest fixture resolving env-var specs or dicts of env-var tuples."""

    @pytest.fixture
    def _fixture():
        if isinstance(spec, dict):
            return {
                key: os.environ.get(val[0], val[1]) if isinstance(val, tuple) else val
                for key, val in spec.items()
            }
        return os.environ.get(spec, DEFAULT_TEST_TARGETS[spec])

    return _fixture


for _fixture_name, _fixture_spec in _ENV_FIXTURES.items():
    globals()[_fixture_name] = _make_env_fixture(_fixture_spec)


@pytest.fixture
def run_ansible_module():
    """Helper to run an Ansible module with custom arguments and intercept exit/fail calls."""

    def _run(module_func, module_args):
        args = dict(module_args)
        if "_ansible_remote_tmp" not in args:
            args["_ansible_remote_tmp"] = "/tmp"
        if "_ansible_keep_remote_files" not in args:
            args["_ansible_keep_remote_files"] = False

        basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": args}))
        if hasattr(basic, "_ANSIBLE_PROFILE"):
            basic._ANSIBLE_PROFILE = "legacy"

        with patch.object(basic.AnsibleModule, "exit_json", _exit_json), patch.object(
            basic.AnsibleModule, "fail_json", _fail_json
        ):
            try:
                module_func()
            except AnsibleExitJson as e:
                return e.data
            except AnsibleFailJson as e:
                return e.data

    return _run
