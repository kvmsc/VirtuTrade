import requests
import json
from app import app

def get_quote(ticker, token=app.config['APIKEY']):
    url = "https://cloud.iexapis.com/stable/stock/{}/quote?token={}".format(ticker.lower(),token)
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return json.loads(resp.content)

def get_quote_latest(ticker, token=app.config['APIKEY']):
    url = "https://cloud.iexapis.com/stable/stock/{}/quote/latestPrice?token={}".format(ticker.lower(),token)
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    return float(resp.content)
