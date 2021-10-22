# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 11:28:49 2021

@author: 박태혁
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 09:41:27 2021

@author: holya
"""

import pandas as pd
import numpy as np
import pickle
#from naver_geocoding import addr_to_coord

from urllib.request import urlopen
from urllib import parse
from urllib.request import Request
from urllib.error import HTTPError
import json

def sha256(file_path):
    f = open(file_path, 'rb')
    data = f.read()
    f.close()
    import hashlib
    return hashlib.sha256(data).hexdigest()

def addr_to_coord(addr):
    client_id = 'e0696ss28s'
    client_pw = '5v8FUs5a76Hvf3ouUdSmed9ObspdNwpxdbolOUD4'
    
    api_url = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query='
    
    #addr = '서울 중구  남대문시장10길  2-0'
    addr_urlenc = parse.quote(addr)
    url = api_url + addr_urlenc
    request = Request(url)
    request.add_header('X-NCP-APIGW-API-KEY-ID', client_id)
    request.add_header('X-NCP-APIGW-API-KEY', client_pw)
    x = None
    y = None     
    try:
        response = urlopen(request)
    except HTTPError as e:
        print('HTTP Error!', e)
        x = None
        y = None
    else:
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read().decode('utf-8')
            response_body = json.loads(response_body)
            if 'addresses' in response_body:
                if response_body['meta']['count'] > 0:
                    x = response_body['addresses'][0]['x']                        
                    y = response_body['addresses'][0]['y']
                    print("Success!")
                    
                    #print(response_body)
            else:
                print("not exist!!")
                x = None
                y = None 
        else:
            print("Response error code : %d" % rescode)
            x = None
            y = None 

    return x, y


class Ptcl:
    def __init__(self, file_path):  
        self.file_path = file_path
        pass

    def make_dict(self):
        self.addr_dic = {}
        self.dic_file_path = 'e:/working/utils/addr_dic.pickle'
        try:
            dic_file = open(self.dic_file_path, 'r+b')        
            self.addr_dic = pickle.load(dic_file)
        except:
            pass            

        self.ptcl_org = pd.read_csv(
            self.file_path,
            encoding='utf-8', 
            low_memory=False)
        self.ptcl_org = self.ptcl_org.dropna(subset=['mest_addr_1'])  #결측치제거
        
        self.ptcl_org['x'] = 0.
        self.ptcl_org['y'] = 0.

        for i in self.ptcl_org.index:
            addr1 = self.ptcl_org.loc[i, 'mest_addr_1']
            addr2 = self.ptcl_org.loc[i, 'mest_addr_2']
            cur_x = self.ptcl_org.loc[i, 'x']
            
            if cur_x == 0:
                addr_org = str(addr1) + ' ' + str(addr2)
                addr = addr_org
                while True:
                    if addr_org in self.addr_dic:
                        x,y = self.addr_dic.get(addr_org)
                        break
                    else:
                        print(addr)
                        try:                           
                            x,y = addr_to_coord(addr)                            
                            if x is None:
                                temp = addr.rsplit(' ', 1)[0]
                                if temp == addr:
                                    break
                                addr = temp
                            else:
                                self.addr_dic[addr_org] = x,y                                
                                break                                                
                        except:
                            break
                self.ptcl_org.loc[i, 'x'] = x
                self.ptcl_org.loc[i, 'y'] = y                                
    
                if i % 100 == 0:
                    print('처리중 :', i)
        self.ptcl_org.to_csv(self.file_path, encoding='utf-8') 

        print('사전 저장 시 ...')
        dic_file = open(self.dic_file_path, 'wb')
        pickle.dump(self.addr_dic, dic_file)
                
                
    def load_ptcl(self, count, features):        
        self.ptcl_org = pd.read_csv(
            self.file_path,
            encoding='utf-8', 
            low_memory=False)
        self.ptcl_org['mest_nm'] = np.where(self.ptcl_org['mest_nm'].str.startswith('FACEBK *'), 
                                            'FACEBK', self.ptcl_org['mest_nm'])        
        self.ptcl_org['card_tpbz_nm'] = np.where(pd.notnull(self.ptcl_org['card_tpbz_nm']), 
                                                 self.ptcl_org['card_tpbz_nm'], self.ptcl_org['mest_nm'])
        
        '''
        self.ptcl_org['x'] = np.where(pd.notnull(self.ptcl_org['x']), 
                                                 0, self.ptcl_org['x'])
        self.ptcl_org['y'] = np.where(pd.notnull(self.ptcl_org['y']), 
                                                 0, self.ptcl_org['y'])
        '''
        #self.ptcl_org = self.ptcl_org.dropna(subset=features)  #결측치제거                        
        ptcl = self.ptcl_org.sample(frac=1).head(count)
        ptcl = ptcl.query("card_tpbz_cd != 'AAAA'")
        ptcl = ptcl.fillna('missing')
        ptcl = ptcl.astype(str)
        
        if 'apv_tm_gb' in features:
            ptcl['apv_tm'] = ptcl['apv_tm'].str.rjust(
                width=6, fillchar='0').str.slice(start=0, stop=2) #시 추출 (분초 제외)
            ptcl.loc[(ptcl['apv_tm'] >= '21') | (ptcl['apv_tm'] < '08'), 'apv_tm_gb'] = 'A'
            ptcl.loc[(ptcl['apv_tm'] >= '08') & (ptcl['apv_tm'] < '11'), 'apv_tm_gb'] = 'B'
            ptcl.loc[(ptcl['apv_tm'] >= '11') & (ptcl['apv_tm'] < '14'), 'apv_tm_gb'] = 'C'
            ptcl.loc[(ptcl['apv_tm'] >= '14') & (ptcl['apv_tm'] < '18'), 'apv_tm_gb'] = 'D'
            ptcl.loc[(ptcl['apv_tm'] >= '18') & (ptcl['apv_tm'] < '21'), 'apv_tm_gb'] = 'E'
        

        if 'apv_dt_gb' in features:    
            ptcl['apv_dt'] = ptcl['apv_dt'].str.slice(start=6, stop=8)  #날짜만 추출
            ptcl.loc[(ptcl['apv_dt'] <= '05'), 'apv_dt_gb'] = 'A'
            ptcl.loc[(ptcl['apv_dt'] >= '06') & (ptcl['apv_dt'] <= '10'), 'apv_dt_gb'] = 'B'
            ptcl.loc[(ptcl['apv_dt'] >= '11') & (ptcl['apv_dt'] <= '24'), 'apv_dt_gb'] = 'C'
            ptcl.loc[(ptcl['apv_dt'] >= '25'), 'apv_dt_gb'] = 'D'
    
        ptcl['card_tpbz_nm'] = ptcl['card_tpbz_nm'].str.replace(" ", "") #공백제거
        
        X_ptcl = ptcl[features]
        #Y_ptcl = ptcl[['tran_kind_cd']]
        
        
        #from sklearn.preprocessing import OrdinalEncoder
        #mest_nm_enc = OrdinalEncoder()
        #card_no_enc = OrdinalEncoder()
        #X_ptcl["mest_nm"] = mest_nm_enc.fit_transform(X_ptcl[["mest_nm"]])
        #X_ptcl["card_no"] = card_no_enc.fit_transform(X_ptcl[["card_no"]])
        '''
        from keras.utils import to_categorical 
        X_ptcl["mest_nm"] = to_categorical(X_ptcl[["mest_nm"]])
        '''
        onehot_list = ['card_no', 'card_tpbz_nm', 'dvsn_cd']
        if 'mest_nm' in features:
            onehot_list.append('mest_nm')
        X = pd.get_dummies(data=X_ptcl, columns=onehot_list)
        
        from sklearn.preprocessing import OneHotEncoder
        self.enc = OneHotEncoder()
        Y = self.enc.fit_transform(ptcl[['tran_kind_nm']]).toarray()
        #print(enc.inverse_transform(Y))
        
        from sklearn.model_selection import train_test_split
        ##X_train,X_test,y_train,y_test = 
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X,Y, random_state=5)
        
        return self.X_train, self.X_test, self.y_train, self.y_test

   