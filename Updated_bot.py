#UPDATED 2024 EDITION (ENJOY THE CODE)

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import alpaca_trade_api as tradeapi
from datetime import datetime

#If you want to trade on paper trading follow this additional step

API_KEY = 'PKUNA5TMMMBFZUM1BHLV'
SECRET_KEY = 'tKJaiBcC17Daq1WbjH2jZwKJ7w7QsLnnLASo24d5'
BASE_URL = 'https://paper-api.alpaca.markets'

# Create an instance of the Alpaca API
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# Download historical data
data = yf.download('EURJPY=X', start="2016-01-01", end="2024-12-31")

def calculate_indicators(data):
    # Exponential Moving Averages
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    # Relative Strength Index
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

data = calculate_indicators(data)

def generate_signals(data):
    # Buy and Sell signals based on EMA and RSI
    pd.set_option('future.no_silent_downcasting', True)
    data['Signal'] = 0
    buy_signal = (data['EMA_12'] > data['EMA_26']) & (data['RSI'] < 30)
    sell_signal = (data['EMA_12'] < data['EMA_26']) & (data['RSI'] > 70)
    data.loc[buy_signal, 'Signal'] = 1
    data.loc[sell_signal, 'Signal'] = -1
    data['Position'] = (data['Signal'].replace(to_replace=0, value=None).ffill().astype(float))
    data['Signal'] = data['Signal'].fillna(0).astype(int)

    return data

data = generate_signals(data)
print(data.Signal.unique())
def backtest(data, initial_balance=10000):
    balance = initial_balance
    position = 0
    stop_loss = 0.95
    take_profit = 1.2
    entry_price = 0

    for i, row in data.iterrows():
        signal = row.Signal.iloc[0]
        close_price = row.Close.iloc[0]
        # print(type(row['Signal']), type(row['Close']))
        if signal  == 1 and balance > 0:
            position = balance / close_price
            balance = 0
            entry_price = close_price
            logging.info(f"BUY at {row['Close']} on {row.name.date()}")
        elif signal == -1 and position != 0:
            balance = position * close_price
            position = 0
            logging.info(f"SELL at {close_price} on {row.name.date()}")
            entry_price = 0

        if position != 0:
            if close_price <= entry_price * stop_loss:
                balance = position * close_price
                position = 0
                logging.info(f"STOP LOSS at {close_price} on {row.name.date()}")
            elif close_price >= entry_price * take_profit:
                balance = position * close_price
                position = 0
                logging.info(f"TAKE PROFIT at {close_price} on {row.name.date()}")

    if position != 0:
        balance = position * data.iloc[-1]['Close'].values[0]  # Close position at the last available price

    return balance

logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

final_balance = backtest(data)
print(f"Final Balance: ${final_balance:.2f}")
# print(final_balance.values)

