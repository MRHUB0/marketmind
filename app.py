import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime, timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load local .env if running locally
load_dotenv()

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",  # Change if you're using a different API version
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

# Streamlit UI
st.set_page_config(page_title="Market Mind", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 Market Mind</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>AI-powered crypto & stock sentiment bot</h3>", unsafe_allow_html=True)

ticker_input = st.text_input("Enter a crypto or stock ticker (e.g. BTC, ETH, TSLA):", value="")

if st.button("Analyze") and ticker_input:
    st.markdown(f"🔍 **Analyzing {ticker_input.upper()}...**")
    
    try:
        # AI recommendation from Azure OpenAI
        prompt = f"You are a financial sentiment analyst. Would you recommend buying, holding, or selling {ticker_input.upper()} today? Reply with a one-sentence recommendation."
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # this must match your deployment name
            messages=[{"role": "system", "content": "You are a financial analyst."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        ai_reply = response.choices[0].message.content.strip()
        st.markdown(f"📊 **Recommendation:** {ai_reply}")
    
    except Exception as e:
        st.error(f"Recommendation: ❌ Error - {e}")

    # Show intraday stock/crypto data using yfinance
    try:
        ticker = yf.Ticker(ticker_input)
        hist = ticker.history(period="1d", interval="15m")
        if hist.empty:
            st.warning("No intraday data found for this ticker.")
        else:
            st.markdown(f"📈 **Intraday Price for {ticker_input.upper()}**")
            plt.figure()
            plt.plot(hist.index, hist['Close'], marker='o')
            plt.title(f"Intraday Price for {ticker_input.upper()}")
            plt.xlabel("Time")
            plt.ylabel("Price (USD)")
            plt.xticks(rotation=45)
            st.pyplot(plt.gcf())
    except Exception as e:
        st.error(f"Price chart error: {e}")
