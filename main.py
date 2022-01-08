import websocket, json, numpy as np, talib, pprint, os
from binance.enums import *
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

API_KEY = os.environ.get('BINANCE_KEY')
API_SECRET = os.environ.get('BINACNE_SECRET')
TEST_API_KEY = os.environ.get('BINANCE_KEY_TEST')
TEST_API_SECRET = os.environ.get('BINACNE_SECRET_TEST')

RSI_PERIOD = 14
OVERSOLD_THRESHOLD = 30
OVERBOUGHT_THRESHOLD = 70
TRADE_SYMBOL = 'ETHEUR'
TRADE_QUNATITY = 0.0072
SOCKET = 'wss://stream.binance.com:9443/ws/etheur@kline_1m'

closes = []
in_position = False
client = Client(TEST_API_KEY, TEST_API_SECRET, testnet=True)

def order(quantity, symbol, side, order_type=ORDER_TYPE_MARKET, test=True):
    try:
        order = None
        if test:
            order = client.create_test_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        else:
            order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print('Error!')
        print(e)
        return False
    return True
        
        
def on_open(ws):
    print('opened connection')
    
def on_message(ws, message):
    global closes, in_position
    print('received message')
    
    json_msg = json.loads(message)    
    candle = json_msg['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        closes.append(float(close))
        
        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print(rsi)
            last_rsi = rsi[-1]
            print(last_rsi)
            
            if last_rsi > OVERBOUGHT_THRESHOLD and in_position:
                print('Sell!!!')
                succeeded = order(quantity=TRADE_QUNATITY, symbol=TRADE_SYMBOL, side=SIDE_SELL)
                if succeeded:
                    in_position = False
            
            if last_rsi < OVERSOLD_THRESHOLD and not in_position:
                print('Buy!!!')
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