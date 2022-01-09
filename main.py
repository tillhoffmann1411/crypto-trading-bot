import websocket, json, numpy as np, talib, pprint, os, yaml
from binance.enums import *
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, yaml.Loader)

API_KEY = os.environ.get('BINANCE_KEY')
API_SECRET = os.environ.get('BINACNE_SECRET')

RSI_PERIOD = int(cfg['RSI_PERIOD'])
OVERSOLD_THRESHOLD = int(cfg['OVERSOLD_THRESHOLD'])
OVERBOUGHT_THRESHOLD = int(cfg['OVERBOUGHT_THRESHOLD'])
TRADE_SYMBOL = cfg['TRADE_SYMBOL']
TRADE_QUNATITY = float(cfg['TRADE_QUNATITY'])
CANDLE_INTERVAL = cfg['CANDLE_INTERVAL']
SOCKET = 'wss://stream.binance.com:9443/ws/{}@kline_{}'.format(TRADE_SYMBOL.lower(), CANDLE_INTERVAL)
COIN = TRADE_SYMBOL[0:3]
STABLE = TRADE_SYMBOL[-3:]

closes = []
in_position = False
client = Client(API_KEY, API_SECRET)

def order(quantity, symbol, side, order_type=ORDER_TYPE_MARKET):
    try:
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print('order')
    except Exception as e:
        print('Error!')
        print(e)
        return False
    return True
        
        
def on_open(ws):
    print('opened connection...')
    print('Candle Interval: {}'.format(CANDLE_INTERVAL))
    print('RSI Period: {}'.format(RSI_PERIOD))
    print('Oversold by: {}'.format(OVERSOLD_THRESHOLD))
    print('Overbought by: {}'.format(OVERBOUGHT_THRESHOLD))
    print('Traded symbol: {}'.format(TRADE_SYMBOL))
    print('Traded quantity: {}'.format(TRADE_QUNATITY))
    
def on_message(ws, message):
    global closes, in_position 
    json_msg = json.loads(message)    
    candle = json_msg['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        
        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            print(last_rsi)
            closes.append(float(close))
            
            eth_balance = client.get_asset_balance(asset=COIN)['free']
            eur_balance = client.get_asset_balance(asset=STABLE)['free']
            price_for_one_trade = round(float(close) * float(TRADE_QUNATITY), 3)
            
            if last_rsi > OVERBOUGHT_THRESHOLD and eth_balance >= TRADE_QUNATITY and in_position:
                print("Sell {} {} for: {}".format(TRADE_QUNATITY, COIN, price_for_one_trade))
                succeeded = order(quantity=TRADE_QUNATITY, symbol=TRADE_SYMBOL, side=SIDE_SELL)
                if succeeded:
                    in_position = False
            
            if last_rsi < OVERSOLD_THRESHOLD and eur_balance >= price_for_one_trade and not in_position:
                print("Buy {} {} for: {} €".format(TRADE_QUNATITY, COIN, price_for_one_trade))
                succeeded = order(quantity=TRADE_QUNATITY, symbol=TRADE_SYMBOL, side=SIDE_BUY)
                if succeeded:
                    in_position = True
    
def on_close(ws, close_status_code, close_msg):
    print('closed connection')
    print('Status Code ' + str(close_status_code) + ' ' + close_msg)

def on_error(ws, error):
    print('error: ' + str(error))


if __name__ == "__main__":    
    ws = websocket.WebSocketApp(SOCKET,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()