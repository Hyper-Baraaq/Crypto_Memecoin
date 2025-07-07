import re
import requests
import streamlit as st
from moralis import evm_api
from datetime import datetime
from dotenv import dotenv_values

config = dotenv_values(".env")

MORALIS_API_KEY = config["MORALIS_API_KEY"]

# Extract chain and token from DexScreener URL
def extract_chain_and_token(link):
    pattern = r"https?://dexscreener\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, link)
    if match:
        return match.group(1), match.group(2)
    else:
        raise ValueError("Invalid DexScreener URL format.")

# Fetch from API
def fetch_data(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"❌ Failed to fetch from {url}")
        st.code(response.text)
        return None

def get_token_holders(token_address):
    params = {
        "token_address": token_address
    }
    try:
        result = evm_api.token.get_token_owners(
            api_key=MORALIS_API_KEY,
            params=params,
        )
        return result['result']
    except Exception as e:
        st.error(f"❌ Error fetching token holders: {e}")
        return []

# Format timestamp to readable time
def format_timestamp(ms):
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "N/A"