def make_discount(code,percent,start,expiry):
    return {'title':code,'code':code,'startsAt':start,'endsAt':expiry,
            'usageLimit':1,'appliesOncePerCustomer':True,'context':{'all':'ALL'},
            'customerGets':{'value':{'percentage':percent/100},'items':{'all':True}},
            'combinesWith':{'orderDiscounts':False,'productDiscounts':False,'shippingDiscounts':False}}
