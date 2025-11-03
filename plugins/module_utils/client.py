#!/usr/bin/env python3
"""
Provides a client to interact with the Citrix Virtual Apps and Desktops REST API
https://developer-docs.citrix.com/en-us/citrix-virtual-apps-desktops/citrix-cvad-rest-apis/overview
"""
import json
from ansible.module_utils.urls import Request

class CVADClient():
    """Initialize the CVADClient"""
    def __init__(
            self,
            username,
            password,
            ddc_server,
            validate_certs,
            **kwargs # pylint: disable=unused-argument
    ):
        self.username = username
        self.password = password
        self.ddc_server = ddc_server
        self.validate_certs = validate_certs


        self.base_url = f'https://{self.ddc_server}/cvad/manage'
        self.request = Request(validate_certs = validate_certs)
        self.cvad_header = None

    def _get_bearer_token(self) -> str:
        """ Return a bearer token using basic authentication """

        response = self.request.post(
            url = self.base_url + '/Tokens',
            url_username=self.username,
            url_password=self.password,
            force_basic_auth=True,
        ).read()

        token_data = json.loads(response)

        return token_data['Token']

    def _get_site_id(self,bearer_token) -> dict:
        """ Get and validate the list of available sites """

        req_sites = self.request.get(
            url = self.base_url + '/Me',
            headers = {
                'Authorization': f'CWSAuth Bearer={bearer_token}'
            }
        ).read()

        sites = json.loads(req_sites)

        # FIXME: This can probably be done fancier
        #
        # Example output:
        #"Customers": [
        #    {
        #        "Id": "CitrixOnPremises",
        #        "Name": "None",
        #        "Sites": [
        #            {
        #                "Id": "<site-id>",
        #                "Name": "<site-name>"
        #            }
        #        ]
        #    }
        #]
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

    def _request(self, method, endpoint, data=None, headers=None):
        """
        Performs A REST request and return content or status code
        """

        url = f"{self.base_url}/{endpoint}"
        payload = json.dumps(data) if data else None

        try:
            response  = self.request.open(
                method=method,
                url=url,
                data=payload,
                headers=self.cvad_header if not None else headers,
            )

            if response.length != 0:
                return json.loads(response.read())

            return response.status

        except AssertionError as http_error:
            raise AssertionError(f"Request failed ({method} {url}): {http_error}") from http_error


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
