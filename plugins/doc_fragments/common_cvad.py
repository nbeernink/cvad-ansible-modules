class ModuleDocFragment(object):
    # Common Citrix options
    DOCUMENTATION = r'''
    options:
      ddc_server:
        description:
          - hostname for the Desktop Delivery Controller server
        type: str
        required: true
      username:
        description:
          - The username which will fetch the bearer token
        type: str
        required: true
      password:
        description:
          - Password for account fetching the bearer token
        type: str
        required: true
      validate_certs:
        description:
          - Validate SSL certificates
        type: bool
        required: false
        default: true
    '''
