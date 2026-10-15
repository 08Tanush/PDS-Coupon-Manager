from .shopify_client import graphql
from .discount_service import make_discount

BULK_ADD = '''mutation($id:ID!,$codes:[DiscountRedeemCodeInput!]!){discountRedeemCodeBulkAdd(discountId:$id,codes:$codes){bulkCreation{id done importedCount failedCount} userErrors{field message}}}'''
BULK_STATUS = '''query($id:ID!){discountRedeemCodeBulkCreation(id:$id){id done importedCount failedCount codes(first:250){nodes{code discountRedeemCode{id} errors{message}}}}}'''
CREATE = '''mutation($input:DiscountCodeBasicInput!){discountCodeBasicCreate(basicCodeDiscount:$input){codeDiscountNode{id} userErrors{field message}}}'''
LOOKUP = '''query($code:String!){codeDiscountNodeByCode(code:$code){id codeDiscount{... on DiscountCodeBasic{title usageLimit}}}}'''

def lookup(store, token, code):
    return graphql(store,token,LOOKUP,{'code':code}).get('codeDiscountNodeByCode')

def create_parent(store, token, code, title, percent, start, expiry):
    payload = make_discount(code,percent,start,expiry)
    payload['title'] = title
    response = graphql(store,token,CREATE,{'input':payload})['discountCodeBasicCreate']
    if response['userErrors']:
        raise RuntimeError('Parent discount rejected: '+str(response['userErrors'])[:400])
    node = response.get('codeDiscountNode')
    if not node or not node.get('id'):
        raise RuntimeError('Parent creation returned no discount ID')
    return node['id']

def add_codes(store, token, discount_id, codes):
    response = graphql(store,token,BULK_ADD,{'id':discount_id,'codes':[{'code':c} for c in codes]})['discountRedeemCodeBulkAdd']
    if response['userErrors']:
        raise RuntimeError('Bulk add rejected: '+str(response['userErrors'])[:400])
    job = response.get('bulkCreation')
    if not job or not job.get('id'):
        raise RuntimeError('Bulk add returned no job ID')
    return job['id']

def job_status(store,token,job_id):
    return graphql(store,token,BULK_STATUS,{'id':job_id}).get('discountRedeemCodeBulkCreation')
