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

def get_token_holders(token_address, chain_id):
    if chain_id == "solana":
        url = f"https://solana-gateway.moralis.io/token/mainnet/{token_address}/top-holders?limit=100"
        headers = {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
        }
        try:
            result = requests.request("GET", url, headers=headers)
            result = result.json()
            print(result['result'][0].keys())
            return result['result']
        except Exception as e:
            st.error(f"❌ Error fetching token holders: {e}")
            return []
        
    if chain_id == "ethereum":
        chain_id = "eth"

    params = {
        "chain": chain_id,
        "order": "DESC",
        "token_address": token_address
    }
    try:
        result = evm_api.token.get_token_owners(
            api_key=MORALIS_API_KEY,
            params=params,
        )
        print(result['result'][0].keys())
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
    

def normalize_holder_entry(holder: dict, chain_id: str) -> dict:
                if chain_id == "solana":
                    return {
                        "address": holder.get("ownerAddress"),
                        "percent": holder.get("percentageRelativeToTotalSupply")
                    }
                else:
                    return {
                        "address": holder.get("owner_address"),
                        "percent": holder.get("percentage_relative_to_total_supply")
                    }