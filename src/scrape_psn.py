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

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1366,900")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    # IMPORTANT: keep headless off while you’re using noVNC
    # options.add_argument("--headless=new")
    # caps = options.to_capabilities()
    # options["platformName"] = "Linux"

    # Use /wd/hub to avoid early-session race headaches
    hub = SELENIUM_REMOTE_URL.rstrip("/") + "/wd/hub"
    return webdriver.Remote(command_executor=hub, options=options)



def wait_for_manual_login(driver, login_url: str, success_selector: str):
    """
    Navigate to the login URL and wait until the user has manually logged in.
    Blocks until `success_selector` is found in the DOM (up to 10 minutes).
    """
    print(f"Navigate to {login_url} and log in manually (using http://localhost:7900)...")
    driver.get(login_url)


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