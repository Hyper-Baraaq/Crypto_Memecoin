import re
import ssl
import socket
import streamlit as st
from datetime import datetime, timezone

######### DEXScreener & MOLARIS ######### 

def extract_chain_and_token(link: str):
    pattern = r"https?://dexscreener\.com/([^/]+)/([^/]+)"
    m = re.match(pattern, link)
    if not m:
        raise ValueError("Invalid DexScreener URL format.")
    return m.group(1), m.group(2)

def format_timestamp(ms: int) -> str:
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

def safe_get(d: dict, key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

######### WHOISAPI ######### 

def _assess_domain_age(created_date: str) -> tuple[bool, str, int]:
    try:
        dt = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days < 90:
            return False, f"Domain is very new ({age_days} days)", 10
        return True, f"Domain age is {age_days} days", 0
    except Exception as e:
        return False, f"Could not parse creation date: {e}", 5

def _assess_registrar_reputation(name: str) -> tuple[bool, str, int]:
    low_rep = {"NameSilo", "Namecheap", "Epik", "Dynadot", "PublicDomainRegistry"}
    if any(bad.lower() in name.lower() for bad in low_rep):
        return False, f"Registrar '{name}' is low-cost or anonymous", 5
    return True, f"Registrar '{name}' appears reputable", 0

def _assess_whois_privacy(record: dict) -> tuple[bool, str, int]:
    rn = record.get('registrant', {}).get('name', '')
    org = record.get('registrant', {}).get('organization', '')
    if 'private' in rn.lower() or 'proxy' in org.lower():
        return False, "WHOIS privacy protection detected", 5
    return True, "WHOIS data is public", 0

def _assess_ssl_certificate(domain: str) -> tuple[bool, str, int]:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(3.0)
            s.connect((domain, 443))
            cert = s.getpeercert()
            issuer = dict(x[0] for x in cert.get('issuer', []))
            issuer_name = issuer.get('O', '')
            if "Let's Encrypt" in issuer_name:
                return False, "Free SSL (Let's Encrypt)", 5
            return True, f"SSL issued by {issuer_name}", 0
    except Exception as e:
        return False, f"SSL check failed: {e}", 5

def _assess_hosting_location(country: str) -> tuple[bool, str, int]:
    high_risk = {"RU", "CN", "IR", "KP", "VE", "BY"}
    if country in high_risk:
        return False, f"Hosting country {country} is high-risk", 5
    return True, f"Hosting country {country} is low-risk", 0

def _assess_update_gap(created_date: str, updated_date: str) -> tuple[bool, str, int]:
    try:
        dt_created = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
        dt_updated = datetime.fromisoformat(updated_date.replace("Z", "+00:00"))
        delta_days = (dt_updated - dt_created).days
        if delta_days <= 1:
            return False, "No meaningful update since domain registration", 10
        return True, f"Domain updated after {delta_days} days", 0
    except Exception as e:
        return False, f"Could not parse update data: {e}", 5

def _assess_expiry_duration(expires_date: str) -> tuple[bool, str, int]:
    try:
        dt_expires = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
        remaining_days = (dt_expires - datetime.now(timezone.utc)).days
        if remaining_days < 180:
            return False, f"Domain expires soon ({remaining_days} days left)", 10
        return True, f"Domain has {remaining_days} days until expiration", 0
    except Exception as e:
        return False, f"Could not parse expiry data: {e}", 5

def _evaluate_domain(record: dict, domain: str) -> tuple[dict, int, list[str]]:
    results = {}
    total_deduction = 0
    reasons = []

    created = record.get('createdDate', '')
    updated = record.get('updatedDate', '')
    expires = record.get('expiresDate', '')

    # Run checks and collect (ok, msg, deduction)
    checks = [
        ("Domain Age", _assess_domain_age(created)),
        ("Update Activity", _assess_update_gap(created, updated)),
        ("Expiration Length", _assess_expiry_duration(expires)),
        ("Registrar Reputation", _assess_registrar_reputation(record.get('registrarName', ''))),
        ("WHOIS Privacy", _assess_whois_privacy(record)),
        ("SSL Certificate", _assess_ssl_certificate(domain)),
    ]

    country = record.get('registrant', {}).get('countryCode')
    if country:
        checks.append(("Hosting Location", _assess_hosting_location(country)))

    for name, result in checks:
        if len(result) == 3:
            ok, msg, penalty = result
        else:
            ok, msg = result
            penalty = 0  # fallback in case not updated
        results[name] = (ok, msg)
        if not ok:
            total_deduction += penalty
            reasons.append(f"{name}: {msg}")

    final_score = max(50 - total_deduction, 0)
    return results, final_score, reasons


######### X Scraper #########

def is_community_link(link: str) -> bool:
    return bool(re.search(r'/i/communities/', link))

def parse_number(text):
    try:
        if "K" in text:
            return int(float(text.replace("K", "")) * 1000)
        elif "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        else:
            return int(text.replace(",", ""))
    except:
        return 0

def evaluate_twitter_community(data):
    score = 50
    deductions = []

    # 👥 Member count
    members = parse_number(data.get("members", "0"))
    if members < 500:
        score -= 10
        deductions.append("Low member count")
        st.warning("⚠️ Very small community.")
    else:
        st.success("✅ Good member base.")

    # 📄 Description
    if len(data.get("description", "")) < 10:
        score -= 5
        deductions.append("Sparse description")
        st.warning("⚠️ Empty or generic community bio.")
    else:
        st.success("✅ Informative description.")

    # 🐦 Tweets
    tweets = data.get("tweets", [])
    if len(tweets) < 3:
        score -= 15
        deductions.append("Few or no community tweets")
        st.warning("⚠️ Very few community tweets.")
    else:
        st.success(f"✅ {len(tweets)} tweets found.")

    # 📈 Engagement
    organic = 0
    seen = set()
    for t in tweets:
        key = tuple(t.values())  # dedup exact tweets
        if key in seen:
            continue
        seen.add(key)

        c = parse_number(t.get("comments", "0"))
        l = parse_number(t.get("likes", "0"))
        r = parse_number(t.get("retweets", "0"))

        if c > 3 and l > 5 and r > 2:
            organic += 1

    if organic < 2:
        score -= 10
        deductions.append("Low engagement")
        st.warning("⚠️ Engagement on tweets is low.")
    else:
        st.success("✅ Organic activity detected.")

    return score, deductions

def evaluate_twitter_profile(data):
    score = 50
    deductions = []

    # Followers
    try:
        followers = int(data["followers"].replace(",", "").replace("K", "000"))
        if followers < 1000:
            score -= 5
            st.warning("⚠️ Low follower count.")
            deductions.append("Low followers")
        else:
            st.success("✅ Healthy follower base.")
    except:
        score -= 5
        deductions.append("Unable to parse followers")
        st.info("ℹ️ Could not parse follower count.")

    # Bio
    if len(data["description"]) < 10:
        score -= 5
        deductions.append("Short/incomplete bio")
        st.warning("⚠️ Short or generic bio.")
    else:
        st.success("✅ Meaningful profile description.")

    # Join date
    joined_str = data.get("joined", "N/A")
    now = datetime.now()

    try:
        # Example format: "Joined July 2025"
        parts = joined_str.replace("Joined", "").strip().split()
        join_month = parts[0]
        join_year = int(parts[1])
        join_datetime = datetime.strptime(f"{join_month} {join_year}", "%B %Y")

        delta_days = (now - join_datetime).days

        if delta_days < 60:
            score -= 10
            deductions.append("Profile joined recently (within 2 months)")
            st.warning(f"⚠️ Joined very recently: {join_month} {join_year}")
        elif delta_days < 180:
            score -= 5
            deductions.append("Profile joined recently (within 6 months)")
            st.warning(f"⚠️ Joined in last 6 months: {join_month} {join_year}")
        else:
            st.success(f"✅ Established account (joined {join_month} {join_year})")

    except Exception as e:
        score -= 3
        deductions.append("Could not parse join date")
        st.info(f"ℹ️ Could not parse join date: {joined_str}")

    # Tweet activity
    tweets = data.get("tweets", [])
    if len(tweets) < 3:
        score -= 10
        deductions.append("Very few tweets")
        st.warning("⚠️ Low tweet activity.")
    else:
        st.success(f"✅ {len(tweets)} recent tweets found.")

    # Engagement quality
    organic = 0
    for t in tweets:
        c = int(t["comments"].replace(",", "").replace("K", "000") or "0")
        l = int(t["likes"].replace(",", "").replace("K", "000") or "0")
        r = int(t["retweets"].replace(",", "").replace("K", "000") or "0")
        if c > 3 and l > 5 and r > 2:
            organic += 1
    if organic < 2:
        score -= 10
        deductions.append("Low organic engagement on tweets")
        st.warning("⚠️ Tweets show low engagement.")
    else:
        st.success("✅ Tweet interactions appear organic.")

    return score, deductions
