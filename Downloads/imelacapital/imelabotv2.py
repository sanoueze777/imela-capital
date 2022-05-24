# -*- coding: utf-8 -*-
"""Untitled-Copy1 (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oxRARj5P76D-WiObaAUTWlf139cNvzIG
"""

!pip install python-binance

import matplotlib.pyplot as plt
import requests
import json
import pandas as pd
import datetime as dt
import statsmodels.tsa.stattools as ts
from scipy.stats import linregress
import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from decimal import Decimal
import math

api_key = 'qSFD8v5nf57EXhXzYLD40vgZXZDcKlf1R8MQ3zuWfz7LUBAmKr88Dnk4SafNlo0P'
api_secret = '8OB7S6Oj58tT24l4rAAfJQP9KSd0cPbYH5HVdbNFzYxXcElnom1PCjFyPWGKjx45'

client = Client(api_key, api_secret)

trade_size = 10
tick_size = 6 # the tick_size as per binance API docs

price = 30000 # Just making this up for now to exemplify, this is fetched within the script

trade_quantity = trade_size / price # Work out how much BTC to order


#print(trade_quantity_str)
#0.000526

def get_quantity_precision(currency_symbol):    
    info = client.futures_exchange_info() 
    info = info['symbols']
    for x in range(len(info)):
        if info[x]['symbol'] == currency_symbol:
            return info[x]['pricePrecision']
    return None

precision = get_quantity_precision('BTCUSDT')
print(precision)
trade_quantity = float(round(trade_quantity, precision))

client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=trade_quantity)

def get_binance_data (symbol, interval, startTime, endTime):

    url = "https://api.binance.com/api/v3/klines"

    
    startTime = str(int(startTime.timestamp()*1000))
    endTime = str(int(endTime.timestamp()*1000))
    limit = '100000'

    req_params = {'symbol' : symbol, 'interval': interval, 'startTime' : startTime, 'endTime' : endTime, 'limit' : limit}

    df = pd.DataFrame(json.loads(requests.get(url, params = req_params).text))

    df = df.iloc[:, 0:6]
    df.columns = ['dateTime' , 'Open', 'High', 'Low', 'Close', 'volume' ]

    df.index = [dt.datetime.fromtimestamp(x/1000.0) for x in df.dateTime]
    
    return df

def check_Cointegration(pair1,pair2):
    result = linregress(pair1, pair2)
    residuals = pair1 - result.slope * pair2
    adf = ts.adfuller(residuals)
    
    is_Cointegrated = False
    if adf[4]['5%']>adf[0]:
        is_Cointegrated = True
    return is_Cointegrated

def market_scan(universe):
    universe['cointegrated'] = False
    for i in range(0, len(universe)):
        symbol1 = universe.loc[i, 'symbol1']
        symbol2 = universe.loc[i, 'symbol2']
        pair1 = get_binance_data(symbol1,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
        pair2 = get_binance_data(symbol2,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
        
        pair1_ = pair1['Close'].astype('float')
        pair2_ = pair2['Close'].astype('float')
        universe.loc[i, 'cointegrated'] = check_Cointegration(pair1_,pair2_)
    return universe

def generate_arb_signal(pair1, pair2):
    pair1_ = get_binance_data(pair1,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
    pair2_ = get_binance_data(pair2,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
    pair1_ = pair1_['Close'].astype('float')
    pair2_ = pair2_['Close'].astype('float')
    ratio = pair1_/pair2_
    ratio_mavg5 = ratio.rolling(window = 5, center = False).mean()
    ratio_mavg20 = ratio.rolling(window = 20, center = False).mean()
    std20_5 = ratio.rolling(window = 20, center = False).std()
    z_score20 = (ratio_mavg5 - ratio_mavg20)/std20_5
    signal = 3
    

    if z_score20[-1] > 1 and ratio_mavg5[-1]>ratio[-1] and ratio[-1]/ratio_mavg20[-1]>1 :
        signal = 0
    if ratio_mavg20[-1]/ratio[-1]>1 and 1.0005>ratio_mavg20[-1]/ratio[-1] :
        signal = -99
    if -1 > z_score20[-1] and ratio[-1]>ratio_mavg5[-1] and ratio_mavg20[-1]/ratio[-1]>1 :
        signal = 1 
    if ratio[-1]/ratio_mavg20[-1]>1 and 1.0005>ratio[-1]/ratio_mavg20[-1]:
        signal = -99
        
    return signal

def transact (pair1, pair2):
    pair1_ = get_binance_data(pair1,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
    pair2_ = get_binance_data(pair2,'5m',dt.datetime.now() - dt.timedelta(hours = 3),dt.datetime.now())
    pair1_ = pair1_['Close'].astype('float')
    pair2_ = pair2_['Close'].astype('float')
    ratio  = pair1_[-1]/pair2_[-1]
    return ratio

sellLevel = 0
buyLevel = 0
closelevel = 0
percentage_profit = 0
cointegrated_pairs = pd.DataFrame()
universe = pd.DataFrame([['STMXUSDT', 'BTSUSDT'], ['MANAUSDT', 'SANDUSDT'], ['SCUSDT', 'LTCUSDT'], ['FILUSDT', 'ETHUSDT'], ['BLZUSDT', 'ALICEUSDT'], ['VETUSDT', 'MATICUSDT'], ['ADAUSDT', 'XRPUSDT'], ['SOLUSDT', 'ETHUSDT'], ['AAVEUSDT', 'AVAXUSDT'], ['DOTUSDT', 'NEARUSDT'], ['LRCUSDT', 'UNIUSDT'], ['ENJUSDT', 'TLMUSDT'], ['CELRUSDT', 'ONEUSDT'], ['ALPHAUSDT', 'DENTUSDT'], ['OMGUSDT', 'XTZUSDT'], ['RVNUSDT', 'NEOUSDT'], ['HBARUSDT', 'COMPUSDT'], ['BATUSDT', 'BAKEUSDT'], ['SRMUSDT', 'CHRUSDT'], ['BANDUSDT', 'QTUMUSDT'], ['ANKRUSDT', 'SXPUSDT'], ['RAYUSDT', 'ICXUSDT'], ['COTIUSDT', 'RENUSDT']],columns=['symbol1', 'symbol2'])
universe['sells'] = 0
universe['buys'] = 0
universe['close'] = 0
universe['profit'] = 0
universe['opensell'] = 0
universe['openbuy'] = 0

while 1 == 1:
    #cointegrated_pairs = market_scan(universe)
    #cointegrated_pairs = cointegrated_pairs.loc[cointegrated_pairs['cointegrated'] == True]  ** without cointegration testing
    #cointegrated_pairs = cointegrated_pairs.reset_index(drop=True)

    #print(cointegrated_pairs)
    cointegrated_pairs = universe
    time.sleep(3)
    for i in range(0,len(cointegrated_pairs)):
        pair1 = cointegrated_pairs.loc[i,'symbol1']
        pair2 = cointegrated_pairs.loc[i,'symbol2']
        sellLevel = 0
        buyLevel = 0
        closelevel = 0
        sellcount = 0
        buycount = 0
        print('looking for opportunities')

        

        try:
            print(generate_arb_signal(pair1, pair2))
            pair1_ = get_binance_data(pair1,'5m',dt.datetime.now() - dt.timedelta(hours =24),dt.datetime.now())
            pair2_ = get_binance_data(pair2,'5m',dt.datetime.now() - dt.timedelta(hours =24),dt.datetime.now())
            pair1_ = pair1_['Close'].astype('float')
            pair2_ = pair2_['Close'].astype('float')
            ratio = pair1_/pair2_
            ratio_mavg5 = ratio.rolling(window = 5, center = False).mean()
            ratio_mavg20 = ratio.rolling(window = 20, center = False).mean()
            std20_5 = ratio.rolling(window = 20, center = False).std()
            z_score20 = (ratio_mavg5 - ratio_mavg20)/std20_5

            plt.plot(ratio.index, ratio.values)
            plt.plot(ratio_mavg5.index, ratio_mavg5.values)
            plt.plot(ratio_mavg20.index, ratio_mavg20.values)
            print(pair1+pair2)
            plt.show()
            
            plt.clf() 
            plt.plot(z_score20.values)
            plt.show()
            plt.clf() 


            closelevel = cointegrated_pairs.loc[i,'close'] + transact(pair1, pair2)
            if generate_arb_signal(pair1, pair2) == 0 and 1>cointegrated_pairs.loc[i,'opensell']:
                sellLevel = cointegrated_pairs.loc[i,'sells'] + transact(pair1, pair2)
                cointegrated_pairs.loc[i,'sells'] = sellLevel
                sellcount = 1
                sellcount = cointegrated_pairs.loc[i,'opensell'] + sellcount
                cointegrated_pairs.loc[i,'opensell'] = sellcount
                print(generate_arb_signal(pair1, pair2))

            elif closelevel/cointegrated_pairs.loc[i,'buys']  > 1.01 and cointegrated_pairs.loc[i,'openbuy']>0:
                closelevel = cointegrated_pairs.loc[i,'close'] + transact(pair1, pair2)
                cointegrated_pairs.loc[i,'close'] = closelevel
                cointegrated_pairs.loc[i,'openbuy'] = 0 
                cointegrated_pairs.loc[i,'profit'] = cointegrated_pairs.loc[i,'profit'] + ((cointegrated_pairs.loc[i,'close'] - cointegrated_pairs.loc[i,'buys'])/ cointegrated_pairs.loc[i,'buys'])
                cointegrated_pairs.loc[i,'buys'] = 0
                cointegrated_pairs.loc[i,'close'] = 0
                print(generate_arb_signal(pair1, pair2))

            elif cointegrated_pairs.loc[i,'sells'] / closelevel > 1.01 and cointegrated_pairs.loc[i,'opensell']>0:
                closelevel = cointegrated_pairs.loc[i,'close'] + transact(pair1, pair2)
                cointegrated_pairs.loc[i,'close'] = closelevel
                cointegrated_pairs.loc[i,'opensell'] = 0 
                cointegrated_pairs.loc[i,'profit'] = cointegrated_pairs.loc[i,'profit'] + ((cointegrated_pairs.loc[i,'sells'] - cointegrated_pairs.loc[i,'close'])/cointegrated_pairs.loc[i,'sells'])
                cointegrated_pairs.loc[i,'sells'] = 0
                cointegrated_pairs.loc[i,'close'] = 0
                print(generate_arb_signal(pair1, pair2))

            elif generate_arb_signal(pair1, pair2) == 1 and 1>cointegrated_pairs.loc[i,'openbuy']:
                buyLevel = cointegrated_pairs.loc[i,'buys'] + transact(pair1, pair2)
                cointegrated_pairs.loc[i,'buys'] = buyLevel
                buycount = 1
                buycount = cointegrated_pairs.loc[i,'openbuy'] + buycount
                cointegrated_pairs.loc[i,'openbuy'] = buycount
        except :
            pass

        print(cointegrated_pairs)

!pip install python-binance

from binance.client import Client

api_key = "477038af4d3290a6c5a8cb73d12ca566720b704c4ddaaac5ab9f90a7de0afa32"
api_secret = "60d0ab3a4b3aecff0ea184b3954bbbce5aefee8310b0d09e9c3d9df83ebe24c6"

client = Client(api_key, api_secret, testnet=True)
client.API_URL = 'https://testnet.binancefuture.com'

order1 = client.create_test_order(
                symbol= 'STMXUSDT',
                side=client.SIDE_BUY,
                type=client.ORDER_TYPE_MARKET,
                quantity=10)







print(generate_arb_signal('AXSUSDT', 'ILVUSDT'))

and ratio_mavg5[i]>ratio[i] and ratio[i]-ratio_mavg20[i]>0.1
and ratio[i]>ratio_mavg5[i] and ratio_mavg20[i]-ratio[i]>0.1

pair1 = get_binance_data('STMXUSDT','1h',dt.datetime(2022,4,1),dt.datetime(2022,5,13))
pair2 = get_binance_data('BTSUSDT','1h',dt.datetime(2022,4,1),dt.datetime(2022,5,13))

# pair1 = pd.read_csv('STMXUSDT1H_20220101_20220512.csv')
# pair2 = pd.read_csv('BTSUSDT1H_20220101_20220512.csv')
pair1 = pair1['Close'].astype('float')
pair2 = pair2['Close'].astype('float')
pair2.reset_index()
pair1.reset_index()
pairs = pd.DataFrame()
pairs['BTS'] = 0
pairs['STMX']=pair1
pairs['BTS']=pair2

pairs=pairs.reset_index()

pairs['cointegrated'] = False
for i in range(100,len(pairs)):
    pair1 = pairs.loc[i-100:i, 'STMX']
    pair2 = pairs.loc[i-100:i, 'BTS'] 
    pairs.loc[i, 'cointegrated'] = check_Cointegration(pair1,pair2)

a = pairs.loc[pairs['cointegrated'] == True]

a = pairs

b = a['BTS']
c = a['STMX']

b
c

plt.plot(b/c)

ratio = b/c
ratio.describe()

a.to_csv('a.csv')

if __name__ == '__main__':
    plot_pairs(pair1,pair2)
    #pair1.to_csv('AXS-USD220101_220512.csv')
    #pair2.to_csv('ILV-USD220101_220512.csv')
    scatter_plot(pair1, pair2)

#pair1 = pair4/pair1
#pair2 = pair2/pair3
result = linregress(pair1, pair2)

result

residuals = pair1 - result.slope * pair2
adf = ts.adfuller(residuals)

adf

check_Cointegration(pair1,pair2)

ratio = pair1/pair2

ratio.reset_index()

ratio.drop(columns="index", inplace=True)

plt.plot(x)

ratio_mavg20 = ratio.rolling(window = 24, center = False).mean()

x = ratio -ratio_mavg20

x.describe()

#ratio = pair1/pair2
ratio_mavg5 = ratio.rolling(window = 5, center = False).mean()
ratio_mavg20 = ratio.rolling(window = 20, center = False).mean()
std20_5 = ratio.rolling(window = 20, center = False).std()
z_score20 = (ratio_mavg5 - ratio_mavg20)/std20_5

plt.plot(ratio.index, ratio.values)
plt.plot(ratio_mavg5.index, ratio_mavg5.values)
plt.plot(ratio_mavg20.index, ratio_mavg20.values)

plt.plot(z_score20)

yesterday = dt.datetime.now() - dt.timedelta(days = 1)

str(int(yesterday.timestamp()*1000))