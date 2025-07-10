import streamlit as st
from bs4 import BeautifulSoup
from utils.api import fetch_domain_info
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.twitter_scrapper import setup_driver, extract_profile_info, extract_community_info
from utils.parser import (
    _evaluate_domain, 
    is_community_link,
    evaluate_twitter_profile,
    evaluate_twitter_community
)

def render_website_intelligence_tab(domain):
    st.subheader("### 🔎 WHOIS Data")
    whois_data = fetch_domain_info(domain)
    if not whois_data:
        st.error("❌ Failed to retrieve WHOIS data.")
        return 0, ["WHOIS fetch failed"]

    record = whois_data.get("WhoisRecord", {})
    created = record.get("createdDateNormalized", "N/A")
    updated = record.get("updatedDateNormalized", "N/A")
    expires = record.get("expiresDateNormalized", "N/A")
    registrar = record.get("registrarName", "N/A")
    registrant_org = record.get("registrant", {}).get("organization", "N/A")

    st.subheader("📅 Domain Dates & Registrar")
    st.markdown(f"- **Created:** {created}")
    st.markdown(f"- **Updated:** {updated}")
    st.markdown(f"- **Expires:** {expires}")
    st.markdown(f"- **Registrar:** {registrar}")
    st.markdown(f"- **Registrant Org:** {registrant_org}")
    st.divider()

    assessments, domain_score, domain_deductions = _evaluate_domain(record, domain)
    st.subheader("🔍 Credibility Assessment")
    for name, (ok, msg) in assessments.items():
        icon = "✅" if ok else "⚠️"
        st.markdown(f"{icon} **{name}:** {msg}")
    st.divider()

    return domain_score, domain_deductions


def render_twitter_intelligence(link):
    driver = setup_driver()
    driver.get(link)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//article")))
    soup = BeautifulSoup(driver.page_source, "html.parser")

    if is_community_link(link):
        data = extract_community_info(driver)
        driver.quit()

        st.subheader(f"👥 Twitter Community: {data['name']}")
        st.markdown(f"**Description:** {data['description']}")
        st.markdown(f"**Members:** {data['members']}")
        st.markdown("---")

        st.markdown("### 📝 Recent Tweets Analysis")
        for i, tweet in enumerate(data.get("tweets", []), 1):
            st.markdown(f"**Tweet #{i}**")
            st.markdown(f"- 💬 Comments: {tweet['comments']}")
            st.markdown(f"- 🔁 Retweets: {tweet['retweets']}")
            st.markdown(f"- ❤️ Likes: {tweet['likes']}")
            st.markdown(f"- 👁️ Views: {tweet['views']}")
        st.markdown("---")

        twitter_score, twitter_deductions = evaluate_twitter_community(data)

    else:
        data = extract_profile_info(soup, driver)
        driver.quit()

        st.subheader(f"🐦 Twitter Profile: {data['username']}")
        st.markdown(f"**Bio:** {data['description']}")
        st.markdown(f"**Joined:** {data['joined']}")
        st.markdown(f"**Followers:** {data['followers']} | **Following:** {data['following']}")
        st.markdown("---")

        st.markdown("### 📝 Recent Tweets Analysis")
        for i, tweet in enumerate(data.get("tweets", []), 1):
            st.markdown(f"**Tweet #{i}**")
            st.markdown(f"- 💬 Comments: {tweet['comments']}")
            st.markdown(f"- 🔁 Retweets: {tweet['retweets']}")
            st.markdown(f"- ❤️ Likes: {tweet['likes']}")
            st.markdown(f"- 👁️ Views: {tweet['views']}")
        st.markdown("---")

        twitter_score, twitter_deductions = evaluate_twitter_profile(data)

    return twitter_score, twitter_deductions

def render_total_intelligence(domain_score=None, twitter_score=None, domain_deductions=None, twitter_deductions=None):
    st.header("🧠 Website & Twitter Intelligence Evaluation")

    # Normalize empty values
    domain_score = domain_score or 0
    twitter_score = twitter_score or 0
    domain_deductions = domain_deductions or []
    twitter_deductions = twitter_deductions or []

    # Show scores
    st.markdown(f"**🌐 Domain Score:** {domain_score} / 50")
    st.markdown(f"**🐦 Twitter Score:** {twitter_score} / 50")

    total = domain_score + twitter_score
    st.markdown(f"### 🧮 **Total Score: {total} / 100**")

    if domain_deductions or twitter_deductions:
        st.subheader("⚠️ Deduction Reasons")
        for reason in domain_deductions + twitter_deductions:
            st.markdown(f"- {reason}")