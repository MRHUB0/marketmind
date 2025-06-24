import streamlit as st
from firebase_config import login_with_firebase, save_insight, check_usage
import os
import requests
from openai import AzureOpenAI
import json
import pandas as pd
import time

# Azure OpenAI setup
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-07-01-preview"
)

st.set_page_config(page_title="MarketMind", layout="centered")

# Firebase login
user = login_with_firebase()
if not user:
    st.stop()

st.title("📊 MarketMind - Crypto & Stock Sentiment Bot")

ticker = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):").upper()

# Placeholder for animated transition
recommendation_container = st.empty()

# Check previous result
if "result" not in st.session_state:
    st.session_state.result = ""
if "recommendation" not in st.session_state:
    st.session_state.recommendation = ""
if "color" not in st.session_state:
    st.session_state.color = ""
if "emoji" not in st.session_state:
    st.session_state.emoji = ""

# Display prior recommendation
if st.session_state.recommendation:
    recommendation_container.markdown(
        f"""<div style='font-size:24px; font-weight:bold; color:{st.session_state.color}; 
             transition: all 0.5s ease-in-out'>
            📈 {ticker} — <span>{st.session_state.recommendation} {st.session_state.emoji}</span>
        </div><hr>""",
        unsafe_allow_html=True
    )

# Analyze button
if st.button("Analyze") and ticker:
    usage = check_usage(user["uid"])
    if usage >= 5:
        st.warning("🚧 Free limit reached. Please subscribe for unlimited access.")
        st.markdown("[Subscribe Here](https://your-stripe-checkout-url)")
        st.stop()

    headlines = f"Recent news about {ticker}: price fluctuation, market sentiment, trading volume."

    prompt = (
        f"Summarize recent crypto/stock sentiment for {ticker}. "
        f"News: {headlines}. "
        "Provide a summary, sentiment score (1-10), and clear Buy, Sell, or Hold recommendation."
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content.lower()

        # Detect recommendation
        recommendation = "Hold"
        color = "orange"
        emoji = "⚖️"
        if "buy" in result:
            recommendation = "Buy"
            color = "green"
            emoji = "🟢"
        elif "sell" in result:
            recommendation = "Sell"
            color = "red"
            emoji = "🔴"

        # Save state
        st.session_state.result = result
        st.session_state.recommendation = recommendation
        st.session_state.color = color
        st.session_state.emoji = emoji

        # Animated color change
        for _ in range(3):
            recommendation_container.markdown(
                f"""<div style='font-size:24px; font-weight:bold; color:{color}; 
                     transition: all 0.5s ease-in-out'>
                    📈 {ticker} — <span>{recommendation} {emoji}</span>
                </div><hr>""",
                unsafe_allow_html=True
            )
            time.sleep(0.3)

        save_insight(user["uid"], ticker, result)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# Full analysis output
if st.session_state.result:
    st.subheader("📄 Full Analysis")
    st.write(st.session_state.result)

# Real-time price chart
def get_price_chart(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart?vs_currency=usd&days=1"
        res = requests.get(url).json()
        prices = res.get("prices", [])
        if not prices:
            return None
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except:
        return None

# Display chart if crypto
if ticker:
    st.subheader(f"📉 Intraday Price for {ticker}")
    price_data = get_price_chart(ticker)
    if price_data is not None:
        st.line_chart(price_data["price"])
    else:
        st.info("No price data found. This may not be a supported crypto on CoinGecko.")