import krakenex
from pykrakenapi import KrakenAPI
from pykrakenapi.pykrakenapi import KrakenAPIError
import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

API_KEY = os.environ.get('KRAKEN_KEY')
API_SECRET = os.environ.get('KRAKEN_SECRET')

api = krakenex.API(key=API_KEY, secret=API_SECRET)
k = KrakenAPI(api, crl_sleep=1, retry=2)

class Kraken:
    def open_sell_order(self, pair, volume, leverage, expire_time, limit=True):
        try:
            if limit:
                k.add_standard_order(pair=pair, type="sell", ordertype="limit", oflags="post",
                                    price="+0.0004%", expiretm="+%i" % expire_time, volume=volume, leverage=leverage, validate=False)
                self.log("%s - Limit Margin Sell Order for %s at opentime %s" % (
                    pair, volume, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            else:
                k.add_standard_order(pair=pair, type="sell", ordertype="market", volume=volume, leverage=leverage, validate=False)
                self.log("%s - Market Sell Order at opentime %s" % (
                    pair, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

        except KrakenAPIError as err:
            raise err


    def open_buy_order(self, pair, volume, leverage, expire_time, limit=True):
        try:
            if limit:
                k.add_standard_order(pair=pair, type="buy", ordertype="limit", oflags="post",
                                    price="-0.0004%", expiretm="+%i" % expire_time, volume=volume, leverage=leverage, validate=False)
                self.log("%s - Limit Margin Buy Order for %s at opentime %s" % (
                    pair, volume, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            else:
                k.add_standard_order(pair=pair, type="buy", ordertype="market", volume=volume, leverage=leverage, validate=False)
                self.log("%s - Market Margin Buy Order at the opentime %s" % (
                    pair, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
        except KrakenAPIError as err:
            raise err

    def log(self, msg):
        print("{} - {}".format(str(datetime.datetime.now()), msg))