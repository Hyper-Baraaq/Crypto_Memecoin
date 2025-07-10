import streamlit as st
import plotly.express as px
from utils.api import fetch_pair_data, fetch_token_pairs, get_token_holders
from utils.parser import format_timestamp, normalize_holder_entry, safe_get

def render_token_profile_tab(chain_id: str, pair_address: str):
    domain = None
    pair = fetch_pair_data(chain_id, pair_address)
    if not pair:
        return None, None, None

    token_addr = pair["baseToken"]["address"]
    token_pairs = fetch_token_pairs(chain_id, token_addr)
    holders = get_token_holders(token_addr, chain_id)

    base, quote, info = pair["baseToken"], pair["quoteToken"], pair.get("info", {})

    # --- Header ---
    col1, col2 = st.columns([1, 2])
    with col1:
        img = safe_get(info, "imageUrl")
        if img:
            st.image(img, width=100)
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

    # --- Token Metrics & Holders ---
    st.subheader("📦 Token Metrics")
    left, right = st.columns(2)
    with left:
        st.markdown("### 💧 Liquidity")
        st.metric("Total Liquidity (USD)", f"${pair['liquidity']['usd']:,}")
        st.metric(f"Base Liquidity ({base['symbol']})", f"{pair['liquidity']['base']:,}")
        st.metric(f"Quote Liquidity ({quote['symbol']})", f"{pair['liquidity']['quote']:,}")
        st.divider()
        st.subheader("🏦 Top Token Holders Distribution")
        if holders:
            top100 = holders[:100]
            norm = [
                normalize_holder_entry(h, chain_id)
                for h in top100
                if normalize_holder_entry(h, chain_id)["address"]
                   and normalize_holder_entry(h, chain_id)["percent"] is not None
            ]
            addrs = [h["address"][:6] + "..." + h["address"][-4:] for h in norm]
            perc = [h["percent"] for h in norm]

            fig = px.bar(
                x=addrs, y=perc,
                labels={"x":"Holder","y":"% of Supply"},
                title=f"Top {len(perc)} Holders by % of Supply",
                text=[f"{p:.2f}%" for p in perc]
            )
            fig.update_layout(
                height=600,
                xaxis=dict(tickangle=45, tickfont=dict(size=10), automargin=True),
                margin=dict(t=50,b=100,l=50,r=20),
                showlegend=False,
                width=max(1000, 10*len(perc))
            )
            st.plotly_chart(fig, use_container_width=False)

    with right:
        st.markdown("### 📊 Volume & Transactions")
        for tf in ("m5","h1","h6","h24"):
            st.markdown(f"**⏱ Time Frame: `{tf}`**")
            vol = pair.get("volume",{}).get(tf)
            tx = pair.get("txns",{}).get(tf,{})
            pc = pair.get("priceChange",{}).get(tf)
            if vol or tx:
                c1,c2,c3 = st.columns(3)
                c1.metric("Volume", f"${vol:,.2f}" if vol else "N/A")
                c2.metric("Buys", f"{tx.get('buys','N/A')}")
                c3.metric("Sells", f"{tx.get('sells','N/A')}")
                st.markdown(f"📈 **Price Change:** `{pc}%`" if pc is not None else "📈 **Price Change:** `N/A`")
            else:
                st.markdown("⚠️ No data for this timeframe.")
            st.markdown("---")

    # --- Social & External Links ---
    twitter_link = None
    social_urls = set()
    if info.get("socials"):
        st.subheader("🔗 Social Links")
        for s in info["socials"]:
            if s['type'] == "twitter":
                twitter_link = s['url']
            st.markdown(f"- [{s['type'].capitalize()}]({s['url']})")
            social_urls.add(s["url"])

    if info.get("websites"):
        for w in info["websites"]:
            if w["url"] not in social_urls:
                domain = w['url']
                st.markdown(f"- [{w['label']}]({w['url']})")

    st.markdown(f"🌐 [View on DexScreener]({pair['url']})")
    return pair, token_pairs, holders, domain, twitter_link
