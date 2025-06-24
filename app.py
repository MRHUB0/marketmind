import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit App Configuration
st.set_page_config(page_title="Market Mind", layout="wide", page_icon="📊")

# App Header
st.markdown("<h1 style='text-align: center;'>📊 Market Mind</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>AI-powered crypto & stock sentiment bot</h4>", unsafe_allow_html=True)

# User Input
symbol = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):")
submit = st.button("Analyze")

# Function to fetch sentiment
def get_sentiment_recommendation(ticker):
    prompt = f"You're an expert financial advisor. Based on recent market sentiment, would you recommend buying, holding, or selling {ticker}? Respond with one word: Buy, Hold, or Sell."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip().capitalize()

# Function to fetch historical price data
def get_price_chart(ticker):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end)
        if hist.empty:
            return None
        return hist
    except:
        return None

# Map recommendation to color and emoji
def style_recommendation(rec):
    emoji = {"Buy": "🟢", "Hold": "🟠", "Sell": "🔴"}.get(rec, "❓")
    color = {"Buy": "green", "Hold": "orange", "Sell": "red"}.get(rec, "gray")
    styled = f"<h2 style='text-align: center; color: {color};'>{emoji} Recommendation: {rec}</h2>"
    return styled

# Main logic
if submit and symbol:
    st.markdown(f"<h3 style='text-align: center;'>Analyzing {symbol.upper()}...</h3>", unsafe_allow_html=True)

    # Get recommendation
    recommendation = get_sentiment_recommendation(symbol)
    st.markdown(style_recommendation(recommendation), unsafe_allow_html=True)

    # Get price chart
    hist = get_price_chart(symbol)
    if hist is not None:
        st.markdown(f"<h4 style='margin-top: 40px;'>📈 Price Chart (Last 30 Days) for {symbol.upper()}</h4>", unsafe_allow_html=True)
        fig, ax = plt.subplots()
        ax.plot(hist.index, hist['Close'], color="skyblue")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.set_title(f"{symbol.upper()} - 30 Day Price Trend")
        st.pyplot(fig)
    else:
        st.warning("❌ No price data found. This may not be a supported ticker.")