import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# Load .env variables (if running locally)
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Market Mind", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 Market Mind</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>AI-powered crypto & stock sentiment bot</h3>", unsafe_allow_html=True)

ticker_input = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):", value="")

def get_sentiment_recommendation(ticker):
    prompt = f"You are a financial sentiment analyst. Would you recommend buying, holding, or selling {ticker} today? Reply with only one word: Buy, Hold, or Sell."
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        sentiment = response.choices[0].message.content.strip().capitalize()
        return sentiment
    except Exception as e:
        return f"Error: {e}"

def get_crypto_price_data(ticker):
    url = f"https://api.coingecko.com/api/v3/coins/{ticker.lower()}/market_chart?vs_currency=usd&days=1&interval=hourly"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    prices = r.json().get("prices", [])
    return [(datetime.fromtimestamp(p[0] / 1000), p[1]) for p in prices]

def plot_price_chart(data, label):
    times, values = zip(*data)
    fig, ax = plt.subplots()
    ax.plot(times, values, marker='o', linewidth=2)
    ax.set_title(f"Intraday Price for {label.upper()}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price (USD)")
    ax.grid(True)
    st.pyplot(fig)

def show_recommendation(rec):
    color_map = {"Buy": "green", "Hold": "orange", "Sell": "red"}
    emoji_map = {"Buy": "🟢", "Hold": "🟠", "Sell": "🔴"}
    color = color_map.get(rec, "gray")
    emoji = emoji_map.get(rec, "❓")
    st.markdown(
        f"<h2 style='text-align:center; color:{color};'>Recommendation: {rec} {emoji}</h2>",
        unsafe_allow_html=True
    )

if st.button("Analyze") and ticker_input:
    st.subheader(f"🔍 Analyzing {ticker_input.upper()}...")

    # Get recommendation
    recommendation = get_sentiment_recommendation(ticker_input)
    show_recommendation(recommendation)

    # Try crypto price chart
    crypto_data = get_crypto_price_data(ticker_input)
    if crypto_data:
        plot_price_chart(crypto_data, ticker_input)
    else:
        # Fallback to stock price if not a crypto
        try:
            stock = yf.Ticker(ticker_input.upper())
            hist = stock.history(period="1d", interval="1h")
            if not hist.empty:
                st.subheader(f"📈 Intraday Price for {ticker_input.upper()}")
                fig, ax = plt.subplots()
                ax.plot(hist.index, hist["Close"], marker='o')
                ax.set_title(f"Intraday Price for {ticker_input.upper()}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Price (USD)")
                st.pyplot(fig)
            else:
                st.info("No price data found for this symbol.")
        except Exception as e:
            st.error(f"Failed to fetch price data: {e}")