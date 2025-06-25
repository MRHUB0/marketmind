import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env (for local testing)
load_dotenv()

# Validate Azure OpenAI environment setup
if not all([os.getenv("AZURE_OPENAI_API_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"), os.getenv("AZURE_OPENAI_DEPLOYMENT")]):
    st.error("❌ Azure OpenAI environment variables missing. Please check your configuration.")
    st.stop()

# Azure OpenAI Client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-05-01-preview"
)

# Streamlit UI Setup
st.set_page_config(page_title="Market Mind", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 Market Mind</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>AI-powered crypto & stock sentiment bot</h3>", unsafe_allow_html=True)

# User Input
ticker_input = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):", value="")

if st.button("Analyze") and ticker_input:
    ticker_symbol = ticker_input.upper()
    st.markdown(f"🔍 **Analyzing {ticker_symbol}...**")

    # Azure OpenAI Sentiment Analysis
    try:
        prompt = f"You are a financial sentiment analyst. Would you recommend buying, holding, or selling {ticker_symbol} today? Reply with a one-sentence recommendation."

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # Must match the model deployment name in Azure
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )

        recommendation = response.choices[0].message.content.strip()
        st.markdown(f"📊 **Recommendation:** {recommendation}")

    except Exception as e:
        st.error(f"❌ Azure OpenAI Error: {e}")

    # Price Data from yfinance
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d", interval="15m")
        if hist.empty:
            st.warning("⚠️ No intraday data found for this symbol.")
        else:
            st.markdown(f"📈 **Intraday Price for {ticker_symbol}**")
            fig, ax = plt.subplots()
            ax.plot(hist.index, hist["Close"], marker='o', linestyle='-')
            ax.set_title(f"{ticker_symbol} Intraday Price")
            ax.set_xlabel("Time")
            ax.set_ylabel("Price (USD)")
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Chart Error: {e}")
