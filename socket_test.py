#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, jsonify
from flask_socketio import Namespace, SocketIO, send, emit
import requests
import json
import time # 引入time
from threading import Lock
import pygsheets


def struct_timestamp(t):
    struct_time = time.localtime(int(t)) # 轉成時間元組
    timeString = time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
    return timeString


def get_sinopacUSD():  #永豐匯率
    url = "https://mma.sinopac.com//ws/share/rate/ws_exchange.ashx?exchangeType=REMIT"
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    buy = resp.json()[0]["SubInfo"][0]['DataValue2']
    sale = resp.json()[0]["SubInfo"][0]['DataValue3']
    data = {'buy_sinopacUSD': buy, 'sale_sinopacUSD': sale}
    return data


####################################################################


def ACE_price():
    currency = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC', 'YFI', 'CRO', 'MANA', 'ANKR', 'SXP', 'CHZ', 'ENJ', 'CAKE', 'DOT', 'SHIB', 'DOGE', 'MATIC']  # 等有網址之後可以用爬ㄉ
    data = {}
    trade = requests.get('https://ace.io/polarisex/oapi/list/tradePrice')

    for c in currency:
        pair = c + '/' + 'TWD' 
        last_price = trade.json()[pair]["last_price"]
        data[c] = last_price
    return data

def get_FTX(currency_list):
    data = {}
    ex_rate = float(exchange_rate())
    
    for c in currency_list:
        pair = c + '/' + 'USD'  #所以要再乘上匯率得到台幣的價格
        trade = requests.get('https://ftx.com/api/markets/' + pair + '/trades?limit=1')
        last_price = trade.json()['result'][0]['price']
        if(c != 'USDT'):
            data[c] = round(last_price * ex_rate, 8)
            data[c + '_USD'] = last_price
        else:
            data[c] = str(last_price) + ' USD'
            
    return data

def get_Binance(currency_list):
    data = {}
    ex_rate = float(exchange_rate())
    
    for c in currency_list:
        if(c != 'USDT'):
            pair = c + 'USDT'  #所以要再乘上匯率得到台幣的價格
            trade = requests.get('https://api1.binance.com/api/v3/trades?symbol=' + pair + '&limit=1')
            last_price = trade.json()[0]["price"]
            data[c] = round(float(last_price) * ex_rate, 8)
            data[c + '_USD'] = last_price
        else: 
            data[c] = '我想想'
    return data

def get_MAX(currency_list):
    data = {}
    for c in currency_list:
        if(c != 'USDT'):
            pair = str.lower(c + 'TWD')
            trade = requests.get('https://max-api.maicoin.com/api/v2/trades?market=' + pair + '&order_by=desc&pagination=true&page=1&limit=1&offset=0')
            data[c] = trade.json()[0]['price']
            
            pair = str.lower(c + 'USDT')
            trade = requests.get('https://max-api.maicoin.com/api/v2/trades?market=' + pair + '&order_by=desc&pagination=true&page=1&limit=1&offset=0')
            data[c + '_USD'] = trade.json()[0]['price']
        else:
            pair = str.lower(c + 'TWD')
            trade = requests.get('https://max-api.maicoin.com/api/v2/trades?market=' + pair + '&order_by=desc&pagination=true&page=1&limit=1&offset=0')
            data[c] = trade.json()[0]['price']
    return data

def get_Bito(currency_list):
    data = {}
    for c in currency_list:
        if(c != 'USDT'):
            pair = c + '_TWD'
            trade = requests.get('https://api.bitopro.com/v3/trades/' + pair)
            last_price = trade.json()['data'][0]['price']
            data[c] = round(float(last_price) ,4)
            
            pair = c + '_USDT'
            trade = requests.get('https://api.bitopro.com/v3/trades/' + pair)
            data[c + '_USD'] = trade.json()['data'][0]['price']
        else:
            pair = c + '_TWD'
            trade = requests.get('https://api.bitopro.com/v3/trades/' + pair)
            last_price = trade.json()['data'][0]['price']
            data[c] = round( float(last_price) ,4)
    return data

    
################ 以下打包 #######################################

def sum_profit_data(): #包含date、sum_profit、永豐的匯率
    d1 = Arbitrage()
    d2 = ACE_price()
    d3 = get_sinopacUSD()
    
    data = dict(d1) #這跟垃圾一樣 但我還沒研究dict要怎寫更簡潔
    data.update(d2)
    data.update(d3)
    return data

def target_ex_data():
    FTX_list = ['YFI', 'CRO', 'SXP', 'CHZ', 'ENJ', 'MATIC']
    d1 = get_FTX(FTX_list)
    
    binance_list = ['CAKE', 'DOT', 'SHIB', 'DOGE', 'MANA', 'ANKR']
    d2 = get_Binance(binance_list)
    
    data = dict(d1) 
    data.update(d2) #這跟垃圾一樣 但我還沒研究dict要怎寫更簡潔
    return data

def competitor_data():
    # binance_list = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC', 'YFI', 'MANA', 'ANKR', 'SXP', 'CHZ', 'ENJ', 'CAKE', 'DOT', 'SHIB', 'DOGE', 'MATIC']
    # d1 = get_Binance(binance_list)
    
    # ftx_list = ['BTC', 'ETH', 'USDT', 'LTC', 'SHIB', 'DOGE']
    # d2 = get_FTX(ftx_list)
    
    max_list = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC', 'DOGE']
    d3 = get_MAX(max_list)
    
    bito_list = ['BTC', 'ETH', 'USDT', 'LTC', 'YFI', 'DOGE']
    d4 = get_Bito(bito_list)
    
    data = {'MAX': d3, 'BitoPro': d4}
    return data
    

################## 網頁 #######################################

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'

socketio = SocketIO()

socketio.init_app(app)

name_space = '/abcd'

thread = None
thread1 = None
thread2 = None

thread_lock = Lock()


@app.route('/abc')
def get_abc():
    """demo page"""
    return render_template('index.html')

@socketio.on('connect', namespace=name_space)
def connected_msg():
    print('client connected!')
    global thread
    global thread1
    global thread2
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target = sum_profit) 
        if thread1 is None:
            thread1 = socketio.start_background_task(target = competitor)
        if thread2 is None:
            thread2 = socketio.start_background_task(target = target_ex)
    
# @app.route('/push')
def sum_profit(): #包含date、sum_profit、永豐的匯率
    while True:
        socketio.sleep(10) #之後改15分鐘？
        event_name = 'sum_profit'
        broadcasted_data = sum_profit_data()
        socketio.emit(event_name, broadcasted_data, broadcast=True, namespace=name_space)
        print('Already sent sum_profit!')
        
def target_ex(): #只有target_ex
    while True:
        socketio.sleep(10)
        event_name = 'target_ex'
        broadcasted_data = target_ex_data()
        socketio.emit(event_name, broadcasted_data, broadcast=True, namespace=name_space)
        print('Already sent target_ex!')
             
def competitor(): #只有competitor
    while True:
        socketio.sleep(10)
        event_name = 'competitor'
        broadcasted_data = competitor_data()
        socketio.emit(event_name, broadcasted_data, broadcast=True, namespace=name_space)
        print('Already sent competitor!')
        
@socketio.on('disconnect', namespace=name_space)
def disconnect_msg():
    """socket client event - disconnected"""
    print('client disconnected!')

if __name__ == '__main__':
    socketio.run(app, debug=True)




