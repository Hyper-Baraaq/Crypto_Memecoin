import requests
import streamlit as st
from moralis import evm_api
from dotenv import dotenv_values
from config import HEADERS

# load your MORALIS_API_KEY from .env
config = dotenv_values(".env")
MORALIS_API_KEY = config.get("MORALIS_API_KEY", "")
WHOIS_API_KEY = config.get("WHOIS_API_KEY", "")

######### DEXScreener & MOLARIS ######### 

def fetch_data(url, headers=HEADERS, params= None):
    if params:
        resp = requests.get(url, params=params)
    else:
        resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"❌ Failed to fetch from {url}")
        st.code(resp.text)
        return None

def fetch_pair_data(chain_id, pair_address):
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}"
    data = fetch_data(url)
    if data and data.get("pairs"):
        return data["pairs"][0]
    else:
        st.warning("No pair data found.")
        return None

def fetch_token_pairs(chain_id, token_address):
    url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
    return fetch_data(url)

def get_token_holders(token_address, chain_id):
    if chain_id == "solana":
        url = f"https://solana-gateway.moralis.io/token/mainnet/{token_address}/top-holders?limit=100"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        try:
            return requests.get(url, headers=headers).json().get("result", [])
        except Exception as e:
            st.error(f"❌ Error fetching token holders: {e}")
            return []
    # for EVM chains
    params = {"chain": chain_id if chain_id != "ethereum" else "eth",
              "order": "DESC",
              "token_address": token_address}
    try:
        result = evm_api.token.get_token_owners(api_key=MORALIS_API_KEY,
                                                params=params)
        return result.get("result", [])
    except Exception as e:
        st.error(f"❌ Error fetching token holders: {e}")
        return []
    
######### WHOISAPI ######### 

def fetch_domain_info(domain_name):
    url = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
    params = {
        "apiKey": WHOIS_API_KEY,
        "domainName": domain_name,
        "outputFormat": "JSON"
    }
    return fetch_data(url, params=params)