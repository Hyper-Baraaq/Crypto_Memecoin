import streamlit as st
from utils.parser import extract_chain_and_token
from components.token_profile import render_token_profile_tab
from components.market_analysis import render_market_analysis_tab
from components.website_intelligence import render_website_intelligence_tab,  render_twitter_intelligence, render_total_intelligence


def main():
    st.set_page_config(page_title="DexScreener Token Profile", layout="wide")
    tab1, tab2, tab3 = st.tabs([
        "📊 Token Profile",
        "🔍 Scam Analysis & Market Health",
        "🌐 Website Intelligence"
    ])

    pair = None
    token_pairs = None
    holders = []
    chain_id = None
    domain = None
    twitter_link = None

    # ------------------ Tab 1 ------------------
    with tab1:
        st.title("📊 DexScreener Token Profile Viewer")
        url = st.text_input(
            "Enter DexScreener URL (e.g., https://dexscreener.com/solana/...)",
            key="tab1_url"
        )
        if url:
            try:
                chain_id, pair_addr = extract_chain_and_token(url)
                pair, token_pairs, holders, domain, twitter_link = render_token_profile_tab(
                    chain_id,
                    pair_addr
                )
            except ValueError as e:
                st.error(str(e))

    # ------------------ Tab 2 ------------------
    with tab2:
        st.header("🔍 Market Health & Scam Risk Analysis")
        st.markdown(
            "This tab analyzes the token’s market data to detect potential "
            "**liquidity risks**, **volume anomalies**, **holder concerns**, "
            "and other **scam indicators**."
        )
        if pair:
            render_market_analysis_tab(
                pair,
                holders,
                token_pairs,
                chain_id
            )

    # ------------------ Tab 3 ------------------
    with tab3:
        st.header("🌐 Website Intelligence")
        domain_score, domain_deductions = 0, []
        twitter_score, twitter_deductions = 0, []

        if domain:
            try:
                domain_score, domain_deductions = render_website_intelligence_tab(domain)
            except Exception as e:
                st.error(f"❌ Failed to analyze domain: {e}")
        else:
            st.info("No website exists.")

        if twitter_link:
            try:
                with st.spinner("Fetching Twitter profile..."):
                    twitter_score, twitter_deductions = render_twitter_intelligence(twitter_link)
            except Exception as e:
                st.error(f"❌ Failed to analyze Twitter: {e}")
        else:
            st.info("No Twitter profile link provided.")

        # Call the combined summary
        render_total_intelligence(
            domain_score=domain_score,
            twitter_score=twitter_score,
            domain_deductions=domain_deductions,
            twitter_deductions=twitter_deductions,
        )

if __name__ == "__main__":
    main()
