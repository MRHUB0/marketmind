import streamlit as st
from firebase_config import login_with_firebase, save_insight, check_usage
import os
import requests
from openai import AzureOpenAI
import json

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

ticker = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):")
analyze = st.button("Analyze")

if analyze and ticker:
    usage = check_usage(user["uid"])
    if usage >= 5:
        st.warning("🚧 Free limit reached. Please subscribe for unlimited access.")
        st.markdown("[Subscribe Here](https://your-stripe-checkout-url)")
        st.stop()

    # Simulated news (replace w/ real API later)
    headlines = f"Recent news about {ticker}: price fluctuation, market sentiment, trading volume."

    prompt = f"Summarize recent crypto/stock sentiment for {ticker}. News: {headlines}. Provide a summary, sentiment score, and Buy/Sell/Hold advice."

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content
        st.success("✅ Analysis Complete")
        st.write(result)

        save_insight(user["uid"], ticker, result)

    except Exception as e:
        st.error(f"Error: {e}")
