import time
import random
import streamlit as st
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)


def extract_profile_info(soup, driver, scroll_count=3):
    # Username
    try:
        username_elem = soup.find("span", string=lambda t: t and t.startswith("@"))
        username = username_elem.get_text(strip=True)
    except:
        username = "N/A"

    # Description
    try:
        description = driver.find_element(By.XPATH, '//div[@data-testid="UserDescription"]').text
    except:
        description = "N/A"

    # Join date
    try:
        join_container = soup.find("div", {"data-testid": "UserProfileHeader_Items"})
        join_date_span = join_container.find("span", string=lambda s: s and "Joined" in s)
        join_date = join_date_span.get_text(strip=True)
    except:
        join_date = "N/A"

    # Following and followers
    try:
        following = driver.find_element(By.XPATH, '//a[contains(@href, "/following")]//span[1]').text
    except:
        following = "N/A"

    try:
        followers = driver.find_element(By.XPATH, '//a[contains(@href, "/followers") or contains(@href, "/verified_followers")]//span[1]').text
    except:
        followers = "N/A"

    # Tweets
    tweets_data = []
    last_position = 0
    no_change_count = 0

    for _ in range(scroll_count):
        try:
            current_position = driver.execute_script("return window.pageYOffset;")

            scroll_increment = random.randint(300, 500)
            if current_position == last_position:
                scroll_increment += 100
                no_change_count += 1
            else:
                no_change_count = 0

            new_position = current_position + scroll_increment
            driver.execute_script(f"window.scrollTo({{top: {new_position}, behavior: 'smooth'}});")
            last_position = current_position

            time.sleep(random.uniform(1.5, 3.5))

            # Retry if stuck
            try:
                retry_btn = driver.find_element(By.XPATH, "//button[.//span[text()='Retry']]")
                if retry_btn.is_displayed():
                    retry_btn.click()
                    time.sleep(random.choice([1, 2]))
            except:
                pass

            if no_change_count >= 5:
                break

            # 🧠 Scrape tweet data on *each* scroll (allow duplicates)
            try:
                tweets = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']"))
                )
                print(f"[Scroll] Fetched {len(tweets)} tweet containers")
                for tweet in tweets:
                    try:
                        html = tweet.get_attribute("outerHTML")
                        tweet_soup = BeautifulSoup(html, "html.parser")

                        likes = tweet.find_element(By.CSS_SELECTOR, "[data-testid='like']").text.strip() or "0"
                        retweets = tweet.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text.strip() or "0"
                        comments = tweet.find_element(By.CSS_SELECTOR, "[data-testid='reply']").text.strip() or "0"

                        views_elem = tweet_soup.find("a", {"aria-label": lambda text: text and "views" in text})
                        views = views_elem["aria-label"].split(" views")[0] if views_elem else "0"

                        tweets_data.append({
                            "comments": comments,
                            "likes": likes,
                            "retweets": retweets,
                            "views": views
                        })
                    except:
                        continue
            except:
                continue

        except Exception as e:
            print(f"Scroll error: {e}")
            break

    driver.quit()

    return {
        "username": username,
        "description": description,
        "joined": join_date,
        "following": following,
        "followers": followers,
        "tweets": tweets_data
    }


def extract_community_info(driver, scroll_count=3):
    # Community Name
    try:
        community_elem = driver.find_element(
            By.XPATH,
            "//h2[@dir='ltr' and @role='heading' and contains(@class, 'r-qvutc0')]"
        )
        community_name = community_elem.text.strip()
    except:
        community_name = "N/A"

    # Description
    try:
        description_elem = driver.find_element(By.XPATH, "//div[@dir='ltr' and contains(@style, '-webkit-line-clamp')]")
        description = description_elem.text.strip()
    except:
        description = "N/A"

    # Member Count
    try:
        member_button = driver.find_element(By.XPATH, "//button[@data-testid='community-facepile']")
        member_number = member_button.find_element(By.XPATH, ".//span[.//text()[normalize-space()='Members']]/preceding-sibling::span[1]").text.strip()
    except:
        member_number = "N/A"

    # Tweets
    tweets_data = []
    last_position = 0
    no_change_count = 0

    for _ in range(scroll_count):
        try:
            current_position = driver.execute_script("return window.pageYOffset;")

            scroll_increment = random.randint(300, 500)
            if current_position == last_position:
                scroll_increment += 100
                no_change_count += 1
            else:
                no_change_count = 0

            new_position = current_position + scroll_increment
            driver.execute_script(f"window.scrollTo({{top: {new_position}, behavior: 'smooth'}});")
            last_position = current_position

            time.sleep(random.uniform(1.5, 3.5))

            # Retry if stuck
            try:
                retry_btn = driver.find_element(By.XPATH, "//button[.//span[text()='Retry']]")
                if retry_btn.is_displayed():
                    retry_btn.click()
                    time.sleep(random.choice([1, 2]))
            except:
                pass

            if no_change_count >= 5:
                break

            # 🧠 Scrape tweet data on *each* scroll (allow duplicates)
            try:
                tweets = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']"))
                )
                print(f"[Scroll] Fetched {len(tweets)} tweet containers")
                for tweet in tweets:
                    try:
                        html = tweet.get_attribute("outerHTML")
                        tweet_soup = BeautifulSoup(html, "html.parser")

                        likes = tweet.find_element(By.CSS_SELECTOR, "[data-testid='like']").text.strip() or "0"
                        retweets = tweet.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text.strip() or "0"
                        comments = tweet.find_element(By.CSS_SELECTOR, "[data-testid='reply']").text.strip() or "0"

                        views_elem = tweet_soup.find("a", {"aria-label": lambda text: text and "views" in text})
                        views = views_elem["aria-label"].split(" views")[0] if views_elem else "0"

                        tweets_data.append({
                            "comments": comments,
                            "likes": likes,
                            "retweets": retweets,
                            "views": views
                        })
                    except:
                        continue
            except:
                continue

        except Exception as e:
            print(f"Scroll error: {e}")
            break

    driver.quit()

    return {
        "name": community_name,
        "description": description,
        "members": member_number,
        "tweets": tweets_data
    }
