import streamlit as st
import plotly.express as px
from utils import extract_chain_and_token, fetch_data, get_token_holders, format_timestamp, normalize_holder_entry

def main():
    st.set_page_config(page_title="DexScreener Token Profile", layout="wide")
    st.title("📊 DexScreener Token Profile Viewer")

    url_input = st.text_input("Enter DexScreener URL (e.g., https://dexscreener.com/solana/...)")

    if url_input:
        try:
            chain_id, pair_address = extract_chain_and_token(url_input)

            HEADERS = {
                "Accept": "*/*",
                "User-Agent": "Streamlit Viewer"
            }

            pair_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}"
            pair_data = fetch_data(pair_url, HEADERS)
            

            if not pair_data or 'pairs' not in pair_data or not pair_data['pairs']:
                st.warning("No pair data found.")
                return

            pair = pair_data['pairs'][0]
            token_address = pair_data['pairs'][0]['baseToken']['address']

            base = pair['baseToken']
            quote = pair['quoteToken']
            info = pair.get("info", {})

            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(info.get("imageUrl", ""), width=100)
                st.subheader(f"{base['name']} ({base['symbol']})")
                st.caption(f"DEX: {pair['dexId'].capitalize()} | Chain: {pair['chainId'].capitalize()}")

            with col2:
                st.markdown(f"**USD Price:** ${pair['priceUsd']}")
                st.markdown(f"**Native Price ({quote['symbol']}):** {pair['priceNative']}")
                st.markdown(f"**FDV:** ${pair['fdv']:,}")
                st.markdown(f"**Market Cap:** ${pair['marketCap']:,}")
                st.markdown(f"**Pair Created At:** {format_timestamp(pair['pairCreatedAt'])}")

            st.divider()

            st.subheader("📦 Token Metrics")
            col_left, col_right = st.columns(2)

            # Left Column: Liquidity
            with col_left:
                st.markdown("### 💧 Liquidity")
                st.metric("Total Liquidity (USD)", f"${pair['liquidity']['usd']:,}")
                st.metric(f"Base Liquidity ({base['symbol']})", f"{pair['liquidity']['base']:,}")
                st.metric(f"Quote Liquidity ({quote['symbol']})", f"{pair['liquidity']['quote']:,}")

            # Right Column: Volume & Transactions
            with col_right:
                st.markdown("### 📊 Volume & Transactions")

                for label in ['m5', 'h1', 'h6', 'h24']:
                    st.markdown(f"**⏱ Time Frame: `{label}`**")
                    volume = pair.get('volume', {}).get(label)
                    txns = pair.get('txns', {}).get(label, {})
                    price_change = pair.get('priceChange', {}).get(label)
                    if volume is not None or txns:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Volume", f"${volume:,.2f}" if volume is not None else "N/A")
                        col2.metric("Buys", f"{txns.get('buys', 'N/A')}")
                        col3.metric("Sells", f"{txns.get('sells', 'N/A')}")
                        if price_change is not None:
                            st.markdown(f"📈 **Price Change:** `{price_change}%`")
                        else:
                            st.markdown("📈 **Price Change:** `N/A`")
                    else:
                        st.markdown("⚠️ No data available for this time frame.")
                    st.markdown("---")
        
            st.subheader("🏦 Top Token Holders Distribution")
            holders = get_token_holders(token_address, chain_id)

            if holders:
                num_to_plot = 100
                top_holders = holders[:num_to_plot]

                # Normalize and filter entries
                normalized = [
                    normalize_holder_entry(h, chain_id)
                    for h in top_holders
                    if normalize_holder_entry(h, chain_id)["address"] and normalize_holder_entry(h, chain_id)["percent"] is not None
                ]

                addresses = [
                    entry["address"][:6] + "..." + entry["address"][-4:]
                    for entry in normalized
                ]
                percents = [entry["percent"] for entry in normalized]

                # Plot using Plotly
                import plotly.express as px

                fig = px.bar(
                    x=addresses,
                    y=percents,
                    orientation='v',
                    labels={"x": "Holder", "y": "Percent of Supply"},
                    title=f"Top {len(normalized)} Token Holders by % of Supply",
                    text=[f"{p:.2f}%" for p in percents]
                )

                fig.update_layout(
                    height=600,
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=10),
                        automargin=True
                    ),
                    margin=dict(t=50, b=100, l=50, r=20),
                    showlegend=False,
                    width=max(1000, 10 * len(addresses))
                )

                st.markdown("### 📈 Scroll to view all holders")
                st.plotly_chart(fig, use_container_width=False)

            # 🔹 Socials
            if info.get("socials"):
                st.subheader("🔗 Social Links")
                for social in info['socials']:
                    st.markdown(f"- [{social['type'].capitalize()}]({social['url']})")

            # 🔹 External Links
            st.markdown(f"🌐 [View on DexScreener]({pair['url']})")

        except ValueError as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
