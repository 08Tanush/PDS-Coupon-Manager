import json
import os
import time
from urllib import error, parse, request
from .config import STORE, API_VERSION
QUERY = 'query { shop { name myshopifyDomain } }'
LOOKUP = 'query($code:String!){codeDiscountNodeByCode(code:$code){id}}'
CREATE = """mutation($input:DiscountCodeBasicInput!){discountCodeBasicCreate(basicCodeDiscount:$input){codeDiscountNode{id} userErrors{field message}}}"""
class Throttled(RuntimeError):
    pass


def http_json(url, payload, headers=None):
    data = json.dumps(payload).encode() if isinstance(payload, dict) else payload
    req = request.Request(url, data=data, headers=headers or {}, method='POST')
    try:
        with request.urlopen(req, timeout=35) as resp:
            return json.load(resp)
    except error.HTTPError as exc:
        if exc.code == 429:
            raise Throttled('Shopify HTTP 429') from None
        # Do not log response body from auth endpoint: it may contain sensitive information.
        raise RuntimeError(f'Shopify HTTP {exc.code}') from None
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError(f'Network request failed: {type(exc).__name__}') from None


def authenticate():
    store = os.getenv('SHOPIFY_STORE', '').strip()
    cid = os.getenv('SHOPIFY_CLIENT_ID', '').strip()
    secret = os.getenv('SHOPIFY_CLIENT_SECRET', '').strip()
    if store != STORE:
        raise RuntimeError('Store mismatch: only approved production myshopify domain is permitted')
    if not cid or not secret or cid == 'replace_locally' or secret == 'replace_locally':
        raise RuntimeError('Set actual SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET in local .env')
    form = parse.urlencode({'grant_type':'client_credentials','client_id':cid,'client_secret':secret}).encode()
    response = http_json(f'https://{store}/admin/oauth/access_token', form, {'Content-Type':'application/x-www-form-urlencoded'})
    if not response.get('access_token'):
        raise RuntimeError('No Shopify access token; check same-organization client-credentials eligibility')
    return store, response['access_token']


def graphql(store, token, query, variables=None):
    for attempt in range(5):
        try:
            result = http_json(f'https://{store}/admin/api/{API_VERSION}/graphql.json',
                               {'query':query,'variables':variables or {}},
                               {'Content-Type':'application/json','X-Shopify-Access-Token':token})
            errors = result.get('errors') or []
            if errors and all(e.get('extensions',{}).get('code') == 'THROTTLED' for e in errors):
                raise Throttled('GraphQL throttled')
            if errors:
                raise RuntimeError('GraphQL rejected request: ' + '; '.join(str(e.get('message','error')) for e in errors)[:400])
            if 'data' not in result:
                raise RuntimeError('Missing GraphQL data')
            return result['data']
        except Throttled:
            if attempt == 4:
                raise
            time.sleep(min(2 ** attempt, 10))


def lookup(store, token, code):
    return (graphql(store, token, LOOKUP, {'code':code}).get('codeDiscountNodeByCode') or {}).get('id')
