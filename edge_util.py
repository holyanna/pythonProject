# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 10:55:42 2021

@author: 박태혁
"""

import base64
import uuid
import time
import json
import requests
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import urllib


def connect(api_url, data):          
    url = api_url + data.replace(' ', '')
    request = Request(url)
    response_body = ''
    try:
        response = urlopen(request)
    except HTTPError as e:
        print('HTTP Error!', e)
    else:
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read().decode('utf-8')
            response_body = response_body.replace('+', '%20')
            response_body = json.loads(urllib.parse.unquote(response_body))
            #print(response_body)
        else:
            print("Response error code : %d" % rescode)
    return response_body

def call_recept(img_url):
    api_url = 'https://b696d14f8f704fd3a48e3b650d0d8b53.apigw.ntruss.com/custom/v1/7635/6ad7ffc9c54e048363230f0b1647c8e9ab9329256d2d08210f222a9d2625f954/document/receipt'
    secret_key = 'aHVKZWdKeERTVkJkdFNWWEZobUZMREhnem9aSXVOZ0Y='    
    
    request_json = {
    'images': [
        {
            'format': 'png',
            'name': 'demo',
            'data': base64.b64encode(requests.get(img_url).content).decode('utf-8')
        }
    ],
    'requestId': str(uuid.uuid4()),
    'version': 'V2',
    'timestamp': int(round(time.time() * 1000))
    }
    
    payload = json.dumps(request_json).encode('UTF-8')
    headers = {
      'X-OCR-SECRET': secret_key,
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", api_url, verify=False, headers=headers, data = payload)
    
    
    return json.loads(response.text)



def call_api(img_url):
    req_data = {}
    req_data['IMG_URL'] = img_url
    req_data['MCR_TEXT_YN'] = 'Y'
    req_data['MCR_RAW_YN'] = 'Y'
    json_data = {}
    json_data['TARGET'] = 'BSTR'
    json_data['TRAN_NO'] = 'BPCR_MBL_L001'
    json_data['PTL_ID'] = 'PTL_51'
    json_data['CHNL_ID'] = 'CHNL_1'
    json_data['USE_INTT_ID'] = 'UTLZ_1709060902735'
    json_data['USER_ID'] = 'simdemo01t'
    json_data['REQ_DATA'] = req_data        
    api_url = 'https://webank.appplay.co.kr/CardAPI.do?JSONData='     
    return connect(api_url, json.dumps(json_data))

def call_ocr(img_url, ocr_type):
    api_url = 'https://webank.appplay.co.kr/CardAPI.do?JSONData=' 

    req_data = {}
    req_data['RCPT_IMG_URL'] = img_url
    req_data['OCR_TYPE'] = ocr_type
    req_data['OCR_TEXT_YN'] = 'Y'
    req_data['OCR_RAW_YN'] = 'Y'
    req_data['PTL_ID'] = 'PTL_51'
    req_data['CHNL_ID'] = 'CHNL_1'
    req_data['USE_INTT_ID'] = 'UTLZ_1709060902735'
    req_data['USER_ID'] = 'simdemo01t'
    
    json_data = {}
    json_data['TRAN_NO'] = 'BPCD_OCR_R001'
    json_data['PTL_ID'] = 'PTL_51'
    json_data['CHNL_ID'] = 'CHNL_1'
    json_data['USE_INTT_ID'] = 'UTLZ_1709060902735'
    json_data['USER_ID'] = 'simdemo01t'
    json_data['REQ_DATA'] = req_data    
    
    return connect(api_url, json.dumps(json_data))
        