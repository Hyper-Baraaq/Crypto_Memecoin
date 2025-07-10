import streamlit as st
from datetime import datetime, timezone
from utils.parser import normalize_holder_entry

def render_market_analysis_tab(pair, holders, token_pair_data, chain_id):
    # ― Extract Metrics ―
    p1h = float(pair.get("priceChange",{}).get("h1", 0))
    p24h = float(pair.get("priceChange",{}).get("h24", 0))
    liq   = float(pair["liquidity"]["usd"])
    mcap  = float(pair.get("marketCap", 0))
    v24   = float(pair["volume"].get("h24", 0))
    v1    = float(pair["volume"].get("h1", 0))

    score = 100
    ded   = []

    # ― Price Movement ―
    st.markdown("### 💵 Price Movement")
    c1,c2 = st.columns(2)
    c1.metric("Price Change (1h)",  f"{p1h:.2f}%", delta_color="inverse")
    c2.metric("Price Change (24h)", f"{p24h:.2f}%", delta_color="inverse")
    spike = abs(p1h)>30 or abs(p24h)>50
    st.markdown(f"🔍 **Price Flag:** {'⚠️ Abnormal spike/dump' if spike else '✅ Stable'}")
    if spike:
        score-=10; ded.append("Extreme short-term price movement")
    st.divider()

    # ― Liquidity Health ―
    ratio = liq/mcap if mcap else 0
    st.markdown("### 💧 Liquidity Health")
    st.metric("Liquidity / Market Cap", f"{ratio:.2%}")
    low_liq = ratio < 0.05
    st.markdown(f"🔍 **Liquidity Flag:** {'⚠️ Low' if low_liq else '✅ Healthy'}")
    if low_liq:
        score-=15; ded.append("Low liquidity depth (<5%)")
    st.divider()

    # ― Volume Spike ―
    spike_r = (v1/(v24/24)) if v24 else 0
    st.markdown("### 📊 Volume Pattern")
    st.metric("Volume Spike Ratio", f"{spike_r:.2f}")
    vol_spike = spike_r>3
    st.markdown(f"🔍 **Volume Flag:** {'⚠️ Suspicious' if vol_spike else '✅ Normal'}")
    if vol_spike:
        score-=10; ded.append("Unusual 1h volume spike")
    st.divider()

    # ― Whale & Holder Risk ―
    whale_pct = sum(normalize_holder_entry(h,chain_id).get("percent",0) for h in holders[:5])
    if whale_pct > 50:
        score-=20; ded.append("High whale concentration (>50%)")
    if len(holders)<50:
        score-=10; ded.append("Too few holders (<50)")

    # ― FDV vs Market Cap ―
    st.markdown("### 🏷️ FDV vs Market Cap")
    fdv = float(pair.get("fdv",0))
    if fdv and mcap:
        fdv_r = fdv/mcap
        st.metric("FDV / Market Cap", f"{fdv_r:.2f}x")
        if fdv_r>5:
            st.markdown("⚠️ FDV >5x MarketCap"); score-=10; ded.append("High FDV-to-MCap (>5x)")
        elif fdv_r>2:
            st.markdown("⚠️ FDV >2x MarketCap"); score-=5; ded.append("Moderate FDV-to-MCap (>2x)")
        else:
            st.markdown("✅ FDV healthy")
    else:
        st.info("ℹ️ FDV/MCap data unavailable")
    st.divider()

    # ― Multi-DEX Comparison ―
    st.markdown("## 📊 Multi-DEX Comparison")
    for dp in token_pair_data or []:
        dex   = dp.get("dexId","?").upper()
        lbl   = ", ".join(dp.get("labels",[])) or "N/A"
        p_usd = float(dp.get("priceUsd",0))
        liq_u = float(dp.get("liquidity",{}).get("usd",0))
        v24h2 = float(dp.get("volume",{}).get("h24",0))

        st.markdown(f"### 🔗 {dex} [{lbl}]")
        st.markdown(f"[View Pair]({dp.get('url','#')})")
        c1,c2,c3 = st.columns(3)
        c1.metric("Price (USD)", f"${p_usd:.4f}")
        c2.metric("Liquidity", f"${liq_u:,.0f}")
        c3.metric("24h Volume", f"${v24h2:,.0f}")
    st.divider()

    # ― Buy/Sell Ratios ―
    st.markdown("### 📊 Buy/Sell Ratios")
    txns = pair.get("txns",{})
    for tf in ("m5","h1","h6","h24"):
        st.markdown(f"#### ⏱ `{tf}`")
        tx = txns.get(tf)
        if not tx:
            st.info("⚠️ No data"); continue
        b,s = tx.get("buys",0), tx.get("sells",0)
        tot = b+s
        if tot==0:
            st.info("⚠️ No trades"); continue
        br = (b/tot)*100; sr=(s/tot)*100
        c1,c2,c3 = st.columns(3)
        c1.metric("Buys", b); c2.metric("Sells", s); c3.metric("Buy Ratio", f"{br:.2f}%")
        if tf=="h24":
            if sr>70:
                score-=15; ded.append("Sell pressure >70%"); st.markdown("🚨 Sell pressure")
            elif br>80:
                score-=10; ded.append("Buy pumping >80%"); st.markdown("⚠️ Pumping")
            elif 40<=br<=60:
                st.markdown("✅ Balanced")
            else:
                score-=5; ded.append("Unbalanced"); st.markdown("⚠️ Unusual")
        else:
            if sr>70:
                st.markdown("🚨 Sell pressure")
            elif br>80:
                st.markdown("⚠️ Pumping")
            elif 40<=br<=60:
                st.markdown("✅ Balanced")
            else:
                st.markdown("⚠️ Unusual")
    st.divider()

    # ― Pair Age ―
    ts = pair.get("pairCreatedAt")
    if ts:
        created = datetime.fromtimestamp(ts/1000, tz=timezone.utc)
        days    = (datetime.now(timezone.utc)-created).days
        new_tok = days<2
        st.markdown("### ⏳ Pair Age")
        st.metric("Days Since Launch", f"{days} days")
        st.markdown(f"🔍 {'⚠️ New (<2d)' if new_tok else '✅ Launched'}")
        if new_tok:
            score-=10; ded.append("Newly launched (<2d)")
    st.divider()

    # ― Final Score ―
    st.subheader(f"🧮 Market Health Score: {score}/100")
    if ded:
        st.markdown("### ⚠️ Risk Factors:")
        for d in ded:
            st.markdown(f"- {d}")
    else:
        st.success("✅ No red flags detected.")

    with st.expander("📊 Scoring Breakdown"):
        st.markdown("""
        - 💵 **Price Movement**: max 10 pts  
        - 💧 **Liquidity Health**: max 15 pts  
        - 📊 **Volume Spike**: max 10 pts  
        - 🐋 **Whale Risk**: max 20 pts  
        - 👥 **Holder Count**: max 10 pts  
        - 🏷️ **FDV/MCap**: max 10 pts  
        - 📈 **Buy/Sell Pressure**: max 15 pts  
        - ⏳ **Pair Age**: max 10 pts  
        """)
