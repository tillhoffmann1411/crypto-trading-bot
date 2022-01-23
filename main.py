import websocket, json, numpy as np, talib, pprint, os, yaml, datetime
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

def order(quantity, price, symbol, side, order_type=ORDER_TYPE_LIMIT):
    try:
        order = order = client.create_margin_order(
            symbol=symbol,
            side=side,
            type=order_type,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=str(price - 0.01),
            stopPrice=str(price + 0.01)
        )
        log('ordered:')
        pprint.pprint(order)
    except Exception as e:
        log('Error!')
        log(e)
        return False
    return True
        
        
def on_open(ws):
    print('opened connection')
    print('  - Candle Interval: {}'.format(CANDLE_INTERVAL))
    print('  - RSI Period: {}'.format(RSI_PERIOD))
    print('  - Oversold by: {}'.format(OVERSOLD_THRESHOLD))
    print('  - Overbought by: {}'.format(OVERBOUGHT_THRESHOLD))
    print('  - Traded symbol: {}'.format(TRADE_SYMBOL))
    print('  - Traded quantity: {}'.format(TRADE_QUNATITY))
    print('  - Data stream from: {}'.format(SOCKET))
    print('_________________________________________________')
    log('Started running...')
    
def on_message(ws, message):
    global closes, in_position 
    json_msg = json.loads(message)    
    candle = json_msg['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        closes.append(float(close))
        log("closes length: {}".format(len(closes)))
        
        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            log("last rsi {}".format(last_rsi))
            
            eth_balance = float(client.get_asset_balance(asset=COIN)['free'])
            eur_balance = float(client.get_asset_balance(asset=STABLE)['free'])
            price_for_one_trade = round(float(close) * float(TRADE_QUNATITY), 3)
            
            if last_rsi > OVERBOUGHT_THRESHOLD:
                if eth_balance >= TRADE_QUNATITY and in_position:
                    log("Sell {} {} for: {}".format(TRADE_QUNATITY, COIN, price_for_one_trade))
                    succeeded = order(quantity=TRADE_QUNATITY, price=price_for_one_trade, symbol=TRADE_SYMBOL, side=SIDE_SELL)
                    if succeeded:
                        in_position = False
                else:
                    log('Tried to sell, but:')
                    if not (eth_balance >= TRADE_QUNATITY):
                        log("  - There are not enough {} coins in your account!".format(COIN))
                    if not in_position:
                        log("  - We are already in the position")
            
            if last_rsi < OVERSOLD_THRESHOLD:
                if eur_balance >= price_for_one_trade and not in_position:
                    log("Buy {} {} for: {} €".format(TRADE_QUNATITY, COIN, price_for_one_trade))
                    succeeded = order(quantity=TRADE_QUNATITY, price=price_for_one_trade, symbol=TRADE_SYMBOL, side=SIDE_BUY)
                    if succeeded:
                        in_position = True
                else:
                    log('Tried to buy, but:')
                    if not (eur_balance >= price_for_one_trade):
                        log("  - There are not enough {} in your account!".format(STABLE))
                    if in_position:
                        log("  - We are not in the position")
    
def on_close(ws, close_status_code, close_msg):
    log('closed connection')
    log('Status Code ' + str(close_status_code) + ' ' + close_msg)

def on_error(ws, error):
    log('error: ' + str(error))
    
def log(msg):
    print("{} - {}".format(str(datetime.datetime.now()), msg))


if __name__ == "__main__":
    ws = websocket.WebSocketApp(SOCKET,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()