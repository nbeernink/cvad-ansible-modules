"""
Base argument spec
"""
from ansible.module_utils.basic import env_fallback

def base_argument_spec():
    """
    Returns a dictionary with common options for all CVAD module specs.
    """
    return dict(
        ddc_server=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ["CVAD_DDC_SERVER"]),
        ),
        username=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ["CVAD_USERNAME"]),
        ),
        password=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ["CVAD_PASSWORD"]),
            no_log=True
        ),
        validate_certs=dict(
            type='bool',
            required=False,
            default=True,
            fallback=(env_fallback, ["CVAD_VALIDATE_CERTS"]),
        ),
    )
