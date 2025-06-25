import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Azure OpenAI setup
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

st.set_page_config(page_title="Market Mind", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 Market Mind</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>AI-powered crypto & stock sentiment bot</h3>", unsafe_allow_html=True)

# Trending symbols
trending_buys = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN"]
trending_sells = ["COIN", "NIO", "GME", "BYND", "PLTR"]

st.markdown("### 🔥 Trending Now")
col1, col2 = st.columns(2)
ticker_input = ""

with col1:
    st.markdown("#### 🟢 Top Buys")
    for symbol in trending_buys:
        if st.button(symbol, key=f"buy_{symbol}"):
            ticker_input = symbol

with col2:
    st.markdown("#### 🔴 Top Sells")
    for symbol in trending_sells:
        if st.button(symbol, key=f"sell_{symbol}"):
            ticker_input = symbol

manual_input = st.text_input("Or enter a crypto or stock ticker:", "")
if manual_input:
    ticker_input = manual_input

def show_recommendation(rec_text):
    color_map = {"Buy": "green", "Hold": "orange", "Sell": "red"}
    emoji_map = {"Buy": "🟢", "Hold": "🟠", "Sell": "🔴"}
    for keyword in ["Buy", "Hold", "Sell"]:
        if keyword in rec_text:
            st.markdown(f"<h2 style='text-align:center; color:{color_map[keyword]};'>Recommendation: {keyword} {emoji_map[keyword]}</h2>", unsafe_allow_html=True)
            break
    st.write(rec_text)

def get_sentiment(ticker):
    prompt = f"You are a financial sentiment analyst. Would you recommend buying, holding, or selling {ticker.upper()} today? Reply with a one-sentence recommendation."
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def get_crypto_prices(ticker):
    url = f"https://api.coingecko.com/api/v3/coins/{ticker.lower()}/market_chart?vs_currency=usd&days=1&interval=hourly"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    prices = r.json().get("prices", [])
    return [(datetime.fromtimestamp(p[0] / 1000), p[1]) for p in prices]

def plot_chart(data, title):
    times, prices = zip(*data)
    fig, ax = plt.subplots()
    ax.plot(times, prices, marker='o')
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Price (USD)")
    ax.grid(True)
    st.pyplot(fig)

if ticker_input:
    st.markdown(f"🔍 **Analyzing {ticker_input.upper()}...**")
    rec = get_sentiment(ticker_input)
    show_recommendation(rec)

    # Try crypto chart first
    crypto_data = get_crypto_prices(ticker_input)
    if crypto_data:
        plot_chart(crypto_data, f"📈 Intraday Price for {ticker_input.upper()}")
    else:
        try:
            stock = yf.Ticker(ticker_input.upper())
            hist = stock.history(period="1d", interval="15m")
            if not hist.empty:
                fig, ax = plt.subplots()
                ax.plot(hist.index, hist["Close"], marker='o')
                ax.set_title(f"📈 Intraday Price for {ticker_input.upper()}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Price (USD)")
                ax.grid(True)
                st.pyplot(fig)
            else:
                st.info("No price data found.")
        except Exception as e:
            st.error(f"Chart Error: {e}")