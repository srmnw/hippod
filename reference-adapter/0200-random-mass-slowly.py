#!/usr/bin/python
# coding: utf-7

import sys
import json
import requests
import pprint
import unittest
import string
import random
import os
import json
import time
import datetime
import base64

pp = pprint.PrettyPrinter(depth=6)

def random_title(words):
    words = ['Foo', 'Bar', 'Linux', 'Something', 'Yeah', 'Nope', 'Random', "REST", "IPv6"]
    s = ' '.join(random.choice(words) for _ in range(11))
    return s

def random_result():
    d = ['passed', 'failed', 'nonapplicable' ]
    return d[random.randint(0, len(d) - 1)]

def random_submitter():
    d = ['Albert Einstein', 'Isaac Newton', 'Nikola Tesla', 'Marie Curie', 'Charles Darwin']
    return d[random.randint(0, len(d) - 1)]

def query_full(id):
    url = 'http://localhost:5000/api/v1/object/{}'.format(id)
    data = ''' '''
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.get(url, data=data, headers=headers)
    print("\nStatus Code:")
    print(r.status_code)
    print("\nRet Data:")
    data = r.json()
    pp.pprint(data)

def add_n(n):
    url = 'http://localhost:5000/api/v1/object'
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

    for i in range(n):
        data = dict()
        data["submitter"] = random_submitter()
        data["object-item"] = dict()
        data["object-item"]['categories'] = [ "team:orange", "topic:ip", "subtopic:route-cache" ]
        data["object-item"]['version'] = 0
        data['object-item']['title'] = "{}".format(random_title(80))

        data['object-item']['data'] = list()
        desc_data = dict()
        desc_data['type'] = 'description'
        desc_data['mime-type'] = 'text/markdown'
        # base64 requires a byte array for encoding -> .encode('utf-8')
        # json requires a string -> convert to UTF-8
        desc_data['data'] = base64.b64encode('This is simple *markdown*'.encode('utf-8')).decode("utf-8") 
        data['object-item']['data'].append(desc_data)

        img_data = dict()
        img_data['name'] = 'image.gif'
        img_data['mime-type'] = 'image/gif'
        img_data['data'] = "R0lGODlhDwAPAKECAAAAzMzM/////wAAACwAAAAADwAPAAACIISPeQHsrZ5ModrLlN48CXF8m2iQ3YmmKqVlRtW4MLwWACH+H09wdGltaXplZCBieSBVbGVhZCBTbWFydFNhdmVyIQAAOw=="
        data['object-item']['data'].append(img_data)

        data["attachment"] = dict()
        data["attachment"]['references'] = [ "doors:234236", "your-tool:4391843" ]
        data["attachment"]['tags'] = [ "ip", "route", "cache", "performance" ]
        data["attachment"]['categories'] = [ "team:orange", "topic:ip", "subtopic:route-cache" ]
        data["attachment"]['responsible'] = data["submitter"]

        achievement = dict()
        achievement["test-date"] = datetime.datetime.now().isoformat('T')
        achievement["result"] = random_result()
        data["achievements"] = list()
        data["achievements"].append(achievement)

        #os.system('cls' if os.name == 'nt' else 'clear')
        print("New Data:\n-----------\n")
        print(json.dumps(data, sort_keys=True, separators=(',', ': '), indent=4))
        print("\n-----------\n")

        dj = json.dumps(data, sort_keys=True, separators=(',', ': '))
        r = requests.post(url, data=dj, headers=headers)
        print("Return Data:\n-----------\n")
        ret_data = r.json()
        print(json.dumps(ret_data, sort_keys=True, separators=(',', ': '), indent=4))
        assert len(ret_data['data']['id']) > 0
        processing_time = ret_data['processing-time']
        sys.stderr.write("\nHTTPStatusCode: {} ServerProcTime {}s\n".format(r.status_code, processing_time))

        query_full(ret_data['data']['id'])
        time.sleep(1)

    print("\r\n\n")
    sys.exit(0)
    print("\r\n\n")

    url = 'http://localhost:5000/api/v1/objects'
    data = '''
    {
        "limit": 0,
        "ordering": "by-submitting-date-reverse",
        "maturity-level": "all"
    }
    '''

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.get(url, data=data, headers=headers)
    print("\nStatus Code:")
    print(r.status_code)
    print("\nRet Data:")
    data = r.json()
    pp.pprint(data)


if __name__ == '__main__':
    add_n(10000)
