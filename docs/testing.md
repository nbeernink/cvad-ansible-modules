# Testing guide for `nbeernink.cvad`

## 1. Overview

The `nbeernink.cvad` collection uses `ansible-test` for automated quality and regression testing:

- **Sanity Tests (`ansible-test sanity`)**: Validates Ansible module documentation/argspecs, Python imports, formatting, and collection metadata.
- **Unit Tests (`ansible-test units` / `pytest`)**: Tests all modules, the `cvad` inventory plugin, and `CVADClient` offline using **`pytest-recording`** (powered by **`vcrpy`**) and pre-recorded YAML cassettes in `tests/unit/fixtures/`.
  - **Offline & Hermetic**: Zero network access required; `--record-mode=none` is the default so unexpected HTTP calls fail immediately.
  - **Fast Execution**: The full unit test suite executes in under 10 seconds.
  - **Automated Secret Sanitization**: Bearer tokens, Basic Auth credentials, customer/site identifiers, AD SIDs, and passwords are scrubbed by `vcr_config` filters and hooks before writing YAML to disk.
  - **Portable Targets**: Hostnames are normalized to `ddc.example.org` and test entities (machine, delivery group, users, tags) are configurable via `CVAD_TEST_*` environment variables.

---

## 2. Directory structure overview

```
tests/
├── config.yml
└── unit/
    ├── requirements.txt            # Unit test dependencies (pytest, pytest-mock, pytest-recording, pytest-xdist)
    ├── conftest.py                 # pytest-recording config (vcr_config, vcr_cassette_dir), scrubbers, env-var fixtures
    ├── fixtures/                   # Serialized YAML network cassettes
    │   ├── client_login.yaml
    │   ├── client_pagination.yaml
    │   ├── client_rate_limit.yaml
    │   ├── delivery_group_info.yaml
    │   ├── delivery_group_machines_present.yaml
    │   ├── delivery_group_machines_absent.yaml
    │   ├── machine_catalog_info.yaml
    │   ├── machine_catalog_machines_present.yaml
    │   ├── machine_catalog_machines_absent.yaml
    │   ├── machine_info.yaml
    │   ├── machine_maintenancemode_on.yaml
    │   ├── machine_maintenancemode_off.yaml
    │   ├── machine_tags_add.yaml
    │   ├── machine_tags_remove.yaml
    │   ├── machine_user_assignment_present.yaml
    │   ├── machine_user_assignment_absent.yaml
    │   └── inventory_cvad.yaml
    └── plugins/
        ├── module_utils/
        │   └── test_client.py
        ├── modules/
        │   ├── test_delivery_group_info.py
        │   ├── test_delivery_group_machines.py
        │   ├── test_machine_catalog_info.py
        │   ├── test_machine_catalog_machines.py
        │   ├── test_machine_info.py
        │   ├── test_machine_maintenancemode.py
        │   ├── test_machine_tags.py
        │   └── test_machine_user_assignment.py
        └── inventory/
            └── test_cvad.py
```

---

## 3. Running sanity tests

Run from the collection root (`/path/to/ansible_collections/nbeernink/cvad`):

- **Using Docker (recommended, matches CI):**
  ```bash
  ansible-test sanity --docker ubuntu
  ```
- **Using an isolated virtualenv:**
  ```bash
  ansible-test sanity --venv --requirements
  ```
- **Target a specific test or Python version:**
  ```bash
  ansible-test sanity --test validate-modules --venv
  ```

---

## 4. Running unit tests

`ansible-test units` reads dependencies from `tests/unit/requirements.txt` when `--requirements` is passed:

- **With Docker (matches GitHub Actions CI):**
  ```bash
  ansible-test units --docker ubuntu --requirements
  ```
- **With an `ansible-test`-managed virtualenv:**
  ```bash
  ansible-test units --venv --requirements
  ```

---

## 5. `pytest-recording` configuration & mock targets

In `tests/unit/conftest.py`, `pytest-recording` is configured via `vcr_cassette_dir` and `vcr_config`:
- **`vcr_cassette_dir`**: Points to `tests/unit/fixtures/`.
- **Recording mode**: Controlled by `pytest-recording`'s `--record-mode` CLI option (defaults to `"none"` so missing recordings fail immediately).
- **`match_on`**: Matches on `["method", "path", "query"]`, allowing cassettes recorded against any internal hostname (e.g. `ddc01.corp.internal`) to match test requests against dummy hosts (`ddc.example.com`).
- **`filter_headers`**: Redacts `authorization`, `Citrix-CustomerId`, `Citrix-InstanceId`, and `Host`.
- **`filter_post_data_parameters`**: Redacts `username` and `password`.
- **`before_record_request`**: Normalizes the target hostname to `ddc.example.org` and normalizes any custom `CVAD_TEST_*` target names back to canonical mock names.
- **`before_record_response`**: Strips volatile headers, scrubs bearer tokens, regex-scrubs AD SIDs (`S-1-5-21-...`), masks Site IDs, and normalizes custom `CVAD_TEST_*` target names.

### Environment variables for mock & lab targets
Tests read target entity names from environment variables with canonical mock defaults:

| Environment Variable | Default (Mock Value) | Used By |
| :--- | :--- | :--- |
| `CVAD_TEST_DELIVERY_GROUP` | `test-group1` | `delivery_group_info`, `delivery_group_machines`, `inventory/cvad` |
| `CVAD_TEST_MACHINE1` | `test-vm1.example.org` | `delivery_group_machines`, `machine_info`, `machine_maintenancemode`, `machine_tags`, `machine_user_assignment`, `inventory/cvad` |
| `CVAD_TEST_MACHINE2` | `test-vm2.example.org` | `inventory/cvad` |
| `CVAD_TEST_MACHINE_CATALOG` | `test-catalog1` | `machine_catalog_machines`, `inventory/cvad` |
| `CVAD_TEST_TAG1` | `AnsibleTestTag1` | `machine_tags`, `inventory/cvad` |
| `CVAD_TEST_TAG2` | `AnsibleTestTag2` | `machine_tags` |
| `CVAD_TEST_USER1` | `CORP\user1` | `machine_user_assignment` |
| `CVAD_TEST_USER2` | `CORP\user2` | `machine_user_assignment` |

---

## 6. Capturing fixtures from a live environment

Run from the collection root (`/path/to/ansible_collections/nbeernink/cvad`):

1. **Install dependencies:**
   ```bash
   pip3 install ansible-dev-tools
   ade install -e --venv .venv
   source .venv/bin/activate
   pip install -r tests/unit/requirements.txt
   ```

2. **Set DDC credentials and target lab entities:**
   ```bash
   export CVAD_DDC_SERVER="ddc01.corp.internal"
   export CVAD_USERNAME="citrix-admin@corp.internal"
   export CVAD_PASSWORD="MySecurePassword123"
   export CVAD_VALIDATE_CERTS="false"

   export CVAD_TEST_MACHINE1="lab-vm-01.corp.internal"
   export CVAD_TEST_MACHINE2="lab-vm-02.corp.internal"
   export CVAD_TEST_DELIVERY_GROUP="Lab-Delivery-Group"
   export CVAD_TEST_MACHINE_CATALOG="Lab-Machine-Catalog"
   export CVAD_TEST_USER1="CORP\\labuser1"
   export CVAD_TEST_USER2="CORP\\labuser2"
   export CVAD_TEST_TAG1="LabTag1"
   export CVAD_TEST_TAG2="LabTag2"
   ```

3. **Record cassettes with `--record-mode=rewrite`:**
   ```bash
   PYTHONPATH=$(pwd)/../../.. pytest tests/unit/ --record-mode=rewrite
   ```

4. **Verify secret scrubbing before committing:**
   ```bash
   grep -rn "$CVAD_PASSWORD" tests/unit/fixtures/
   grep -rn "Authorization: Basic" tests/unit/fixtures/
   ```

---

## 7. GitHub actions

Both `sanity` and `units` jobs are configured in `.github/workflows/ansible-test.yml` using `ansible-community/ansible-test-gh-action` across:
- `stable-2.16`
- `stable-2.18`
- `stable-2.19`
- `stable-2.20`
- `milestone`
