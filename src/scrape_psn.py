import os
from tenacity import retry, wait_fixed, stop_after_attempt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import json, time, urllib.request

from .db import record_played_game


load_dotenv()


SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444")
LOGIN_URL = os.getenv("LOGIN_URL", "https://my.playstation.com/profile")
SUCCESS_SELECTOR = os.getenv("SUCCESS_SELECTOR", "section[aria-label='Games']")

def _wait_for_grid_ready(url: str, timeout_s: int = 120):
    status_url = url.rstrip("/") + "/status"
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(status_url, timeout=3) as resp:
                data = json.load(resp)
                if data.get("value", {}).get("ready") is True:
                    return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"Selenium not ready after {timeout_s}s at {status_url}")

@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def make_driver():
    _wait_for_grid_ready(SELENIUM_REMOTE_URL, timeout_s=120)

    opts = webdriver.ChromeOptions()
    # Docker stability
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")   # also see docker shm_size below
    opts.add_argument("--disable-gpu")             # harmless in xvfb/noVNC setups

    # Allow 3rd-party cookies (SSO/iframed auth frequently needs this)
    opts.add_experimental_option("prefs", {
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False
    })
    opts.add_argument("--disable-features=BlockThirdPartyCookies,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure,PrivacySandboxSettings4")

    # Make it look like a regular desktop session
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    opts.add_argument("--accept-lang=en-US,en")

    # De-announce WebDriver (helps with bot/CDN checks)
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Remote(
        command_executor=SELENIUM_REMOTE_URL,
        options=opts,
    )
    driver.set_window_size(1366, 900)
    return driver

def wait_for_manual_login(driver, login_url: str, success_selector: str):
    """
    Navigate to the login URL and wait until the user has manually logged in.
    Blocks until `success_selector` is found in the DOM (up to 10 minutes).
    """
    print(f"Navigate to {login_url} and log in manually (using http://localhost:7900)...")
    driver.get(login_url)
    try:
        # wait until the button is present & clickable
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="web-toolbar#signin-button"]'))
            )
        button.click()

        print("Clicked the sign-in button!")
    except Exception as e:
        print("Could not find or click button:", e)

    wait = WebDriverWait(driver, 600) # 10 minutes
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, success_selector)))
    print("Login successful. Proceeding with scraping...")


def scrape_played_games(driver):
    # Ensure user has logged in manually first
    wait_for_manual_login(driver, LOGIN_URL, SUCCESS_SELECTOR)


    # TODO: Navigate to the actual games page and collect titles
    titles = [
        "ELDEN RING",
        "Ghost of Tsushima",
        "Gran Turismo 7",
    ]


    for t in titles:
        print(f"Recording: {t}")
        record_played_game(t)


if __name__ == "__main__":
    driver = make_driver()
    try:
        scrape_played_games(driver)
    finally:
        driver.quit()