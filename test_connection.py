"""Read-only Shopify connectivity check. No writes."""
from pds.config import load_env
from pds.shopify_client import authenticate, graphql, QUERY

if __name__ == '__main__':
    load_env()
    store, token = authenticate()
    shop = graphql(store, token, QUERY)['shop']
    print('CONNECTED:', shop['name'], '|', shop['myshopifyDomain'])
