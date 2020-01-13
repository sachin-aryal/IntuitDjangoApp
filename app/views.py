from __future__ import absolute_import

from django.http import JsonResponse
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.conf import settings

from app.services import get_account_info
from quickbooks import QuickBooks


# Create your views here.
def index(request):
    return render(request, 'index.html')


def oauth(request):
    auth_client = AuthClient(
        settings.CLIENT_ID,
        settings.CLIENT_SECRET,
        settings.REDIRECT_URI,
        settings.ENVIRONMENT,
    )

    url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    request.session['state'] = auth_client.state_token
    return redirect(url)


def callback(request):
    auth_client = AuthClient(
        settings.CLIENT_ID,
        settings.CLIENT_SECRET,
        settings.REDIRECT_URI,
        settings.ENVIRONMENT,
        state_token=request.session.get('state', None),
    )

    state_tok = request.GET.get('state', None)
    error = request.GET.get('error', None)

    if error == 'access_denied':
        return redirect('app:index')

    if state_tok is None:
        return HttpResponseBadRequest()
    elif state_tok != auth_client.state_token:
        return HttpResponse('unauthorized', status=401)

    auth_code = request.GET.get('code', None)
    realm_id = request.GET.get('realmId', None)
    request.session['realm_id'] = realm_id

    if auth_code is None:
        return HttpResponseBadRequest()

    try:
        auth_client.get_bearer_token(auth_code, realm_id=realm_id)
        request.session['access_token'] = auth_client.access_token
        request.session['refresh_token'] = auth_client.refresh_token
        request.session['id_token'] = auth_client.id_token
    except AuthClientError as e:
        # just printing status_code here but it can be used for retry workflows, etc
        print(e.status_code)
        print(e.content)
        print(e.intuit_tid)
    except Exception as e:
        print(e)
    return redirect('app:connected')


def connected(request):
    auth_client = AuthClient(
        settings.CLIENT_ID,
        settings.CLIENT_SECRET,
        settings.REDIRECT_URI,
        settings.ENVIRONMENT,
        access_token=request.session.get('access_token', None),
        refresh_token=request.session.get('refresh_token', None),
        id_token=request.session.get('id_token', None),
    )

    if auth_client.id_token is not None:
        return render(request, 'connected.html', context={'openid': True})
    else:
        return render(request, 'connected.html', context={'openid': False})


def account(request):
    auth_client = AuthClient(
        settings.CLIENT_ID,
        settings.CLIENT_SECRET,
        settings.REDIRECT_URI,
        settings.ENVIRONMENT,
        access_token=request.session.get('access_token', None),
        refresh_token=request.session.get('refresh_token', None),
        realm_id=request.session.get('realm_id', None),
    )
    client = QuickBooks(
        auth_client=auth_client,
        refresh_token=request.session.get('refresh_token', None),
        company_id=4620816365030839390,
    )

    from quickbooks.objects.account import Account
    accounts = Account.all(qb=client)
    print(accounts)
    if auth_client.access_token is not None:
        access_token = auth_client.access_token

    if auth_client.realm_id is None:
        raise ValueError('Realm id not specified.')
    response = get_account_info(auth_client.access_token, auth_client.realm_id)
    if not response.ok:
        return HttpResponse(' '.join([response.content, str(response.status_code)]))
    else:
        response = response.json()["QueryResponse"]
        return JsonResponse(response)


def refresh(request):
    auth_client = AuthClient(
        settings.CLIENT_ID,
        settings.CLIENT_SECRET,
        settings.REDIRECT_URI,
        settings.ENVIRONMENT,
        access_token=request.session.get('access_token', None),
        refresh_token=request.session.get('refresh_token', None),
    )

    try:
        auth_client.refresh()
    except AuthClientError as e:
        print(e.status_code)
        print(e.intuit_tid)
    return HttpResponse('New refresh_token: {0}'.format(auth_client.refresh_token))
