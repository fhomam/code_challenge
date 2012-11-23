#!/usr/bin/python

import sys
import getopt
import json
import re
import io
import pprint
import string

class ProductFamily:
    def __init__(self, family_name):
        self.family_name = family_name
        self.products = []

class RunStats:
    products_matched = 0
    listings_matched = 0

def main(argv=None):
    if argv is None:
        argv = sys.argv

    if (len(argv) < 3 ):
        msg = ("-- Please specify input data textfiles\n"
            +  "-- e.g.\"match.py products.txt listings.txt\"")
        print msg
    else:
        process (argv)

    sys.exit(0)

def process(argv):
    #Process and store products
    products_store = {}
    products = open(argv[1], 'r')
    products_line = products.readline()
    while products_line:
        product = json.loads(products_line)
        store_product(products_store, product)
        products_line = products.readline()

    #Match listings to products
    matches_store = {}
    listings = open(argv[2], 'r')
    listings_line = listings.readline()
    while listings_line:
        listing = json.loads(listings_line)
        match_and_store(matches_store, products_store, listing)
        listings_line = listings.readline()

    #Output results to textfile
    pprint.pprint(matches_store)

    #Print Stats
    RunStats.products_matched = len(matches_store)
        
    for k in matches_store.keys():
        l = matches_store[k]
        print 'bla'
        print len(l)
        print l
        #print l.size()
        RunStats.listings_matched += len(l)

    stats = ('products matched: ' + str(RunStats.products_matched) + '\n' +
             'listings matched: ' + str(RunStats.listings_matched) + '\n')
    print (stats)

#Store products in {"manufacturer":[ProductFamily]}
def store_product(products_store, product):
    family_name = product.get('family') #None when key not present
    manufacturer_name = product.get('manufacturer')
    family = ProductFamily(family_name)
    family.products.append(product)

    #Check if manufacturer already in store
    if manufacturer_name in products_store:
        families = products_store.get(manufacturer_name)
        family_found = False
        #Check if ProductFamily already exists
        for fam in families:
            if fam.family_name == family_name:

                fam.products.append(product)
                family_found = True
                break

        if not family_found:
            families.append(family)
    else:
        products_store[manufacturer_name] = [family]

def match_and_store(matches_store, products_store, listing):
    matched_manufacturer = None
    matched_family = None
    matched_product = None
    matched_product_name = None

    for k in products_store.keys():
        matched_manufacturer = match_strings(k, listing.get('manufacturer'))
        if matched_manufacturer:
            break

    if matched_manufacturer == None:
        return

    #Constraint - Ignore when '+' appears in description
    #Such listing genearlly lists price for product + peripherals
    pattern_plus_sign = re.compile(r'\+')
    match_plus_sign = pattern_plus_sign.search(listing.get('title'))
    if match_plus_sign:
        return
    
    for f in products_store[matched_manufacturer]:
        matched_family = match_strings(f.family_name, listing.get('title'))
        if matched_family:
            matched_family = f #Assign to ProductFamily object
            break
    
    if matched_family:
        for p in matched_family.products:
            pattern_model = get_product_model_pattern(p.get('model'))
            matched_product = match_strings (pattern_model, listing.get('title'))
            if matched_product:
                matched_product = p #Assign to Product dict
                break
                    
    else: #If _family not defined, search all product models for manufacturer
        for f in products_store[matched_manufacturer]:
            for p in f.products:
                pattern_model = get_product_model_pattern(p.get('model'))
                matched_product = match_strings (pattern_model, listing.get('title'))
                if matched_product:
                    matched_product = p #Assign to Product dict
                    break

    if matched_product == None:
        return

    #Add or append product, listing pair to matches store
    matched_product_name = matched_product['product_name']
    if matched_product_name in matches_store:
        listings = matches_store[matched_product_name]
        listings.append(listing)
    else:
        matches_store [matched_product_name] = [listing]

#Match two strings, if matched return the pattern string else None
def match_strings(pattern, text):
    #When either is None, assume no match
    if pattern == None or text == None:
        return None

    #Strip most non-alphanumeric characters
    #pattern_strip_noise = re.compile(r'[\-_\+=\(\):,&!\\\"\'\/]')
    #pattern_strip_noise = re.compile(r'[\+=\(\):,&!\\\"\'\/]')
    #flat_pattern = re.sub(pattern_strip_noise, "", pattern)
    #flat_text = re.sub(pattern_strip_noise, "", text)

    flat_pattern = pattern
    flat_text = text

    pattern_flat_pattern = re.compile(flat_pattern, re.IGNORECASE)
    match_flat_pattern = pattern_flat_pattern.search(flat_text)

    if match_flat_pattern:
        return pattern
    else:
        return None

#Constraint - Enforce first and last character matching, remove spaces
def get_product_model_pattern(model):
    model = "".join(model.split())
    return model

if __name__ == "__main__":
    sys.exit(main())