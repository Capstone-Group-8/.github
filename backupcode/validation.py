'''
Capstone Group 8 - Invoice Processing System
Validates invoice line item data arithmetically, semantically, and syntactically.
Author: Sally Little @slittle95
Created on Aug 26, 2026
'''

import re

def test_line_semantic_validation(line, group1, group3):
    def check_desc_for(keys):
        desc = line.SuppliersDesc.lower()
        if 'Invoice' in desc:
            return(f"Contains the word Invoice.")
        #print("desc", desc)
        for key in keys:
            #print("key", key)
            if key not in desc:
                #print("fail")
                return (f"Failed line validation: Supplier ID implies {key}, but the description does not contain the keyword(s). ")
                #return(f"Semantic_error (line {count}) /")
        #print("pass")
        return ""
    return_group = ""
    if (group1 == '0031'):
        return_group += check_desc_for(['irid', 'rainbow'])
    elif (group1 == '0001'):
        return_group += check_desc_for(['fine', 'frit'])
    elif (group1 == '0002'):
        return_group += check_desc_for(['med','frit'])
    elif (group1 == '0003'):
        return_group += check_desc_for(['coarse', 'frit'])
    elif (group1 == '0008'):
        return_group += check_desc_for(['powder'])
    elif (group1 == '0107'):
        return_group += check_desc_for(['stringer','1','mm'])
    elif (group1 == '0272'):
        return_group += check_desc_for(['stringer','2','mm'])
    if (group3 == 'P001'):
        return_group += check_desc_for(['1','lb'])
    elif (group3 == 'P005'):
        return_group += check_desc_for(['5','lb'])
    elif (group3 == 'OZ05'):
        return_group += check_desc_for(['5', 'oz'])
    x = re.search("error", return_group)
    return return_group

def validate(invoice, line_items): 
    subtotal = 0
    errors = [""] * (len(line_items)+1)
    count = 0
    for i in line_items:
        count += 1
        #test the regex--syntactic errors
        x = re.search(r"0[0-9]{5}-[A-Z0-9]{4}-[A-Z]-[A-Z0-9]{4}", i.SuppliersID)
        if not x:
            errors[count] = (f"Failed line validation: {i.SuppliersID} does not follow the required format. ")
        else:
            #semantic errors--cannot have semantics without syntax so no point running it if syntax check fails
            id = x.group()
            #print(x)
            #print(id)
            group1 = id[7:11]
            group3 = id[-4:]
            #print(group3, group1)
            semantic_result = test_line_semantic_validation(i, group1, group3)
            if (semantic_result != ""):
                errors[count] = errors[count] + semantic_result
        #arithmetic errors
        if (i.Quantity * i.Rate != i.Amount):
            errors[count] = errors[count] + f"Failed line validation: {i.Quantity} times ${i.Rate} is not ${i.Amount}."
        subtotal += i.Amount
    if (subtotal + invoice.ShippingHandling != invoice.TotalAmt):
        errors[0] = f"Failed total validation:  Subtotal ${subtotal} + shipping cost ${invoice.ShippingHandling} is not ${invoice.TotalAmt}."
    return errors


'''
0: InvoiceNumber
1: Supplier
2: OrderDate
3: ShipDate
4: DueDate
5: SalesOrderNo
6: ShippingHandling
7: TotalAmt
8: line item 1
9: line item 2...
'''
''' this hasn't been tested
def update_confidence_scores(invoice, scores):
    errors = validate(invoice)
    if (errors == "200"):
        return invoice, scores
    error_list = errors.split('/')
    for err in error_list:
        if err.startswith("Arithmetic_total_error"):
            scores[7] = 0
        else:
            #get the number out of (line )
            #scores[n] = 0
    return scores
'''            
        
