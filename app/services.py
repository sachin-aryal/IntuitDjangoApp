import requests
from django.conf import settings


def get_account_info(access_token, realm_id):
    """[summary]

    """

    if settings.ENVIRONMENT == 'production':
        base_url = settings.QBO_BASE_PROD
    else:
        base_url = settings.QBO_BASE_SANDBOX

    route = '/v3/company/{0}/query?query={1}'.format(realm_id, "select * from Account")
    auth_header = 'Bearer {0}'.format(access_token)
    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json'
    }
    response = requests.post('{0}{1}'.format(base_url, route), headers=headers)
    return response
