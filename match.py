#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import pprint
import codecs
if sys.version_info < (2,6):
    import simplejson as json
else:
    import json

PRINT_STATS = True

class Rules:
    filter_additional_items = True #to filter products + peripherals
    filter_terms = [u'for', u'pour', u'für'] #to filter product accessories

class ProductFamily:
    def __init__(self, family_name):
        self.family_name = family_name
        self.products = []

class RunStats:
    def __init__(self):
        self.products_matched = 0
        self.listings_matched = 0

    def get_stats(self, matches_store):
        self.products_matched = len(matches_store)
        for k in matches_store.keys():
            self.listings_matched += len(matches_store[k])

    def __repr__(self):
        stats = ('products matched: ' + str(self.products_matched) + '\n' +
                 'listings matched: ' + str(self.listings_matched) + '\n')
        return stats

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

    #Print results
    output_matches(matches_store)

    #Print Stats
    if (PRINT_STATS):
        stats = RunStats()
        stats.get_stats(matches_store)
        print stats

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

#Match product component strings to listing titles
def match_and_store(matches_store, products_store, listing):
    #Discard listings with peripheral items, indicated by '+'
    if Rules.filter_additional_items:
        pattern_plus_sign = re.compile(r'\+')
        match_plus_sign = pattern_plus_sign.search(listing.get('title'))
        if match_plus_sign:
            return

    if Rules.filter_terms:
        for w in Rules.filter_terms:
            if w in listing.get('title'):
                return

    manufacturer = match_manufacturer(products_store, listing)
    if not manufacturer:
        return

    family = match_family(products_store, listing, manufacturer)
    product = match_product(products_store, listing, manufacturer, family)

    if not product:
        return

    store_match(matches_store, product, listing)

#Match if pattern is contained in *cleaned up* text, returns pattern
def match_strings(pattern, text):
    #When either is None, assume no match
    if pattern == None or text == None:
        return None

    #Clean up the strings
    noise = re.compile(r'[\-_\+=\(\):,&!\\\"\'\/]')
    pattern = re.sub(noise, '', pattern)
    text = re.sub(noise, '', text)

    re_pattern = re.compile(pattern, re.IGNORECASE)
    if re_pattern.search(text):
        return pattern

def exact_match_strings(pattern, text):
    if pattern == None or text == None:
        return None

    #Convert dashes to spaces in pattern
    dashes = re.compile(r'[\-]')
    pattern = re.sub(dashes, ' ', pattern)

    #Now we match on the word boundry
    pattern_words = pattern.split()
    for w in pattern_words:
        re_pattern = re.compile(r"\b" + pattern + r"\b", re.IGNORECASE)
        match = re_pattern.search(text)
        if not match:
            return False

    return True

def match_manufacturer(products_store, listing):
    for k in products_store.keys():
        match = match_strings(k, listing.get('manufacturer'))
        if match:
            return match
    return None

def match_family(products_store, listing, manufacturer):
    for f in products_store[manufacturer]:
        match = match_strings(f.family_name, listing.get('title'))
        if match:
            return f
    return None

def match_product(products_store, listing, manufacturer, family):
    if family:
        for p in family.products:
            match = exact_match_strings(p.get('model'), listing.get('title'))
            if match:
                return p
    else:
        for f in products_store[manufacturer]:
            for p in f.products:
                match = exact_match_strings(p.get('model'), listing.get('title'))
                if match:
                    return p

    return None

def store_match(matches_store, product, listing):
    product_name = product['product_name']
    if product_name in matches_store:
        listings = matches_store[product_name]
        listings.append(listing)
    else:
        matches_store [product_name] = [listing]

def print_matches(matches_store):
    matches = matches_store.items()
    for m in matches:
        match = {m[0]:m[1]}
        print json.dumps(match)

#Output to file and encode to literal strings
def output_matches(matches_store):
    matches = matches_store.items()
    output_file = codecs.open('results.txt', 'w', 'utf-8')
    for m in matches:
        match = {"product_name": m[0], "listings":m[1]}
        match_json_string = json.dumps(match, ensure_ascii=False)
        output_file.write(match_json_string)
        output_file.write('\n')

if __name__ == "__main__":
    sys.exit(main())