"""
Provides a client to interact with the Citrix Virtual Apps and Desktops REST API
https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/overview
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from time import sleep
from urllib.error import HTTPError
from ansible.module_utils.urls import Request


class CVADClient():
    """Initialize the CVADClient"""
    def __init__(
            self,
            username,
            password,
            ddc_server,
            validate_certs,
            **kwargs  # pylint: disable=unused-argument
    ):
        self.username = username
        self.password = password
        self.ddc_server = ddc_server
        self.validate_certs = validate_certs

        self.base_url = f'https://{self.ddc_server}/cvad/manage'
        self.request = Request(validate_certs=validate_certs)
        self.cvad_header = None

    def _get_bearer_token(self) -> str:
        """ Return a bearer token using basic authentication """

        response = self.request.post(
            url=self.base_url + '/Tokens',
            url_username=self.username,
            url_password=self.password,
            force_basic_auth=True,
        ).read()

        token_data = json.loads(response)

        return token_data['Token']

    def _get_site_id(self, bearer_token) -> dict:
        """ Get and validate the list of available sites """

        req_sites = self.request.get(
            url=self.base_url + '/Me',
            headers={
                'Authorization': f'CWSAuth Bearer={bearer_token}'
            }
        ).read()

        sites = json.loads(req_sites)

        # FIXME: This can probably be done fancier
        #
        # Example output:
        # "Customers": [
        #     {
        #         "Id": "CitrixOnPremises",
        #         "Name": "None",
        #         "Sites": [
        #             {
        #                 "Id": "<site-id>",
        #                 "Name": "<site-name>"
        #             }
        #         ]
        #     }
        # ]
        #
        #
        # Exactly 1 customer
        if len(sites['Customers']) == 1:
            # Only CitrixOnPremises is supported
            if sites['Customers'][0]['Id'] == 'CitrixOnPremises':
                # Exactly 1 site
                if len(sites['Customers'][0]['Sites']) == 1:
                    return sites['Customers'][0]['Sites'][0]['Id']
                raise AssertionError("Exactly 1 site is supported")
            raise AssertionError("Only CitrixOnPremises is supported")
        raise AssertionError("Exactly 1 customer is supported")

    def login(self) -> None:
        """
        Log into the API and set up the required header
        The any requests going to the API basically require 4 things:
        * Authorization, CWSAuth with Bearer token
        * Citrix-CustomerId, only CitrixOnPremises is supported
        * Citrix-InstanceId, the site instance we're operating on
        """
        bearer_token = self._get_bearer_token()
        site_id = self._get_site_id(bearer_token)

        cvad_header = {
            'Authorization': f'CWSAuth Bearer={bearer_token}',
            'Citrix-CustomerId': 'CitrixOnPremises',
            'Citrix-InstanceId': f'{site_id}',
            'Content-type': 'application/json'
        }

        self.cvad_header = cvad_header

    # Maximum number of consecutive rate limit (HTTP 429) retries before giving up
    _MAX_RATE_LIMIT_RETRIES = 5
    # Fallback wait time in seconds in case retryDelay cannot be parsed
    _DEFAULT_RETRY_DELAY = 10

    @staticmethod
    def _parse_retry_delay(error_body, default_delay):
        """
        Parse the retry delay (in seconds) from a HTTP 429 response payload

        The Citrix CVAD REST API returns the number of seconds to wait in a
        'retryDelay' parameter inside the response body, for example:

            {
                "parameters": [
                    { "name": "retryDelay", "value": "4" }
                ]
            }

        Returns the retryDelay value as an integer, or default_delay when the
        value cannot be determined.
        """
        try:
            error_json = json.loads(error_body)
        except (json.JSONDecodeError, TypeError, ValueError):
            return default_delay

        for param in error_json.get("parameters", []):
            if param.get("name") == "retryDelay":
                try:
                    return int(param["value"])
                except (KeyError, ValueError, TypeError):
                    break

        return default_delay

    def _request(self, method, endpoint, data=None):
        """
        Performs a REST request and returns content if present
        Automatically retries on HTTP 429 (rate limit exceeded), waiting the
        number of seconds specified in the response body before giving it another try
        """

        payload = json.dumps(data) if data else None
        all_items = []
        rate_limit_retries = 0

        base_request_url = f"{self.base_url}/{endpoint}"

        # We'll loop over current_url when a ContinuationToken is in the response
        current_url = base_request_url

        while True:
            try:
                response = self.request.open(
                    method=method,
                    url=current_url,
                    data=payload,
                    headers=self.cvad_header,
                )

                # A successful response resets the rate-limit retry counter
                rate_limit_retries = 0

                if response.length != 0:
                    json_resp = json.loads(response.read())

                    if 'Items' in json_resp.keys():

                        items = json_resp.get('Items', [])
                        all_items.extend(items)

                        # Multiple pages are coming in when response has a ContinuationToken
                        if 'ContinuationToken' in json_resp.keys():
                            continuation_token = json_resp.get('ContinuationToken')

                            # Handle query parameter seperator
                            # should be a '&' for multiple and '?' if only 1 param
                            separator = '&' if '?' in base_request_url else '?'

                            # Update current_url with the new continuation_token
                            current_url = f"{base_request_url}" \
                                f"{separator}" \
                                f"continuationToken={continuation_token}"

                            # Be gentle with the API
                            sleep(0.5)

                        else:
                            # Paging through API complete, break out of the loop
                            break

                    else:
                        # Return json response if there are no Items
                        return json_resp

                else:
                    # No data received, also break from the loop
                    break

            except HTTPError as http_error:
                if http_error.code == 429:
                    rate_limit_retries += 1
                    if rate_limit_retries > self._MAX_RATE_LIMIT_RETRIES:
                        raise AssertionError(
                            f"Request failed ({method} {current_url}): rate limit exceeded "
                            f"and retry limit ({self._MAX_RATE_LIMIT_RETRIES}) reached."
                        ) from http_error

                    retry_delay = self._parse_retry_delay(
                        http_error.read(), self._DEFAULT_RETRY_DELAY
                    )
                    sleep(retry_delay)
                    continue

                raise AssertionError(
                    f"Request failed ({method} {current_url}): {http_error}"
                ) from http_error
            except AssertionError:
                raise
            except Exception as err:
                raise AssertionError(
                    f"Request failed ({method} {current_url}): {err}"
                ) from err

        return all_items

    # Search functions
    def _find_entity_field_by_name(self, endpoint: str, name: str, fields: str) -> str:
        """
        Generic method to search an endpoint and return its field

        Args:
            endpoint: The REST endpoint to search
            name: name of the item to search for
            fields: fields to return, if empty, returns all fields

        Returns:
            dict or str: The value of the requested field.
        """

        # FIXME: This works but needs some cleaning up/type checking

        results = self.post(
            f"{endpoint}/$search?fields={fields}",
            data={'BasicSearchString': name}
        )

        if not results:
            raise AssertionError(f"No item found for search '{name}' at endpoint '{endpoint}'")

        first_item = results[0]

        value = first_item.get(fields, None)

        if value is None:
            raise KeyError(f"API response missing expected field '{fields}'")

        return value

    def find_delivery_group_by_id(self, group_name) -> str:
        """Search delivery group and return the id"""
        return self._find_entity_field_by_name(
            endpoint="/DeliveryGroups",
            name=group_name,
            fields="Id"
        )

    def find_machine_catalog_by_id(self, catalog_name) -> str:
        """Search delivery group and return the id"""
        return self._find_entity_field_by_name(
            endpoint="/MachineCatalogs",
            name=catalog_name,
            fields="Id"
        )

    def find_machine_id(self, machine_name) -> str:
        """Search machine and return its ID"""
        return self._find_entity_field_by_name(
            endpoint="/Machines",
            name=machine_name,
            fields="Id"
        )

    def find_machine_catalog_id_for_machine(self, machine_name) -> str:
        """Search machine and return the machine catalog ID"""
        results = self._find_entity_field_by_name(
            endpoint="/Machines",
            name=machine_name,
            fields="MachineCatalog"
        )

        # Handles the nested dictionary lookup
        catalog_id = results.get('Id', None)

        if catalog_id is None:
            raise KeyError("The 'MachineCatalog' object did not contain an 'Id' key.")

        return str(catalog_id)

    # CRUD operations
    def get(self, endpoint):
        """Perform a GET request"""
        return self._request('GET', endpoint)

    def post(self, endpoint, data):
        """Perform a POST request"""
        return self._request('POST', endpoint, data)

    def patch(self, endpoint, data):
        """Perform a PATCH request"""
        return self._request("PATCH", endpoint, data)

    def put(self, endpoint, data):
        """Perform a PUT request"""
        return self._request("PUT", endpoint, data)

    def delete(self, endpoint):
        """Perform a DELETE request"""
        return self._request("DELETE", endpoint)

    # Machine User Helper methods
    @staticmethod
    def matches_user(target_user, existing_user_obj) -> bool:
        """
        Check if target_user string matches an existing user object or string representation.
        """
        target = target_user.strip().lower()
        if not target:
            return False

        if isinstance(existing_user_obj, str):
            return existing_user_obj.strip().lower() == target

        if isinstance(existing_user_obj, dict):
            candidates = {
                (existing_user_obj.get('SamName') or '').strip().lower(),
                (existing_user_obj.get('PrincipalName') or '').strip().lower(),
                (existing_user_obj.get('SamAccountName') or '').strip().lower(),
                (existing_user_obj.get('Sid') or '').strip().lower(),
                (existing_user_obj.get('DisplayName') or '').strip().lower(),
                (existing_user_obj.get('Name') or '').strip().lower(),
            }
            candidates.discard('')
            return target in candidates

        return False

    @staticmethod
    def get_user_identity_string(user_obj) -> str:
        """
        Get the best canonical string representation for an assigned user object.
        """
        if isinstance(user_obj, str):
            return user_obj
        if isinstance(user_obj, dict):
            for key in ('SamName', 'PrincipalName', 'Sid', 'SamAccountName', 'DisplayName', 'Name'):
                val = user_obj.get(key)
                if val and isinstance(val, str) and val.strip():
                    return val.strip()
        return str(user_obj)
