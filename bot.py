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
data = yf.download("EURJPY=X", start="2024-01-01", end="2024-12-01")


###
def calculate_indicators(data):
    # Exponential Moving Averages
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    # data['EMA_12'] = data['Close'].ewm(span=15, adjust=False).mean()
    # data['EMA_26'] = data['Close'].ewm(span=50, adjust=False).mean()
    # Relative Strength Index
    delta = data['Close'].diff()
    # gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    # loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
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
    data['Position'] = data['Signal'].replace(to_replace=0, value=None).ffill()
    data['Signal'] = data['Signal'].fillna(0).astype(int)

    return data

# def generate_signals(data):
#     """
#     Generate buy and sell signals based purely on price action.
#     Criteria:
#       - Buy Signal: 3 consecutive bearish candles followed by a bullish candle 
#         with a wick at least 50% of the candle body to the downside.
#       - Sell Signal: 3 consecutive bullish candles followed by a bearish candle 
#         with a wick at least 50% of the candle body to the upside.
#     """
#     # Calculate candle attributes
#     data['Candle_Body'] = abs(data['Close'] - data['Open'])
#     data['Lower_Wick'] = abs(data['Low'] - data[['Close', 'Open']].min(axis=1))
#     data['Upper_Wick'] = abs(data['High'] - data[['Close', 'Open']].max(axis=1))
#     data['Candle_Type'] = data['Close'] > data['Open']  # True for bullish, False for bearish

#     # Identify three consecutive bearish and bullish candles
#     # Identify three consecutive bearish and bullish candles
#     # data['Bearish_3'] = data['Candle_Type'].rolling(window=3).apply(lambda x: all(~x), raw=True).shift(1)
#     # data['Bullish_3'] = data['Candle_Type'].rolling(window=3).apply(lambda x: all(x), raw=True).shift(1)
#     data['Bearish_3'] = (
#         data['Candle_Type']
#         .rolling(window=3)
#         .apply(lambda x: all(not val for val in x), raw=False)
#         .shift(1)
#         )

#     data['Bullish_3'] = (
#         data['Candle_Type']
#           .rolling(window=3)
#           .apply(lambda x: all(val for val in x), raw=False)
#           .shift(1)
#           )

#     # Check for bullish and bearish signals
#     data['Bullish_Signal'] = data['Bearish_3'] & (data['Candle_Type']) & (data['Lower_Wick'] >= 0.5 * data['Candle_Body'])
#     data['Bearish_Signal'] = data['Bullish_3'] & (~data['Candle_Type']) & (data['Upper_Wick'] >= 0.5 * data['Candle_Body'])

#     # Combine signals into one column
#     data['Signal'] = 0
#     data.loc[data['Bullish_Signal'], 'Signal'] = 1
#     data.loc[data['Bearish_Signal'], 'Signal'] = -1

#     # Calculate position based on signal
#     data['Position'] = data['Signal'].replace(to_replace=0, value=None).ffill()
#     data['Signal'] = data['Signal'].fillna(0).astype(int)

#     # Drop intermediate columns for cleanliness (optional)
#     data = data.drop(['Candle_Body', 'Lower_Wick', 'Upper_Wick', 'Candle_Type', 'Bearish_3', 'Bullish_3', 
#                       'Bullish_Signal', 'Bearish_Signal'], axis=1)
    
#     return data

data = generate_signals(data)

def backtest(data, initial_balance=10000):
    balance = initial_balance
    position = 0
    stop_loss = 0.95
    take_profit = 2.0
    entry_price = 0

    for i, row in data.iterrows():
        if row['Signal'] == 1 and balance != 0:
            position = balance / row['Close']
            balance = 0
            entry_price = row['Close']
            logging.info(f"BUY at {row['Close']} on {row.name.date()}")
        elif row['Signal'] == -1 and position != 0:
            balance = position * row['Close']
            position = 0
            logging.info(f"SELL at {row['Close']} on {row.name.date()}")
            entry_price = 0

        if position != 0:
            if row['Close'] <= entry_price * stop_loss:
                balance = position * row['Close']
                position = 0
                logging.info(f"STOP LOSS at {row['Close']} on {row.name.date()}")
            elif row['Close'] >= entry_price * take_profit:
                balance = position * row['Close']
                position = 0
                logging.info(f"TAKE PROFIT at {row['Close']} on {row.name.date()}")

    if position != 0:
        balance = position * data.iloc[-1]['Close']  # Close position at the last available price

    return balance

logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

final_balance = backtest(data)
print(final_balance)


