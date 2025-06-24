import streamlit as st
from firebase_config import login_with_firebase, save_insight, check_usage
import os
import requests
from openai import AzureOpenAI
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Azure OpenAI setup
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-07-01-preview"
)

# UI Config
st.set_page_config(page_title="MarketMind", layout="centered", page_icon="📊")
st.markdown("""
    <style>
        .buy {color: green; font-size: 26px; font-weight: bold;}
        .hold {color: orange; font-size: 26px; font-weight: bold;}
        .sell {color: red; font-size: 26px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# Firebase Login
user = login_with_firebase()
if not user:
    st.stop()

# Title and Form
st.image("logo.png", width=100)
st.title("📊 MarketMind - Crypto & Stock Sentiment Bot")
ticker = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):")
analyze = st.button("Analyze Sentiment")

# Crypto Symbol Map
def map_symbol_to_coingecko_id(symbol):
    return {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "XRP": "ripple",
        "DOGE": "dogecoin"
    }.get(symbol.upper())

# Chart Generator
def get_price_chart(symbol):
    coingecko_id = map_symbol_to_coingecko_id(symbol)
    if coingecko_id:
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart?vs_currency=usd&days=1"
        data = requests.get(url).json()
        prices = data.get("prices", [])
        if prices:
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
            df.set_index("timestamp", inplace=True)
            return df
    else:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="1d", interval="5m")
            if not df.empty:
                return df.rename(columns={"Close": "price"})[["price"]]
        except:
            return None
    return None

# Main Logic
if analyze and ticker:
    usage = check_usage(user["uid"])
    if usage >= 10:
        st.warning("🚧 Free limit reached. Subscribe for unlimited access.")
        st.markdown("[Subscribe Here](https://your-stripe-checkout-url)")
        st.stop()

    headlines = f"Recent news about {ticker.upper()}: price fluctuation, market sentiment, trading volume."
    prompt = f"Summarize recent crypto or stock sentiment for {ticker.upper()}. News: {headlines}. Provide a summary, sentiment score (0-100), and Buy/Sell/Hold advice."

    try:
        response = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content

        # Basic Recommendation Detection
        lower_result = result.lower()
        if "buy" in lower_result:
            rec = "Buy"
        elif "sell" in lower_result:
            rec = "Sell"
        else:
            rec = "Hold"

        emoji = {"Buy": "🟢", "Hold": "🟠", "Sell": "🔴"}[rec]
        color_class = rec.lower()
        st.markdown(f"<div class='{color_class}'>{emoji} {rec} recommendation for {ticker.upper()}</div>", unsafe_allow_html=True)
        st.write(result)

        df = get_price_chart(ticker.upper())
        if df is not None:
            st.subheader(f"📈 Intraday Price for {ticker.upper()}")
            fig, ax = plt.subplots()
            df["price"].plot(ax=ax, color="skyblue", linewidth=2)
            ax.set_title(f"{ticker.upper()} - {datetime.now().strftime('%Y-%m-%d')}")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price (USD)")
            st.pyplot(fig)
        else:
            st.warning("📉 No price data found. May be an unsupported symbol on CoinGecko or Yahoo Finance.")

        save_insight(user["uid"], ticker, result)

    except Exception as e:
        st.error(f"❌ Error: {e}")