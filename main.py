import streamlit as st
import plotly.express as px
from datetime import datetime, timezone
from utils import extract_chain_and_token, fetch_data, get_token_holders, format_timestamp, normalize_holder_entry, safe_get

def main():
    tab1, tab2 = st.tabs(["📊 Token Profile", "🔍 Scam Analysis & Market Health"])
    with tab1:
        st.set_page_config(page_title="DexScreener Token Profile", layout="wide")
        st.title("📊 DexScreener Token Profile Viewer")

        url_input = st.text_input("Enter DexScreener URL (e.g., https://dexscreener.com/solana/...)")

        pair = None
        token_address = None
        token_pair_data = None
        holders = []

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

                token_pair_url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
                token_pair_data = fetch_data(token_pair_url, HEADERS)

                base = pair['baseToken']
                quote = pair['quoteToken']
                info = pair.get("info", {})

                col1, col2 = st.columns([1, 2])
                with col1:
                    image_url = safe_get(info, "imageUrl", default=None)
                    if image_url:
                        st.image(image_url, width=100)
                    else:
                        st.write("No image available.")
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

                    st.divider()
                    
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
                        st.plotly_chart(fig, use_container_width=False)

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
            
                
                # 🔹 Socials
                if info.get("socials"):
                    st.subheader("🔗 Social Links")
                    for social in info['socials']:
                        st.markdown(f"- [{social['type'].capitalize()}]({social['url']})")

                # 🔹 External Links
                st.markdown(f"🌐 [View on DexScreener]({pair['url']})")

            except ValueError as e:
                st.error(str(e))
    with tab2:
        st.header("🔍 Market Health & Scam Risk Analysis")
        st.markdown("This tab analyzes the token’s market data to detect potential **liquidity risks**, **volume anomalies**, **holder concerns**, and other **scam indicators**.")

        if pair:
            # === Extract Key Metrics ===
            price_change_1h = float(pair.get('priceChange', {}).get('h1', 0))
            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0))

            liquidity_usd = float(pair['liquidity']['usd'])
            market_cap = float(pair.get('marketCap', 0))
            volume_24h = float(pair['volume'].get('h24', 0))
            volume_1h = float(pair['volume'].get('h1', 0))

            score = 100
            deductions = []

            # === 💵 Price Change Analysis ===
            st.markdown("### 💵 Price Movement")
            col1, col2 = st.columns(2)
            col1.metric("Price Change (1h)", f"{price_change_1h:.2f}%", delta_color="inverse")
            col2.metric("Price Change (24h)", f"{price_change_24h:.2f}%", delta_color="inverse")

            is_price_spike = abs(price_change_1h) > 30 or abs(price_change_24h) > 50
            st.markdown(f"🔍 **Price Flag:** {'⚠️ Abnormal spike/dump' if is_price_spike else '✅ Stable price'}")

            if is_price_spike:
                score -= 10
                deductions.append("Extreme short-term price movement")

            st.divider()

            # === 💧 Liquidity vs Market Cap ===
            st.markdown("### 💧 Liquidity Health")
            liquidity_ratio = liquidity_usd / market_cap if market_cap else 0
            is_low_liquidity = liquidity_ratio < 0.05

            st.metric("Liquidity / Market Cap", f"{liquidity_ratio:.2%}")
            st.markdown(f"🔍 **Liquidity Flag:** {'⚠️ Low' if is_low_liquidity else '✅ Healthy'}")

            if is_low_liquidity:
                score -= 15
                deductions.append("Low liquidity depth (<5% of market cap)")

            st.divider()

            # === 📊 Volume Pattern Analysis ===
            st.markdown("### 📊 Volume Pattern Analysis")
            spike_ratio = (volume_1h / (volume_24h / 24)) if volume_24h else 0
            is_volume_spike = spike_ratio > 3

            st.metric("Volume Spike Ratio (1h vs avg)", f"{spike_ratio:.2f}")
            st.markdown(f"🔍 **Volume Flag:** {'⚠️ Suspicious spike' if is_volume_spike else '✅ Normal'}")

            if is_volume_spike:
                score -= 10
                deductions.append("Unusual 1h volume spike")

            st.divider()

            # === 🐳 Whale Concentration ===
            whale_percent = sum([
                normalize_holder_entry(h, chain_id).get("percent", 0)
                for h in holders[:5]
            ])
            is_high_whale_concentration = whale_percent > 50

            if is_high_whale_concentration:
                score -= 20
                deductions.append("High whale concentration (>50% in top 5 wallets)")

            # === 👥 Holder Count Risk ===
            if len(holders) < 50:
                score -= 10
                deductions.append("Too few holders (<50)")
            
            # === 🏷️ FDV vs Market Cap Analysis ===
            st.markdown("### 🏷️ FDV vs Market Cap")
            fdv = float(pair.get('fdv', 0))

            if fdv and market_cap:
                fdv_ratio = fdv / market_cap
                st.metric("FDV / Market Cap", f"{fdv_ratio:.2f}x")

                if fdv_ratio > 5:
                    st.markdown("⚠️ **Red Flag:** FDV is more than 5x Market Cap")
                    score -= 10
                    deductions.append("High FDV-to-MarketCap ratio (>5x)")

                elif fdv_ratio > 2:
                    st.markdown("⚠️ **Caution:** FDV is more than 2x Market Cap")
                    score -= 5
                    deductions.append("Moderate FDV-to-MarketCap ratio (>2x)")

                else:
                    st.markdown("✅ **Healthy FDV-to-MarketCap ratio**")
            else:
                st.info("ℹ️ FDV or Market Cap data unavailable")
            
            st.divider()
            
            # === 🏷️ Multi-DEX Token Pair ===
            st.markdown("## 📊 Multi-DEX Token Pair Comparison")

            price_map = []
            liquidity_map = []
            volume_map = []

            for dex_pair in token_pair_data:
                dex = dex_pair.get("dexId", "unknown").upper()
                label = ", ".join(dex_pair.get("labels", [])) or "N/A"
                pair_url = dex_pair.get("url", "#")
                price_usd = float(dex_pair.get("priceUsd", 0))
                liquidity_usd = float(dex_pair.get("liquidity", {}).get("usd", 0))
                volume_24h = float(dex_pair.get("volume", {}).get("h24", 0))

                price_map.append((dex, price_usd))
                liquidity_map.append((dex, liquidity_usd))
                volume_map.append((dex, volume_24h))

                st.markdown(f"### 🔗 DEX: {dex} [{label}]")
                st.markdown(f"[View Pair]({pair_url})")

                col1, col2, col3 = st.columns(3)
                col1.metric("Price (USD)", f"${price_usd:.4f}")
                col2.metric("Liquidity", f"${liquidity_usd:,.0f}")
                col3.metric("24h Volume", f"${volume_24h:,.0f}")

            st.divider()


            # === 🔁 Buy/Sell Ratios ===
            st.markdown("### 📊 Buy/Sell Ratio Across Timeframes")
            available_txns = pair.get('txns', {})

            for label in ['m5', 'h1', 'h6', 'h24']:
                if label not in available_txns:
                    st.markdown(f"#### ⏱ Timeframe: `{label}`")
                    st.info("⚠️ Data not available for this timeframe.")
                    continue

                tx = available_txns[label]
                buys = tx.get('buys', 0)
                sells = tx.get('sells', 0)
                total = buys + sells

                st.markdown(f"#### ⏱ Timeframe: `{label}`")
                if total == 0:
                    st.info("⚠️ No trading activity in this window.")
                    continue

                buy_ratio = (buys / total) * 100
                sell_ratio = (sells / total) * 100

                col1, col2, col3 = st.columns(3)
                col1.metric("Buys", buys)
                col2.metric("Sells", sells)
                col3.metric("Buy Ratio", f"{buy_ratio:.2f}%")

                if label == 'h24':  # Use h24 only for scoring
                    if sell_ratio > 70:
                        score -= 15
                        deductions.append("Sell pressure dominates (Sell ratio >70%)")
                        st.markdown("🚨 **Red Flag:** Sell pressure (>70%)")
                    elif buy_ratio > 80:
                        score -= 10
                        deductions.append("Suspicious buy dominance (Buy ratio >80%)")
                        st.markdown("⚠️ **Suspicious Pumping:** Buy ratio >80%")
                    elif 40 <= buy_ratio <= 60:
                        st.markdown("✅ **Healthy Trading** (40–60% balance)")
                    else:
                        score -= 5
                        deductions.append("Unbalanced buy/sell ratio")
                        st.markdown("⚠️ **Unusual Imbalance**")
                else:
                    if sell_ratio > 70:
                        st.markdown("🚨 **Red Flag:** Sell pressure (>70%)")
                    elif buy_ratio > 80:
                        st.markdown("⚠️ **Suspicious Pumping:** Buy ratio >80%")
                    elif 40 <= buy_ratio <= 60:
                        st.markdown("✅ **Healthy Trading** (40–60% balance)")
                    else:
                        st.markdown("⚠️ **Unusual Imbalance**")

            st.divider()

            # === ⏳ Pair Age ===
            pair_created_at = pair.get("pairCreatedAt")
            if pair_created_at:
                created_datetime = datetime.fromtimestamp(pair_created_at / 1000, tz=timezone.utc)
                now = datetime.now(tz=timezone.utc)
                days_since_launch = (now - created_datetime).days
                is_new_token = days_since_launch < 2

                st.markdown("### ⏳ Pair Age")
                st.metric("Days Since Launch", f"{days_since_launch} days")
                st.markdown(f"🔍 **Launch Flag:** {'⚠️ New token (<2 days)' if is_new_token else '✅ Launched long enough'}")

                if is_new_token:
                    score -= 10
                    deductions.append("Newly launched token (<2 days)")

            st.divider()

            # === 🧮 Final Market Health Score ===
            st.subheader(f"🧮 Market Health Score: {score}/100")
            if deductions:
                st.markdown("### ⚠️ Risk Factors Detected:")
                for reason in deductions:
                    st.markdown(f"- {reason}")
            else:
                st.success("✅ No major red flags detected.")





if __name__ == "__main__":
    main()
